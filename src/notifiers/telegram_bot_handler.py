"""
Telegram Bot Command Handler
Handles incoming commands from users and triggers GitHub workflows

This allows users to:
- Send /fix commands to create GitHub issues
- Check status of fixes
- Get help information
"""

import os
import time
import logging
import requests
import json
import asyncio
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Try to import Claude fixer, but don't fail if not available
try:
    from .claude_auto_fixer import ClaudeAutoFixer
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    logger.warning("Claude Auto-Fixer not available")
    ClaudeAutoFixer = None

# Import Smart Intent Parser
try:
    from src.utils.intent_parser import IntentParser, ParsedIntent, parse_intent
    SMART_INTENT_AVAILABLE = True
except ImportError:
    SMART_INTENT_AVAILABLE = False
    logger.warning("Smart Intent Parser not available")
    IntentParser = None
    ParsedIntent = None
    parse_intent = None

# Back-off delay (seconds) after polling errors to avoid tight loops
_ERROR_BACKOFF_SECONDS = 5

# Rate limiting for on-demand news (minutes between requests per user)
_NEWS_RATE_LIMIT_MINUTES = 5

# News keywords that trigger on-demand news
NEWS_TRIGGER_KEYWORDS = ['news', 'latest news', 'get news', 'show news', 'fetch news']


