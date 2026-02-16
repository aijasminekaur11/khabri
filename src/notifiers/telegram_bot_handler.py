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

📰 Type `news` or `/news` - Get latest real estate news instantly
   • Fetches fresh news from multiple sources
   • Rate limit: 1 request per 5 minutes
   • Includes: Property, Infrastructure, Policy, Finance news

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
            
            # RSS feeds to scrape - same as github_digest_runner.py
            rss_feeds = [
                {
                    'name': 'Real Estate India',
                    'url': 'https://news.google.com/rss/search?q=indian+real+estate+property&hl=en-IN&gl=IN&ceid=IN:en'
                },
                {
                    'name': 'Property Prices',
                    'url': 'https://news.google.com/rss/search?q=india+property+prices+housing+market&hl=en-IN&gl=IN&ceid=IN:en'
                },
                {
                    'name': 'Home Loan',
                    'url': 'https://news.google.com/rss/search?q=home+loan+interest+rate+EMI&hl=en-IN&gl=IN&ceid=IN:en'
                },
                {
                    'name': 'Infrastructure',
                    'url': 'https://news.google.com/rss/search?q=india+infrastructure+metro+highway+smart+city&hl=en-IN&gl=IN&ceid=IN:en'
                }
            ]
            
            # Real estate keywords for filtering
            REAL_ESTATE_KEYWORDS = [
                'real estate', 'property', 'housing', 'home loan', 'affordable housing',
                'pmay', 'pradhan mantri awas', 'rera', 'stamp duty', 'builder', 'developer',
                'residential', 'commercial property', 'realty', 'home buyer', 'rental',
                'apartment', 'flat', 'plot', 'land', 'construction', 'infrastructure',
                'metro', 'highway', 'airport', 'smart city', 'dlf', 'godrej properties',
                'home loan rate', 'emi', 'mortgage', 'housing finance', 'property prices',
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
                
                # Must have at least one real estate keyword
                has_real_estate = any(kw in text for kw in REAL_ESTATE_KEYWORDS)
                if not has_real_estate:
                    continue
                
                # Categorize
                if any(kw in text for kw in ['rera', 'regulation', 'policy', 'government', 'pmay']):
                    article['category'] = 'policy'
                elif any(kw in text for kw in ['price', 'rate', 'market', 'demand', 'sales']):
                    article['category'] = 'market_updates'
                elif any(kw in text for kw in ['metro', 'infrastructure', 'airport', 'highway']):
                    article['category'] = 'infrastructure'
                elif any(kw in text for kw in ['launch', 'new project', 'upcoming']):
                    article['category'] = 'launches'
                elif any(kw in text for kw in ['loan', 'emi', 'interest', 'rbi', 'mortgage']):
                    article['category'] = 'finance'
                
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
        Format news articles for Telegram
        
        Args:
            articles: List of news articles
            
        Returns:
            Formatted message string
        """
        import html
        
        now = datetime.now()
        date_str = now.strftime('%B %d, %Y')
        time_str = now.strftime('%I:%M %p')
        
        lines = [
            f"<b>📰 Latest Real Estate News</b>",
            f"📅 {date_str} | ⏰ {time_str}",
            f"📊 {len(articles)} articles",
            "",
            "━━━━━━━━━━━━━━━━━━━━"
        ]
        
        if not articles:
            lines.append("")
            lines.append("No new articles found at the moment.")
            lines.append("Try again in a few minutes!")
        else:
            # Group by category
            categories = {}
            for article in articles[:15]:  # Max 15 articles
                cat = article.get('category', 'general')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(article)
            
            for category, cat_articles in categories.items():
                lines.append("")
                lines.append(f"📁 <b>{category.upper().replace('_', ' ')}</b>")
                
                for article in cat_articles[:3]:  # Max 3 per category
                    title = html.escape(article.get('title', 'No title')[:70])
                    url = html.escape(article.get('url', ''), quote=True)
                    source = html.escape(article.get('source', 'Unknown').replace('Google News - ', ''))
                    
                    lines.append(f"")
                    if url:
                        lines.append(f"• <a href='{url}'>{title}</a>")
                    else:
                        lines.append(f"• {title}")
                    lines.append(f"  📰 {source}")
        
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append("🤖 <i>On-demand news via Khabri Bot</i>")
        lines.append(f"⏱️ <i>Rate limit: 1 request per {_NEWS_RATE_LIMIT_MINUTES} minutes</i>")
        
        return "\n".join(lines)
    
    async def handle_news_command(self, chat_id: str) -> bool:
        """
        Handle /news command or news keyword - send on-demand news
        
        Args:
            chat_id: Chat ID to send news to
            
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
            "🔍 <b>Fetching latest real estate news...</b>\n"
            "This will take a few seconds ⏳",
            parse_mode='HTML'
        )
        
        try:
            # Fetch news
            articles = await self._fetch_news_on_demand()
            
            # Update rate limit timestamp
            self._news_last_request[chat_id] = datetime.now()
            
            # Format and send
            message = self._format_news_message(articles)
            
            # Send with retry
            success = self.send_message(chat_id, message, parse_mode='HTML')
            
            if success:
                logger.info(f"Sent on-demand news to {chat_id} ({len(articles)} articles)")
            else:
                logger.error(f"Failed to send news to {chat_id}")
                # Try sending shorter message
                short_msg = f"📰 <b>News Update</b>\n\nFound {len(articles)} articles.\n\n(Some articles may have been too long to display)"
                self.send_message(chat_id, short_msg, parse_mode='HTML')
            
            return success
            
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
