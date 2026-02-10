"""
Telegram Bot Command Handler
Handles incoming commands from users and triggers GitHub workflows

This allows users to:
- Send /fix commands to create GitHub issues
- Check status of fixes
- Get help information
"""

import os
import logging
import requests
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import Claude fixer, but don't fail if not available
try:
    from .claude_auto_fixer import ClaudeAutoFixer
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    logger.warning("Claude Auto-Fixer not available")
    ClaudeAutoFixer = None


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

        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.github_api = "https://api.github.com"

        # Initialize Claude Auto-Fixer if available
        if CLAUDE_AVAILABLE and ClaudeAutoFixer:
            self.claude_fixer = ClaudeAutoFixer()
        else:
            self.claude_fixer = None
            logger.info("Claude Auto-Fixer disabled")

        # Track last update ID to avoid duplicate processing
        self.last_update_id = 0

    def get_updates(self, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get new updates from Telegram

        Args:
            offset: Update ID to start from

        Returns:
            List of update objects
        """
        params = {
            'timeout': 30,
            'offset': offset
        }

        try:
            response = requests.get(
                f"{self.api_url}/getUpdates",
                params=params,
                timeout=35
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('result', [])
            else:
                logger.error(f"Failed to get updates: {response.status_code}")
                return []

        except Exception as e:
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
        except Exception as e:
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
            if response.status_code == 200:
                logger.info(f"Added label '{label}' to issue #{issue_number}")
                return True
            else:
                logger.warning(f"Failed to add label: {response.status_code}")
                return False
        except Exception as e:
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
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            return False

    def create_github_issue(
        self,
        title: str,
        body: str,
        labels: List[str] = None
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

        except Exception as e:
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

        except Exception as e:
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

            if analysis_result['success']:
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

**Available Commands:**

📝 `/fix <description>` - Create automated fix request
   Example: `/fix Budget alerts showing wrong news`

📊 `/status` - Check status of recent fixes

❓ `/help` - Show this help message

---

**How it works:**
1. You send `/fix` command with description
2. Bot creates GitHub issue automatically
3. Claude Code analyzes and fixes the issue
4. Bot notifies you when PR is ready
5. You review and merge the fix

**Example Usage:**
```
/fix Login page is broken on mobile
/fix Budget alerts not filtering correctly
/fix Telegram notifications not sending
```

Need help? Contact support or check the GitHub repository.
"""

        self.send_message(chat_id, help_text)
        return True

    def process_message(self, message: Dict[str, Any]) -> bool:
        """
        Process a single message

        Args:
            message: Message object from Telegram

        Returns:
            True if processed successfully
        """
        chat_id = str(message['chat']['id'])
        text = message.get('text', '')

        # Handle commands
        if text.startswith('/fix'):
            return self.handle_fix_command(chat_id, text)
        elif text.startswith('/status'):
            return self.handle_status_command(chat_id)
        elif text.startswith('/help') or text.startswith('/start'):
            return self.handle_help_command(chat_id)
        else:
            # Unknown command
            self.send_message(
                chat_id,
                "❓ Unknown command.\n\n"
                "Use `/help` to see available commands."
            )
            return False

    def run_polling(self):
        """
        Run bot in polling mode (long polling)
        Continuously checks for new messages
        """
        logger.info("Starting Telegram bot polling...")

        while True:
            try:
                updates = self.get_updates(offset=self.last_update_id + 1)

                for update in updates:
                    update_id = update['update_id']
                    self.last_update_id = max(self.last_update_id, update_id)

                    if 'message' in update:
                        self.process_message(update['message'])

            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                # Continue polling even after errors


if __name__ == "__main__":
    # Run bot in standalone mode
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    bot = TelegramBotHandler()
    bot.run_polling()