class TelegramBotHandler:
    """
    Handles Telegram bot commands and triggers GitHub Actions

    Commands:
    - /fix <description> - Create GitHub issue and trigger auto-fix
    - /status - Check recent fixes status
    - /help - Show available commands
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        github_token: Optional[str] = None,
        github_repo: Optional[str] = None
    ):
        """
        Initialize Telegram Bot Handler

        Args:
            bot_token: Telegram Bot API token
            github_token: GitHub Personal Access Token
            github_repo: GitHub repository (format: owner/repo)
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.github_token = github_token or os.getenv('GH_TOKEN')
        self.github_repo = github_repo or os.getenv('GITHUB_REPO', 'aijasminekaur11/khabri')

        if not self.bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not configured — bot will not function")

        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.github_api = "https://api.github.com"

        # Authorized chat IDs (from environment) - for command access control
        authorized_ids_str = os.getenv('TELEGRAM_AUTHORIZED_IDS', os.getenv('TELEGRAM_CHAT_ID', ''))
        self.authorized_chat_ids = set(cid.strip() for cid in authorized_ids_str.split(',') if cid.strip())

        if self.authorized_chat_ids:
            logger.info(f"Bot authorization enabled for {len(self.authorized_chat_ids)} chat(s)")
        else:
            logger.warning("No authorized chat IDs configured - bot will accept commands from anyone")

        # Initialize Claude Auto-Fixer if available
        if CLAUDE_AVAILABLE and ClaudeAutoFixer:
            self.claude_fixer = ClaudeAutoFixer()
        else:
            self.claude_fixer = None
            logger.info("Claude Auto-Fixer disabled")

        # Track last update ID to avoid duplicate processing
        self.last_update_id = 0
        
        # Rate limiting storage for on-demand news {chat_id: last_request_time}
        self._news_last_request: Dict[str, datetime] = {}
        
        # Cache for on-demand news results
        self._news_cache: Optional[Dict[str, Any]] = None
        self._news_cache_time: Optional[datetime] = None
        self._news_cache_ttl_minutes = 2  # Cache news for 2 minutes

    def get_updates(self, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get new updates from Telegram

        Args:
            offset: Update ID to start from

        Returns:
            List of update objects
        """
        params: Dict[str, Any] = {
            'timeout': 30,
        }
        if offset is not None:
            params['offset'] = offset

        try:
            response = requests.get(
                f"{self.api_url}/getUpdates",
                params=params,
                timeout=35
            )

            if response.status_code == 200:
                try:
                    data = response.json()
                except (json.JSONDecodeError, ValueError):
                    logger.error("Invalid JSON response from Telegram getUpdates")
                    return []
                return data.get('result', [])
            else:
                logger.error(f"Failed to get updates: {response.status_code}")
                return []

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting updates: {e}")
            return []

    def send_message(self, chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a message to Telegram chat

        Args:
            chat_id: Chat ID to send to
            text: Message text
            parse_mode: Parsing mode (Markdown or HTML)

        Returns:
            True if sent successfully
        """
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }

        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending message: {e}")
            return False

    def _add_label_to_issue(self, issue_number: int, label: str) -> bool:
        """
        Add a label to a GitHub issue

        Args:
            issue_number: Issue number
            label: Label to add

        Returns:
            True if successful
        """
        if not self.github_token:
            return False

        url = f"{self.github_api}/repos/{self.github_repo}/issues/{issue_number}/labels"

        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        payload = {'labels': [label]}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code in (200, 201):
                logger.info(f"Added label '{label}' to issue #{issue_number}")
                return True
            else:
                logger.warning(f"Failed to add label: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error adding label: {e}")
            return False

    def _add_issue_comment(self, issue_number: int, comment_body: str) -> bool:
        """
        Add a comment to a GitHub issue

        Args:
            issue_number: Issue number
            comment_body: Comment text

        Returns:
            True if successful
        """
        if not self.github_token:
            return False

        url = f"{self.github_api}/repos/{self.github_repo}/issues/{issue_number}/comments"

        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        payload = {'body': comment_body}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            return response.status_code == 201
        except requests.exceptions.RequestException as e:
            logger.error(f"Error adding comment: {e}")
            return False

    def create_github_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a GitHub issue

        Args:
            title: Issue title
            body: Issue description
            labels: List of labels to add

        Returns:
            Issue data if created successfully
        """
        if not self.github_token:
            logger.error("GitHub token not configured")
            return None

        url = f"{self.github_api}/repos/{self.github_repo}/issues"

        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        payload = {
            'title': title,
            'body': body
        }

        # Only add labels if explicitly provided (don't add default labels)
        if labels:
            payload['labels'] = labels

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)

            if response.status_code == 201:
                issue_data = response.json()
                logger.info(f"Created GitHub issue #{issue_data['number']}")
                return issue_data
            else:
                logger.error(f"Failed to create issue: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating GitHub issue: {e}")
            return None

    def get_recent_issues(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent GitHub issues with auto-fix label

        Args:
            limit: Number of issues to retrieve

        Returns:
            List of issue data
        """
        if not self.github_token:
            return []

        url = f"{self.github_api}/repos/{self.github_repo}/issues"

        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        params = {
            'labels': 'auto-fix',
            'state': 'all',
            'per_page': limit,
            'sort': 'created',
            'direction': 'desc'
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get issues: {response.status_code}")
                return []

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting issues: {e}")
            return []

    def handle_fix_command(self, chat_id: str, message_text: str) -> bool:
        """
        Handle /fix command

        Args:
            chat_id: Chat ID that sent the command
            message_text: Full message text

        Returns:
            True if handled successfully
        """
        # Extract description after /fix
        parts = message_text.split(None, 1)

        if len(parts) < 2:
            self.send_message(
                chat_id,
                "❌ Please provide a description.\n\n"
                "Usage: `/fix <description>`\n"
                "Example: `/fix Budget alerts not showing real estate news`"
            )
            return False

        description = parts[1]

        # Create GitHub issue
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        issue_title = f"[Auto-Fix] {description[:80]}"
        issue_body = f"""## 🤖 Automated Fix Request
**Requested via**: Telegram Bot
**Timestamp**: {timestamp}
**Requested by**: User

### Description
{description}

### Instructions for Claude Code
Please analyze and fix the issue described above. Follow these steps:
1. Read relevant code files
2. Identify the root cause
3. Implement the fix
4. Run tests to verify
5. Create a pull request

---
*This issue was created automatically via Telegram bot command.*
"""

        self.send_message(
            chat_id,
            "🔄 Creating fix request...\n"
            "Please wait while I create a GitHub issue."
        )

        issue = self.create_github_issue(
            title=issue_title,
            body=issue_body
            # Labels removed - add them manually in GitHub if needed
        )

        if issue:
            issue_url = issue['html_url']
            issue_number = issue['number']

            # Add 'auto-fix' label AFTER issue creation to trigger GitHub Actions
            self._add_label_to_issue(issue_number, 'auto-fix')

            # Send initial success message
            msg_lines = [
                f"✅ **Issue #{issue_number} created!**",
                "",
                f"🔗 {issue_url}",
            ]
            if self.claude_fixer:
                msg_lines.extend(["", "🤖 Claude is analyzing..."])
            self.send_message(chat_id, "\n".join(msg_lines))

            # Use Claude to analyze the issue if available
            if self.claude_fixer:
                logger.info(f"Analyzing issue #{issue_number} with Claude...")
                analysis_result = self.claude_fixer.analyze_issue(issue_title, issue_body)
            else:
                analysis_result = {'success': False, 'message': 'Claude API not configured'}

            if analysis_result.get('success'):
                analysis = analysis_result['analysis']
                tokens_used = analysis_result.get('tokens_used', 0)

                # Add analysis as a comment on the issue
                self._add_issue_comment(issue_number, f"""## 🤖 Claude Analysis

{analysis}

---
*Analysis powered by Claude Sonnet 4 ({tokens_used} tokens)*
""")

                # Send analysis to user
                analysis_preview = analysis[:500] + "..." if len(analysis) > 500 else analysis

                response = f"""🤖 **Claude Analysis Complete!**

📋 **Issue**: #{issue_number}

**Analysis Preview:**
{analysis_preview}

Full analysis posted as comment on GitHub issue.
You'll be notified when implementation is ready for review.
"""
            else:
                # Claude analysis failed
                error_msg = analysis_result.get('message', 'Analysis failed')
                response = f"""✅ **Issue created**: #{issue_number}

⚠️ Auto-analysis unavailable: {error_msg}

Please review manually: {issue_url}
"""

            self.send_message(chat_id, response)
            return True
        else:
            self.send_message(
                chat_id,
                "❌ Failed to create fix request.\n"
                "Please try again or contact support."
            )
            return False

    def handle_status_command(self, chat_id: str) -> bool:
        """
        Handle /status command

        Args:
            chat_id: Chat ID that sent the command

        Returns:
            True if handled successfully
        """
        self.send_message(chat_id, "🔍 Checking recent fixes...")

        issues = self.get_recent_issues(limit=5)

        if not issues:
            self.send_message(
                chat_id,
                "📋 No recent fix requests found.\n\n"
                "Use `/fix <description>` to create a new fix request."
            )
            return True

        response = "📊 **Recent Fix Requests**\n\n"

        for issue in issues:
            number = issue['number']
            title = issue['title'].replace('[Auto-Fix] ', '')
            state = issue['state']

            # Determine status emoji
            if state == 'closed':
                status_emoji = "✅"
                status_text = "Completed"
            elif 'pull_request' in issue:
                status_emoji = "🔄"
                status_text = "PR Ready"
            else:
                status_emoji = "⏳"
                status_text = "In Progress"

            response += f"{status_emoji} **#{number}** - {title[:50]}\n"
            response += f"   Status: {status_text}\n\n"

        response += "\nTap issue number to view details on GitHub."

        self.send_message(chat_id, response)
        return True

    def handle_help_command(self, chat_id: str) -> bool:
        """
        Handle /help command

        Args:
            chat_id: Chat ID that sent the command

        Returns:
            True if handled successfully
        """
        help_text = """🤖 **Telegram Bot Commands**

**Quick Actions:**

📰 Type `news` or `/news` - Get infrastructure & metro news
   • 🚇 Metro Projects | 🛣️ Highways | ✈️ Airports | 🏛️ Govt Updates
   • 📱 Sends to ALL your Telegram chats
   • 📧 Also sends to your Email
   • Rate limit: 1 request per 5 minutes

**Available Commands:**

📝 `/fix <description>` - Create automated fix request
   Example: `/fix Budget alerts showing wrong news`

🧠 **Smart Commands** (Just type naturally):
   • `add automotive companies like Mahindra, Tata`
   • `add bollywood actors like Shah Rukh Khan`
   • `change morning time to 8 AM`
   • `show all cricketers`
   • `remove John Deere from automotive`

📊 `/status` - Check status of recent fixes

↩️ `/undo` - Undo your last change

❓ `/help` - Show this help message

---

**How it works:**
1. **News:** Just type `news` anytime for instant updates
   
2. **Smart Mode:** Type what you want naturally
   → Bot will understand and ask for confirmation
   
3. **Detailed Mode:** Use `/fix` for complex changes
   → Bot creates GitHub issue
   → Claude Code analyzes and fixes
   → You review and approve

**Example Usage:**
```
Instant news:
→ news

Smart commands (no / needed):
→ add car companies like Mahindra, Tata Motors
→ include real estate developers like Lodha
→ change evening digest to 5 PM

Detailed commands (/fix):
/fix Budget alerts not filtering correctly
/fix Add robots.txt compliance to scrapers
```

Need help? Contact support or check the GitHub repository.
"""

        self.send_message(chat_id, help_text)
        return True

    def handle_undo_command(self, chat_id: str) -> bool:
        """
        Handle /undo command - restore from last backup

        Args:
            chat_id: Chat ID that sent the command

        Returns:
            True if handled successfully
        """
        try:
            # Import ConfigExecutor
            try:
                from utils.config_executor import ConfigExecutor
            except ImportError:
                from src.utils.config_executor import ConfigExecutor

            executor = ConfigExecutor()

            # Read audit log to find user's last change
            if not executor.audit_log_file.exists():
                self.send_message(
                    chat_id,
                    "⚠️ No changes found to undo.\n\n"
                    "The undo feature tracks your configuration changes.\n"
                    "Make some changes first, then you can undo them."
                )
                return True

            audit_data = executor._read_yaml(executor.audit_log_file)

            if 'changes' not in audit_data or not audit_data['changes']:
                self.send_message(
                    chat_id,
                    "⚠️ No changes found to undo."
                )
                return True

            # Find last successful change by this user
            last_change = None
            for change in audit_data['changes']:
                if change.get('user_id') == chat_id and change.get('success') and change.get('backup_file'):
                    last_change = change
                    break

            if not last_change:
                self.send_message(
                    chat_id,
                    "⚠️ No recent changes found for your account.\n\n"
                    "Only your own changes can be undone."
                )
                return True

            # Perform rollback
            backup_file = last_change['backup_file']
            result = executor.rollback(backup_file)

            # Send result
            self.send_message(chat_id, result.message, parse_mode='Markdown')

            return result.success

        except Exception as e:
            logger.error(f"Error handling undo command: {e}", exc_info=True)
            self.send_message(
                chat_id,
                f"❌ Error undoing last change: {str(e)}\n\n"
                "Please try again or contact support."
            )
            return False

    def handle_smart_intent(self, chat_id: str, intent: ParsedIntent) -> bool:
        """
        Handle parsed smart intent with confirmation UI (or direct execution for read-only)

        Args:
            chat_id: Chat ID to respond to
            intent: Parsed intent from user's message

        Returns:
            True if handled successfully
        """
        # Read-only intents execute immediately without confirmation
        read_only_intents = ['LIST_ITEMS', 'SHOW_CONFIG', 'SHOW_SCHEDULE', 'SHOW_STATS', 'CHECK_STATUS', 'HELP']

        if intent.intent_type in read_only_intents:
            # Execute directly without confirmation
            try:
                from utils.config_executor import ConfigExecutor
            except ImportError:
                from src.utils.config_executor import ConfigExecutor

            executor = ConfigExecutor()
            result = executor.execute(intent, user_id=chat_id)
            self.send_message(chat_id, result.message, parse_mode='Markdown')
            return result.success
        logger.info(f"Handling smart intent: {intent.intent_type} with confidence {intent.confidence}")
        
        # Build confirmation message
        emoji_map = {
            'ADD_COMPANIES': '🏢',
            'REMOVE_ITEM': '🗑️',
            'CHANGE_TIME': '⏰',
            'LIST_ITEMS': '📋',
            'ADD_SOURCE': '📰',
            'HELP': '❓',
        }
        
        emoji = emoji_map.get(intent.intent_type, '🤖')
        
        # Format entities for display
        if intent.entities:
            entity_list = '\n'.join([f"  • {e}" for e in intent.entities[:10]])
            if len(intent.entities) > 10:
                entity_list += f"\n  ... and {len(intent.entities) - 10} more"
        else:
            entity_list = "  (No specific items detected)"
        
        # Build message
        message = f"""{emoji} **I understood your request:**

**Action:** {intent.suggested_changes}

**Category:** {intent.category.replace('_', ' ').title() if intent.category else 'General'}
**Target File:** `{intent.target_file}`

**Detected Items:**
{entity_list}

**Confidence:** {intent.confidence:.0%}

Would you like me to proceed with this change?"""

        # Create inline keyboard for confirmation
        keyboard = {
            'inline_keyboard': [
                [
                    {'text': '👍 Yes, proceed', 'callback_data': f'confirm:{intent.intent_type}:{hash(intent.original_text) & 0xFFFFFFFF}'},
                    {'text': '✏️ Edit', 'callback_data': f'edit:{intent.intent_type}:{hash(intent.original_text) & 0xFFFFFFFF}'},
                ],
                [
                    {'text': '❌ Cancel', 'callback_data': 'cancel'},
                    {'text': '🔄 Use /fix instead', 'callback_data': f'fallback:{intent.original_text[:50]}'},
                ]
            ]
        }
        
        # Store intent in memory for callback handling (simple approach)
        # In production, use Redis or database
        if not hasattr(self, '_pending_intents'):
            self._pending_intents = {}
        
        intent_key = f"{chat_id}:{hash(intent.original_text) & 0xFFFFFFFF}"
        self._pending_intents[intent_key] = intent
        
        # Send message with inline keyboard
        self._send_message_with_keyboard(chat_id, message, keyboard)
        return True

    def _send_message_with_keyboard(self, chat_id: str, text: str, keyboard: Dict) -> bool:
        """Send message with inline keyboard"""
        if not self.bot_token:
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown',
            'reply_markup': json.dumps(keyboard)
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.error(f"Error sending message with keyboard: {e}")
            return False

    def handle_callback_query(self, callback_query: Dict[str, Any]) -> bool:
        """
        Handle inline button callbacks
        
        Args:
            callback_query: Callback query from Telegram
            
        Returns:
            True if handled successfully
        """
        callback_id = callback_query.get('id', '')
        chat_id = str(callback_query.get('message', {}).get('chat', {}).get('id', ''))
        data = callback_query.get('data', '')
        
        # Acknowledge callback
        self._answer_callback(callback_id)
        
        if data == 'cancel':
            self.send_message(chat_id, "❌ Cancelled. No changes made.")
            return True
        
        if data.startswith('confirm:'):
            parts = data.split(':', 2)
            if len(parts) >= 2:
                intent_type = parts[1]
                intent_hash = parts[2] if len(parts) > 2 else ''
                return self._execute_confirmed_intent(chat_id, intent_type, intent_hash)
        
        if data.startswith('fallback:'):
            original_text = data.split(':', 1)[1] if ':' in data else ''
            return self.handle_fix_command(chat_id, f"/fix {original_text}")
        
        if data.startswith('edit:'):
            self.send_message(
                chat_id,
                "✏️ Please send the corrected command:\n"
                "Example: `add automotive companies like Mahindra, Tata Motors`",
                parse_mode='Markdown'
            )
            return True
        
        return False

    def _execute_confirmed_intent(self, chat_id: str, intent_type: str, intent_hash: str) -> bool:
        """Execute a confirmed intent using ConfigExecutor"""
        intent_key = f"{chat_id}:{intent_hash}"

        if not hasattr(self, '_pending_intents') or intent_key not in self._pending_intents:
            self.send_message(chat_id, "❌ Error: Intent expired. Please try again.")
            return False

        intent = self._pending_intents[intent_key]

        # Import ConfigExecutor
        try:
            from utils.config_executor import ConfigExecutor
        except ImportError:
            try:
                from src.utils.config_executor import ConfigExecutor
            except ImportError:
                self.send_message(chat_id, "❌ ConfigExecutor not available. Please check installation.")
                return False

        # Execute the intent
        self.send_message(chat_id, "🔄 Executing your request...")

        try:
            executor = ConfigExecutor()
            result = executor.execute(intent, user_id=chat_id)

            # Send result message
            self.send_message(chat_id, result.message, parse_mode='Markdown')

            # Clean up pending intent
            if intent_key in self._pending_intents:
                del self._pending_intents[intent_key]

            return result.success

        except Exception as e:
            logger.error(f"Error executing intent: {e}", exc_info=True)
            self.send_message(
                chat_id,
                f"❌ Error executing request: {str(e)}\n\n"
                "Please try again or contact support."
            )
            return False

    def _answer_callback(self, callback_id: str) -> bool:
        """Answer callback query to remove loading state"""
        if not self.bot_token:
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/answerCallbackQuery"
        
        try:
            response = requests.post(url, json={'callback_query_id': callback_id}, timeout=10)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.error(f"Error answering callback: {e}")
            return False

    def _is_news_trigger(self, text: str) -> bool:
        """
        Check if the message text is a news trigger
        
        Args:
            text: Message text from user
            
        Returns:
            True if this is a news request
        """
        if not text:
            return False
        
        text_lower = text.lower().strip()
        
        # Check for exact matches or simple news requests
        if text_lower in NEWS_TRIGGER_KEYWORDS:
            return True
        
        # Check for patterns like "send news", "get me news", etc.
        news_patterns = [
            r'^news$',
            r'^latest\s+news$',
            r'^send\s+(?:me\s+)?news',
            r'^get\s+(?:me\s+)?(?:the\s+)?news',
            r'^show\s+(?:me\s+)?news',
            r'^fetch\s+news',
        ]
        
        import re
        for pattern in news_patterns:
            if re.match(pattern, text_lower):
                return True
        
        return False
    
    def _check_rate_limit(self, chat_id: str) -> tuple[bool, int]:
        """
        Check if user is rate limited for news requests
        
        Args:
            chat_id: User's chat ID
            
        Returns:
            Tuple of (is_allowed, seconds_remaining)
        """
        now = datetime.now()
        last_request = self._news_last_request.get(chat_id)
        
        if last_request is None:
            return True, 0
        
        elapsed = (now - last_request).total_seconds()
        limit_seconds = _NEWS_RATE_LIMIT_MINUTES * 60
        
        if elapsed < limit_seconds:
            remaining = int(limit_seconds - elapsed)
            return False, remaining
        
        return True, 0
    
    def _get_cached_news(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached news if still valid
        
        Returns:
            List of news articles or None if cache expired
        """
        if self._news_cache is None or self._news_cache_time is None:
            return None
        
        elapsed = (datetime.now() - self._news_cache_time).total_seconds()
        if elapsed > (self._news_cache_ttl_minutes * 60):
            return None
        
        return self._news_cache
    
    def _set_news_cache(self, articles: List[Dict[str, Any]]):
        """Cache news articles"""
        self._news_cache = articles
        self._news_cache_time = datetime.now()
    
    async def _fetch_news_on_demand(self) -> List[Dict[str, Any]]:
        """
        Fetch news on demand using the RSS scraper
        
        Returns:
            List of processed news articles
        """
        # Check cache first
        cached = self._get_cached_news()
        if cached is not None:
            logger.info(f"Returning cached news ({len(cached)} articles)")
            return cached
        
        try:
            # Import feedparser for RSS scraping
            import feedparser
            
            # RSS feeds to scrape - Focus on INFRASTRUCTURE & METRO projects
            # Based on user's requirement for news like:
            # - Noida Metro expansion (Aqua Line extension)
            # - Pune Metro Phase 2 (Line 4B and 4C)  
            # - Meerut Metro (Namo Bharat corridor)
            rss_feeds = [
                {
                    'name': '🚇 Metro Projects',
                    'url': 'https://news.google.com/rss/search?q=india+metro+expansion+line+extension+stations&hl=en-IN&gl=IN&ceid=IN:en'
                },
                {
                    'name': '🏗️ Infrastructure TOI',
                    'url': 'https://news.google.com/rss/search?q=site:timesofindia.indiatimes.com+infrastructure+metro+highway+cabinet+approval&hl=en-IN&gl=IN&ceid=IN:en'
                },
                {
                    'name': '🚉 Urban Transport',
                    'url': 'https://news.google.com/rss/search?q=india+urban+transport+metro+rapid+rail+namo+bharat&hl=en-IN&gl=IN&ceid=IN:en'
                },
                {
                    'name': '🏛️ Government Projects',
                    'url': 'https://news.google.com/rss/search?q=india+inaugurated+cabinet+approves+new+stations+infrastructure&hl=en-IN&gl=IN&ceid=IN:en'
                },
                {
                    'name': '📍 Regional Metro News',
                    'url': 'https://news.google.com/rss/search?q=delhi+metro+noida+metro+gurugram+metro+pune+metro+mumbai+metro&hl=en-IN&gl=IN&ceid=IN:en'
                },
                {
                    'name': '🛣️ Highways & Corridors',
                    'url': 'https://news.google.com/rss/search?q=india+highway+corridor+expressway+phase+2+3+extension&hl=en-IN&gl=IN&ceid=IN:en'
                }
            ]
            
            # Infrastructure & Metro keywords for filtering
            # Focus on specific project types mentioned in user's examples
            INFRASTRUCTURE_KEYWORDS = [
                # Metro/Urban Transport
                'metro', 'metro expansion', 'metro line', 'line extension', 'new stations',
                'aqua line', 'blue line', 'green line', 'red line', 'yellow line', 'violet line',
                'phase 2', 'phase 3', 'phase 4', 'phase 2b', 'phase 4a', 'phase 4b', 'phase 4c',
                'rapid rail', 'namo bharat', 'rrts', 'urban transport',
                'noida metro', 'delhi metro', 'mumbai metro', 'pune metro', 'bangalore metro',
                'hyderabad metro', 'chennai metro', 'kolkata metro', 'meerut metro',
                'gurugram metro', 'faridabad metro', 'ghaziabad metro',
                
                # Highways & Roads
                'highway', 'expressway', 'corridor', 'eastern peripheral', 'western peripheral',
                'dwarka expressway', 'mumbai-pune expressway', 'delhi-mumbai expressway',
                
                # Government Actions
                'cabinet okays', 'cabinet approves', 'inaugurated', 'foundation stone',
                'tender invited', 'bids invited', 'contract awarded', 'construction begins',
                'trial run', 'commercial operation', 'partial opening',
                
                # Infrastructure
                'infrastructure', 'smart city', 'airport', 'new terminal', 'runway',
                'bridge', 'tunnel', 'flyover', 'underpass', 'elevated road',
                
                # Specific Projects
                'jewar airport', 'navi mumbai airport', 'pune metro', 'noida metro',
                'meerut metro', 'bangalore suburban rail', 'mumbai suburban',
            ]
            
            all_articles = []
            
            for feed_config in rss_feeds:
                try:
                    feed = feedparser.parse(feed_config['url'])
                    
                    for entry in feed.entries[:5]:  # Limit to 5 per feed
                        # Generate unique ID
                        id_source = entry.get('link', '') or entry.get('title', '')
                        article_id = hashlib.md5(id_source.encode()).hexdigest()
                        
                        article = {
                            'id': article_id,
                            'title': entry.get('title', 'No title'),
                            'url': entry.get('link', ''),
                            'source': feed_config['name'],
                            'content': entry.get('summary', entry.get('description', '')),
                            'published_at': entry.get('published', ''),
                            'category': 'general'
                        }
                        all_articles.append(article)
                        
                except Exception as e:
                    logger.error(f"Error fetching {feed_config['name']}: {e}")
            
            # Filter and categorize articles
            processed = []
            seen_titles = set()
            
            for article in all_articles:
                title_lower = article.get('title', '').lower()
                content_lower = article.get('content', '').lower()
                text = title_lower + ' ' + content_lower
                
                # Skip if already seen
                title_key = article.get('title', '').lower()[:50]
                if title_key in seen_titles:
                    continue
                seen_titles.add(title_key)
                
                # Must have at least one infrastructure keyword
                has_infrastructure = any(kw in text for kw in INFRASTRUCTURE_KEYWORDS)
                if not has_infrastructure:
                    continue
                
                # IMPACT SCORING SYSTEM
                # Calculate impact score based on keywords
                impact_score = 0
                
                # HIGH IMPACT keywords (major announcements, inaugurations, cabinet approvals)
                HIGH_IMPACT_KEYWORDS = [
                    'cabinet okays', 'cabinet approves', 'cabinet clears',
                    'inaugurated', 'prime minister inaugurates', 'pm inaugurates',
                    'foundation stone', 'foundation laid',
                    'green signal', 'approved', 'sanctioned',
                    'rs crore', 'thousand crore', 'billion', 'mega project',
                    'major breakthrough', 'landmark', 'historic',
                ]
                
                # MEDIUM IMPACT keywords (tenders, contracts, construction progress)
                MEDIUM_IMPACT_KEYWORDS = [
                    'tender invited', 'bids invited', 'tender floated',
                    'contract awarded', 'contract signed', 'l&t', 'lt', 'tata', 'reliance',
                    'construction begins', 'work begins', 'construction underway',
                    'trial run', 'test run', 'commissioning',
                    'phase complete', 'stretch opens', 'section opens',
                    'deadline extended', 'cost escalation',
                ]
                
                # SMART NEWS keywords (technology, innovation, sustainability)
                SMART_NEWS_KEYWORDS = [
                    'smart city', 'smart metro', 'ai-powered', 'autonomous',
                    'solar', 'green energy', 'renewable', 'zero emission',
                    'wifi', 'digital', 'app', 'mobile ticketing',
                    'waterproof', 'anti-corrosion', 'modern technology',
                    'cctv', 'surveillance', 'automatic', 'driverless',
                ]
                
                # Calculate score
                high_impact_matches = sum(1 for kw in HIGH_IMPACT_KEYWORDS if kw in text)
                medium_impact_matches = sum(1 for kw in MEDIUM_IMPACT_KEYWORDS if kw in text)
                smart_matches = sum(1 for kw in SMART_NEWS_KEYWORDS if kw in text)
                
                # Determine impact level
                if high_impact_matches >= 1:
                    article['impact'] = 'HIGH'
                    impact_score = 3
                elif medium_impact_matches >= 1 or smart_matches >= 2:
                    article['impact'] = 'MEDIUM'
                    impact_score = 2
                else:
                    article['impact'] = 'LOW'
                    impact_score = 1
                
                # Determine category based on project type + impact
                is_smart = smart_matches >= 1
                
                if is_smart:
                    article['category'] = 'smart_news'
                elif any(kw in text for kw in ['metro', 'line extension', 'new stations', 'aqua line', 'rapid rail', 'rrts', 'namo bharat']):
                    article['category'] = 'metro_projects'
                elif any(kw in text for kw in ['highway', 'expressway', 'corridor', 'eastern peripheral', 'western peripheral']):
                    article['category'] = 'highways'
                elif any(kw in text for kw in ['airport', 'terminal', 'runway', 'jewar', 'navi mumbai airport']):
                    article['category'] = 'airports'
                elif any(kw in text for kw in ['cabinet okays', 'cabinet approves', 'inaugurated', 'foundation stone', 'tender', 'bids invited']):
                    article['category'] = 'government_updates'
                elif any(kw in text for kw in ['bridge', 'tunnel', 'flyover', 'underpass']):
                    article['category'] = 'civil_infrastructure'
                else:
                    article['category'] = 'infrastructure'
                
                processed.append(article)
            
            # Cache the results
            self._set_news_cache(processed)
            
            logger.info(f"Fetched {len(processed)} news articles on demand")
            return processed
            
        except Exception as e:
            logger.error(f"Error fetching on-demand news: {e}")
            return []
    
    def _format_news_message(self, articles: List[Dict[str, Any]]) -> str:
        """
        Format news articles for Telegram - IMPACT LEVEL CATEGORIZATION
        
        Args:
            articles: List of news articles
            
        Returns:
            Formatted message string
        """
        import html
        
        now = datetime.now()
        date_str = now.strftime('%B %d, %Y')
        time_str = now.strftime('%I:%M %p')
        
        # Impact level emojis
        impact_emojis = {
            'HIGH': '🔴 HIGH IMPACT',
            'MEDIUM': '🟡 MEDIUM IMPACT', 
            'LOW': '🟢 LOW IMPACT'
        }
        
        # Category emoji mapping
        category_emojis = {
            'smart_news': '🤖 SMART NEWS',
            'metro_projects': '🚇 METRO PROJECTS',
            'highways': '🛣️ HIGHWAYS & EXPRESSWAYS',
            'airports': '✈️ AIRPORTS',
            'government_updates': '🏛️ GOVERNMENT UPDATES',
            'civil_infrastructure': '🌉 BRIDGES & TUNNELS',
            'smart_cities': '🏙️ SMART CITIES',
            'infrastructure': '🏗️ INFRASTRUCTURE',
            'general': '📰 GENERAL'
        }
        
        # Count articles by impact
        high_count = sum(1 for a in articles if a.get('impact') == 'HIGH')
        medium_count = sum(1 for a in articles if a.get('impact') == 'MEDIUM')
        low_count = sum(1 for a in articles if a.get('impact') == 'LOW')
        smart_count = sum(1 for a in articles if a.get('category') == 'smart_news')
        
        lines = [
            f"<b>🚇 Infrastructure News - Impact Analysis</b>",
            f"📅 {date_str} | ⏰ {time_str}",
            f"📊 {len(articles)} articles | 🤖 {smart_count} Smart",
            f"🔴 {high_count} High | 🟡 {medium_count} Medium | 🟢 {low_count} Low",
            "",
            "━━━━━━━━━━━━━━━━━━━━"
        ]
        
        if not articles:
            lines.append("")
            lines.append("No new infrastructure articles found at the moment.")
            lines.append("Try again in a few minutes!")
        else:
            # Group by IMPACT LEVEL first (High -> Medium -> Low)
            impact_order = ['HIGH', 'MEDIUM', 'LOW']
            
            for impact in impact_order:
                impact_articles = [a for a in articles if a.get('impact') == impact]
                
                if not impact_articles:
                    continue
                
                # Add impact level header
                lines.append("")
                lines.append(f"<b>{impact_emojis.get(impact, impact)}</b>")
                lines.append("")
                
                # Within each impact level, group by category
                categories = {}
                for article in impact_articles:
                    cat = article.get('category', 'general')
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(article)
                
                # Category priority order
                category_priority = ['smart_news', 'metro_projects', 'highways', 'airports', 
                                    'government_updates', 'civil_infrastructure', 'smart_cities', 
                                    'infrastructure', 'general']
                
                sorted_categories = sorted(categories.items(), 
                                          key=lambda x: category_priority.index(x[0]) if x[0] in category_priority else 999)
                
                for category, cat_articles in sorted_categories:
                    # Category sub-header with emoji
                    cat_display = category_emojis.get(category, f"📁 {category.upper().replace('_', ' ')}")
                    lines.append(f"  <i>{cat_display}</i>")
                    
                    for article in cat_articles[:3]:  # Max 3 per category within impact level
                        title = html.escape(article.get('title', 'No title')[:75])
                        url = html.escape(article.get('url', ''), quote=True)
                        source = article.get('source', 'Unknown').replace('Google News - ', '')
                        
                        # Add smart indicator if it's smart news
                        smart_indicator = "🤖 " if article.get('category') == 'smart_news' else "• "
                        
                        if url:
                            lines.append(f"    {smart_indicator}<a href='{url}'>{title}</a>")
                        else:
                            lines.append(f"    {smart_indicator}{title}")
                        
                        # Show source only if it's informative
                        if source and not source.startswith('http'):
                            lines.append(f"      <i>{html.escape(source)}</i>")
                    
                    lines.append("")  # Empty line between categories
        
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append("🤖 <i>On-demand infra news via Khabri Bot</i>")
        lines.append(f"⏱️ <i>Rate limit: 1 request per {_NEWS_RATE_LIMIT_MINUTES} minutes</i>")
        
        return "\n".join(lines)
    
    def _format_news_email_html(self, articles: List[Dict[str, Any]], requested_by: str = "Telegram User") -> str:
        """
        Format news articles as HTML email
        
        Args:
            articles: List of news articles
            requested_by: Who requested the news
            
        Returns:
            HTML formatted email body
        """
        import html
        
        now = datetime.now()
        date_str = now.strftime('%B %d, %Y')
        time_str = now.strftime('%I:%M %p')
        
        # Impact colors for email
        impact_colors = {
            'HIGH': '#e74c3c',    # Red
            'MEDIUM': '#f39c12',  # Orange
            'LOW': '#27ae60'      # Green
        }
        
        category_emojis = {
            'smart_news': '🤖 SMART NEWS',
            'metro_projects': '🚇 METRO PROJECTS',
            'highways': '🛣️ HIGHWAYS & EXPRESSWAYS',
            'airports': '✈️ AIRPORTS',
            'government_updates': '🏛️ GOVERNMENT UPDATES',
            'civil_infrastructure': '🌉 BRIDGES & TUNNELS',
            'smart_cities': '🏙️ SMART CITIES',
            'infrastructure': '🏗️ INFRASTRUCTURE',
            'general': '📰 GENERAL'
        }
        
        # Count by impact
        high_count = sum(1 for a in articles if a.get('impact') == 'HIGH')
        medium_count = sum(1 for a in articles if a.get('impact') == 'MEDIUM')
        low_count = sum(1 for a in articles if a.get('impact') == 'LOW')
        smart_count = sum(1 for a in articles if a.get('category') == 'smart_news')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
                .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 15px; margin-bottom: 20px; }}
                .meta {{ color: #7f8c8d; font-size: 14px; margin-bottom: 25px; }}
                .impact-header {{ padding: 15px 20px; margin: 25px 0 15px 0; border-radius: 5px; font-weight: bold; font-size: 18px; color: white; }}
                .impact-high {{ background: linear-gradient(135deg, #e74c3c, #c0392b); }}
                .impact-medium {{ background: linear-gradient(135deg, #f39c12, #d68910); }}
                .impact-low {{ background: linear-gradient(135deg, #27ae60, #229954); }}
                .category {{ background: linear-gradient(135deg, #3498db, #2980b9); color: white; padding: 8px 15px; margin: 15px 0 10px 0; border-radius: 5px; font-weight: bold; font-size: 14px; }}
                .article {{ background: #f9f9f9; padding: 15px; margin: 10px 0; border-left: 4px solid #3498db; border-radius: 0 5px 5px 0; }}
                .article-high {{ border-left-color: #e74c3c; }}
                .article-medium {{ border-left-color: #f39c12; }}
                .article-low {{ border-left-color: #27ae60; }}
                .article h3 {{ margin: 0 0 8px 0; color: #2c3e50; font-size: 15px; }}
                .article .source {{ color: #7f8c8d; font-size: 12px; margin-top: 8px; }}
                .article .impact-badge {{ display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 10px; color: white; margin-left: 10px; }}
                .badge-high {{ background: #e74c3c; }}
                .badge-medium {{ background: #f39c12; }}
                .badge-low {{ background: #27ae60; }}
                .smart-badge {{ background: #9b59b6; }}
                .article a {{ color: #3498db; text-decoration: none; }}
                .article a:hover {{ text-decoration: underline; }}
                .stats {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .footer {{ text-align: center; color: #95a5a6; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }}
                .empty {{ text-align: center; padding: 40px; color: #95a5a6; }}
                .header-icon {{ font-size: 40px; margin-bottom: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header-icon">🚇</div>
                <h1>Infrastructure News - Impact Analysis</h1>
                <div class="meta">
                    📅 {date_str} | ⏰ {time_str}<br>
                    👤 Requested by: {html.escape(requested_by)}
                </div>
                <div class="stats">
                    <b>📊 Summary:</b> {len(articles)} articles | 
                    <span style="color:#e74c3c">🔴 {high_count} High</span> | 
                    <span style="color:#f39c12">🟡 {medium_count} Medium</span> | 
                    <span style="color:#27ae60">🟢 {low_count} Low</span> | 
                    <span style="color:#9b59b6">🤖 {smart_count} Smart</span>
                </div>
        """
        
        if not articles:
            html_content += '<div class="empty"><p>No new infrastructure articles found at the moment.</p><p>Try again in a few minutes!</p></div>'
        else:
            # Group by IMPACT LEVEL first
            impact_order = [('HIGH', 'impact-high'), ('MEDIUM', 'impact-medium'), ('LOW', 'impact-low')]
            
            for impact, css_class in impact_order:
                impact_articles = [a for a in articles if a.get('impact') == impact]
                
                if not impact_articles:
                    continue
                
                # Impact level header
                impact_label = f"🔴 {impact} IMPACT" if impact == 'HIGH' else f"🟡 {impact} IMPACT" if impact == 'MEDIUM' else f"🟢 {impact} IMPACT"
                html_content += f'<div class="impact-header {css_class}">{impact_label}</div>'
                
                # Group by category within impact level
                categories = {}
                for article in impact_articles:
                    cat = article.get('category', 'general')
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(article)
                
                category_priority = ['smart_news', 'metro_projects', 'highways', 'airports', 
                                    'government_updates', 'civil_infrastructure', 'smart_cities', 
                                    'infrastructure', 'general']
                sorted_categories = sorted(categories.items(), 
                                          key=lambda x: category_priority.index(x[0]) if x[0] in category_priority else 999)
                
                for category, cat_articles in sorted_categories:
                    cat_display = category_emojis.get(category, category.upper().replace('_', ' '))
                    html_content += f'<div class="category">{cat_display}</div>'
                
                for article in cat_articles[:3]:
                    title = html.escape(article.get('title', 'No title'))
                    url = article.get('url', '')
                    source = html.escape(article.get('source', 'Unknown'))
                    article_impact = article.get('impact', 'LOW')
                    is_smart = article.get('category') == 'smart_news'
                    
                    # Impact badge
                    badge_class = f"badge-{article_impact.lower()}"
                    badge_text = article_impact
                    
                    # Smart badge
                    smart_badge = '<span class="impact-badge smart-badge">🤖 SMART</span>' if is_smart else ''
                    
                    # Article border color based on impact
                    article_class = f"article article-{article_impact.lower()}"
                    
                    html_content += f'''
                    <div class="{article_class}">
                        <h3>{f'<a href="{url}">{title}</a>' if url else title}<span class="impact-badge {badge_class}">{badge_text}</span>{smart_badge}</h3>
                        <div class="source">📰 {source}</div>
                    </div>
                    '''
        
        html_content += """
            <div class="footer">
                🤖 Powered by <strong>Khabri News Intelligence</strong><br>
                ⚡ Auto-delivered via Telegram Bot<br>
                📧 Also sent to your email for convenience
            </div>
        </div>
        </body>
        </html>
        """
        
        return html_content
    
    async def _send_news_email(self, articles: List[Dict[str, Any]], requested_by: str = "Telegram User") -> bool:
        """
        Send news via email
        
        Args:
            articles: List of news articles
            requested_by: Who requested the news
            
        Returns:
            True if successful
        """
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Get email credentials from environment
        # Support both naming conventions used in the project
        smtp_host = os.getenv('EMAIL_SMTP_HOST') or os.getenv('SMTP_HOST', 'smtp.gmail.com')
        raw_port = os.getenv('EMAIL_SMTP_PORT') or os.getenv('SMTP_PORT')
        try:
            smtp_port = int(raw_port) if raw_port else 587
        except ValueError:
            smtp_port = 587
        
        # Try multiple env var names for email credentials
        username = (os.getenv('EMAIL_USERNAME') or 
                   os.getenv('SMTP_USERNAME') or 
                   os.getenv('GMAIL_ADDRESS'))
        
        password = (os.getenv('EMAIL_PASSWORD') or 
                   os.getenv('SMTP_PASSWORD') or 
                   os.getenv('GMAIL_APP_PASSWORD'))
        
        sender = username  # Use username as sender
        
        recipient = (os.getenv('EMAIL_TO') or 
                    os.getenv('EMAIL_RECIPIENT') or 
                    os.getenv('RECIPIENT_EMAIL'))
        
        if not all([username, password, recipient]):
            logger.warning("Email not configured - skipping email notification")
            logger.debug(f"Email config - username: {username is not None}, password: {password is not None}, recipient: {recipient is not None}")
            return False
        
        logger.info(f"Sending email to {recipient} via {smtp_host}:{smtp_port}")
        
        try:
            # Format email
            now = datetime.now()
            subject = f"🚇 On-Demand Infrastructure News - {now.strftime('%B %d, %Y')}"
            body_html = self._format_news_email_html(articles, requested_by)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = recipient
            
            html_part = MIMEText(body_html, 'html')
            msg.attach(html_part)
            
            # Send via SMTP
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                server.starttls()
                server.login(username, password)
                recipients = [addr.strip() for addr in recipient.split(',') if addr.strip()]
                server.sendmail(sender, recipients, msg.as_string())
            
            logger.info(f"News email sent to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send news email: {e}")
            return False
    
    def _get_all_telegram_chat_ids(self) -> List[str]:
        """
        Get all Telegram chat IDs to send news to
        Returns primary chat ID and any additional configured IDs
        
        Returns:
            List of chat IDs
        """
        chat_ids = []
        
        # Primary chat ID from authorized list
        if self.authorized_chat_ids:
            chat_ids.extend(list(self.authorized_chat_ids))
        
        # Also check for additional comma-separated chat IDs
        additional_ids = os.getenv('TELEGRAM_ADDITIONAL_CHAT_IDS', '')
        if additional_ids:
            for cid in additional_ids.split(','):
                cid = cid.strip()
                if cid and cid not in chat_ids:
                    chat_ids.append(cid)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_ids = []
        for cid in chat_ids:
            if cid not in seen:
                seen.add(cid)
                unique_ids.append(cid)
        
        return unique_ids
    
    async def handle_news_command(self, chat_id: str) -> bool:
        """
        Handle /news command or news keyword - send on-demand news
        Sends to: Telegram (requester + all configured IDs) + Email
        
        Args:
            chat_id: Chat ID that sent the command
            
        Returns:
            True if successful
        """
        logger.info(f"Handling news request from chat_id: {chat_id}")
        
        # Check rate limit
        is_allowed, seconds_remaining = self._check_rate_limit(chat_id)
        
        if not is_allowed:
            minutes = seconds_remaining // 60
            seconds = seconds_remaining % 60
            
            self.send_message(
                chat_id,
                f"⏱️ <b>Rate Limited</b>\n\n"
                f"Please wait <b>{minutes}m {seconds}s</b> before requesting news again.\n\n"
                f"This prevents spam and ensures fair usage. 💙",
                parse_mode='HTML'
            )
            return False
        
        # Send "typing" indicator
        self._send_chat_action(chat_id, 'typing')
        
        # Acknowledge the request
        self.send_message(
            chat_id,
            "🚇 <b>Fetching latest infrastructure & metro news...</b>\n"
            "Sending to Telegram + Email ⏳",
            parse_mode='HTML'
        )
        
        try:
            # Fetch news
            articles = await self._fetch_news_on_demand()
            
            # Update rate limit timestamp
            self._news_last_request[chat_id] = datetime.now()
            
            # Format messages
            telegram_msg = self._format_news_message(articles)
            
            # Send to all Telegram chat IDs
            all_chat_ids = self._get_all_telegram_chat_ids()
            telegram_success_count = 0
            
            for target_chat_id in all_chat_ids:
                try:
                    success = self.send_message(target_chat_id, telegram_msg, parse_mode='HTML')
                    if success:
                        telegram_success_count += 1
                        logger.info(f"Sent news to Telegram chat {target_chat_id}")
                    else:
                        logger.error(f"Failed to send news to Telegram chat {target_chat_id}")
                except Exception as e:
                    logger.error(f"Error sending to Telegram chat {target_chat_id}: {e}")
            
            # Send Email
            email_success = await self._send_news_email(articles, requested_by=f"Telegram User ({chat_id})")
            
            # Confirm to requester
            success_summary = f"✅ <b>News delivered!</b>\n\n"
            success_summary += f"📱 Telegram: {telegram_success_count} chat(s)\n"
            success_summary += f"📧 Email: {'Sent' if email_success else 'Failed/Not configured'}\n"
            success_summary += f"📊 Articles: {len(articles)}\n\n"
            success_summary += "Check your email and Telegram for the full news update."
            
            self.send_message(chat_id, success_summary, parse_mode='HTML')
            
            logger.info(f"News request completed. Telegram: {telegram_success_count}, Email: {email_success}")
            return telegram_success_count > 0
            
        except Exception as e:
            logger.error(f"Error in handle_news_command: {e}", exc_info=True)
            self.send_message(
                chat_id,
                "❌ <b>Sorry, couldn't fetch news right now.</b>\n\n"
                "Please try again in a few minutes.",
                parse_mode='HTML'
            )
            return False
    
    def _send_chat_action(self, chat_id: str, action: str) -> bool:
        """
        Send chat action (typing, uploading_photo, etc.)
        
        Args:
            chat_id: Chat ID
            action: Action type (typing, uploading_photo, etc.)
            
        Returns:
            True if successful
        """
        if not self.bot_token:
            return False
        
        url = f"{self.api_url}/sendChatAction"
        payload = {
            'chat_id': chat_id,
            'action': action
        }
        
        try:
            response = requests.post(url, json=payload, timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def process_message(self, message: Dict[str, Any]) -> bool:
        """
        Process a single message

        Args:
            message: Message object from Telegram

        Returns:
            True if processed successfully
        """
        chat_id = str(message.get('chat', {}).get('id', ''))
        if not chat_id:
            logger.warning("Received message without chat ID")
            return False
        text = message.get('text', '')

        # Check authorization (if configured)
        if self.authorized_chat_ids and chat_id not in self.authorized_chat_ids:
            logger.warning(f"Unauthorized access attempt from chat_id: {chat_id}")
            self.send_message(
                chat_id,
                "⛔ *Access Denied*\n\n"
                "You are not authorized to use this bot.\n"
                "Contact the administrator for access.\n\n"
                f"Your Chat ID: `{chat_id}`"
            )
            return False

        # Handle commands
        if text.startswith('/fix'):
            return self.handle_fix_command(chat_id, text)
        elif text.startswith('/status'):
            return self.handle_status_command(chat_id)
        elif text.startswith('/undo'):
            return self.handle_undo_command(chat_id)
        elif text.startswith('/help') or text.startswith('/start'):
            return self.handle_help_command(chat_id)
        elif text.startswith('/news'):
            # Handle /news command
            return asyncio.run(self.handle_news_command(chat_id))
        else:
            # Check for natural language undo
            if any(phrase in text.lower() for phrase in ['undo', 'rollback', 'revert', 'restore']):
                if any(phrase in text.lower() for phrase in ['last', 'previous', 'recent']):
                    return self.handle_undo_command(chat_id)
            
            # Check for news keyword trigger
            if self._is_news_trigger(text):
                logger.info(f"News trigger detected from {chat_id}: '{text}'")
                return asyncio.run(self.handle_news_command(chat_id))

            # Try Smart Intent Parsing for non-command messages
            if SMART_INTENT_AVAILABLE and parse_intent and len(text) > 5:
                try:
                    intent = parse_intent(text)
                    if intent and intent.confidence >= 0.5:  # Lowered from 0.6 to catch more patterns
                        logger.info(f"Smart intent detected: {intent.intent_type} with {intent.confidence:.0%} confidence")
                        return self.handle_smart_intent(chat_id, intent)
                except Exception as e:
                    logger.error(f"Error parsing smart intent: {e}")
            
            # Unknown command or no intent matched
            self.send_message(
                chat_id,
                "❓ I didn't understand that.\n\n"
                "<b>Quick Commands:</b>\n"
                "• Type <code>news</code> for latest real estate news 📰\n"
                "• Use <code>/fix &lt;description&gt;</code> for detailed fixes\n\n"
                "<b>Smart Commands:</b>\n"
                "• <code>add automotive companies like Mahindra</code>\n"
                "• <code>change morning time to 8 AM</code>\n"
                "• <code>show all bollywood celebrities</code>\n\n"
                "Or use <code>/help</code> for more options.",
                parse_mode='HTML'
            )
            return False

    def run_polling(self):
        """
        Run bot in polling mode (long polling)
        Continuously checks for new messages
        """
        if not self.bot_token:
            logger.error("Cannot start polling: TELEGRAM_BOT_TOKEN not set")
            return

        logger.info("Starting Telegram bot polling...")

        while True:
            try:
                updates = self.get_updates(offset=self.last_update_id + 1)

                for update in updates:
                    update_id = update.get('update_id')
                    if update_id is None:
                        continue
                    self.last_update_id = max(self.last_update_id, update_id)

                    if 'message' in update:
                        self.process_message(update['message'])
                    elif 'callback_query' in update:
                        # Handle inline button clicks
                        self.handle_callback_query(update['callback_query'])

            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                time.sleep(_ERROR_BACKOFF_SECONDS)


if __name__ == "__main__":
    # Run bot in standalone mode
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    bot = TelegramBotHandler()
    bot.run_polling()
