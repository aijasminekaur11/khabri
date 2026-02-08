"""
Telegram Notifier
Sends notifications via Telegram Bot API
"""

import os
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import requests
from .base_notifier import BaseNotifier, NotificationError


logger = logging.getLogger(__name__)


class TelegramNotifier(BaseNotifier):
    """
    Telegram notification implementation using Bot API.

    Requirements:
    - Respect 4096 char message limit
    - Support markdown formatting
    - Handle rate limiting (30 msgs/sec)
    - Implement retry logic with exponential backoff
    """

    # Telegram message limits
    MAX_MESSAGE_LENGTH = 4096
    RATE_LIMIT_DELAY = 0.034  # ~30 msgs/sec

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Initialize TelegramNotifier

        Args:
            bot_token: Telegram Bot API token (defaults to env TELEGRAM_BOT_TOKEN)
            chat_id: Telegram chat ID (defaults to env TELEGRAM_CHAT_ID)
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')

        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not configured. Notifier will not function.")

        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.last_send_time = 0

    def _rate_limit(self):
        """Enforce rate limiting between messages"""
        elapsed = time.time() - self.last_send_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_send_time = time.time()

    def _send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a single message to Telegram with retry logic

        Args:
            text: Message text
            parse_mode: Parsing mode (Markdown or HTML)

        Returns:
            bool: True if sent successfully
        """
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram credentials not configured")
            return False

        self._rate_limit()

        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }

        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.post(
                    f"{self.api_url}/sendMessage",
                    json=payload,
                    timeout=10
                )

                if response.status_code == 200:
                    logger.info(f"Telegram message sent successfully (attempt {attempt + 1})")
                    return True
                else:
                    logger.warning(f"Telegram API error: {response.status_code} - {response.text}")

            except requests.exceptions.RequestException as e:
                logger.error(f"Telegram send error (attempt {attempt + 1}): {e}")

            if attempt < self.MAX_RETRIES - 1:
                delay = self.RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                time.sleep(delay)

        logger.error("Failed to send Telegram message after all retries")
        return False

    def _split_message(self, text: str) -> List[str]:
        """
        Split long messages into chunks that fit Telegram's limit

        Args:
            text: Message text to split

        Returns:
            List of message chunks
        """
        if len(text) <= self.MAX_MESSAGE_LENGTH:
            return [text]

        chunks = []
        lines = text.split('\n')
        current_chunk = ""

        for line in lines:
            if len(current_chunk) + len(line) + 1 <= self.MAX_MESSAGE_LENGTH:
                current_chunk += line + '\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = line + '\n'

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _format_digest(self, digest: Dict[str, Any]) -> str:
        """
        Format digest for Telegram display

        Args:
            digest: Digest dictionary

        Returns:
            Formatted message string
        """
        digest_type = digest.get('type', 'unknown').upper()
        generated_at = digest.get('generated_at', datetime.now())
        news_items = digest.get('news_items', [])

        # Select emoji based on digest type
        emoji_map = {
            'MORNING': '🌅',
            'EVENING': '🌆',
            'EVENT': '⚡'
        }
        emoji = emoji_map.get(digest_type, '📰')

        # Build message header
        message = f"{emoji} *{digest_type} DIGEST* - Magic Bricks Daily Brief\n"
        message += f"📅 {generated_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

        # Group by category
        categories = {}
        for item in news_items:
            category = item.get('category', 'uncategorized')
            if category not in categories:
                categories[category] = []
            categories[category].append(item)

        # Category emoji mapping
        category_emojis = {
            'real_estate': '🏢',
            'infrastructure': '🏗️',
            'policy': '📋',
            'celebrity': '⭐',
            'competitor': '🎯',
            'uncategorized': '📰'
        }

        # Format each category
        for category, items in categories.items():
            emoji_cat = category_emojis.get(category, '📰')
            message += f"{emoji_cat} *{category.replace('_', ' ').upper()}* ({len(items)})\n"

            for item in items[:5]:  # Limit to 5 items per category
                title = item.get('title', 'No title')
                source = item.get('source', 'Unknown')
                impact = item.get('impact_level', 'LOW')

                # Truncate long titles
                if len(title) > 80:
                    title = title[:77] + "..."

                impact_icon = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(impact, '⚪')
                message += f"• {title}\n"
                message += f"  └ {source} {impact_icon}\n"

            message += "\n"

        message += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        message += "📧 Full details in email digest"

        return message

    def _format_alert(self, news: Dict[str, Any]) -> str:
        """
        Format high-priority alert for Telegram

        Args:
            news: ProcessedNews dictionary

        Returns:
            Formatted alert message
        """
        score = news.get('signal_score', 0)
        impact = news.get('impact_level', 'LOW')
        discover = news.get('discover_potential', 0)
        title = news.get('title', 'No title')
        url = news.get('url', '')
        keywords = news.get('keywords', [])
        celebrity = news.get('celebrity_match')
        verified = news.get('verified', False)

        message = f"🚨 *HIGH-IMPACT ALERT* (Score: {score}/10)\n\n"
        message += f"*{title}*\n\n"
        message += f"📊 IMPACT: {impact} | DISCOVER: {discover}%\n\n"

        if celebrity:
            message += f"⭐ Celebrity: {celebrity}\n\n"

        # Extract keyword strings if they're dictionaries
        if keywords:
            kw_list = []
            for kw in keywords[:5]:  # Limit to 5 keywords
                if isinstance(kw, dict):
                    kw_list.append(kw.get('keyword', str(kw)))
                else:
                    kw_list.append(str(kw))
            message += f"🎯 Keywords: {', '.join(kw_list)}\n\n"

        verification = "✅ Verified" if verified else "⚠️ Unverified"
        message += f"{verification}\n\n"

        if url:
            message += f"🔗 [Read More]({url})"

        return message

    def send(self, digest: Dict[str, Any]) -> bool:
        """
        Send a digest to Telegram

        Args:
            digest: Digest dictionary

        Returns:
            bool: True if sent successfully
        """
        try:
            message = self._format_digest(digest)
            chunks = self._split_message(message)

            success = True
            for i, chunk in enumerate(chunks):
                if i > 0:
                    chunk = f"*[Continued {i+1}/{len(chunks)}]*\n\n" + chunk

                if not self._send_message(chunk):
                    success = False
                    break

            return success

        except Exception as e:
            logger.error(f"Error sending Telegram digest: {e}")
            raise NotificationError(f"Failed to send Telegram digest", e)

    def send_alert(self, news: Dict[str, Any]) -> bool:
        """
        Send a single high-priority alert to Telegram

        Args:
            news: ProcessedNews dictionary

        Returns:
            bool: True if sent successfully
        """
        try:
            message = self._format_alert(news)
            return self._send_message(message)

        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
            raise NotificationError(f"Failed to send Telegram alert", e)

    def health_check(self) -> bool:
        """
        Check if Telegram Bot API is accessible

        Returns:
            bool: True if service is healthy
        """
        if not self.bot_token:
            logger.error("Telegram bot token not configured")
            return False

        try:
            response = requests.get(
                f"{self.api_url}/getMe",
                timeout=5
            )

            if response.status_code == 200:
                bot_info = response.json()
                logger.info(f"Telegram health check passed: {bot_info.get('result', {}).get('username')}")
                return True
            else:
                logger.warning(f"Telegram health check failed: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Telegram health check error: {e}")
            return False
