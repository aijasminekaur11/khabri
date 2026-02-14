"""
Telegram Notifier
Sends notifications via Telegram Bot API
"""

import os
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import pytz
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
    - Display times in IST timezone
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
            chat_id: Telegram chat ID(s) - comma-separated (defaults to env TELEGRAM_CHAT_ID)
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id_str = chat_id or os.getenv('TELEGRAM_CHAT_ID', '')

        # Support multiple chat IDs (comma-separated)
        self.chat_ids = [cid.strip() for cid in chat_id_str.split(',') if cid.strip()]

        # Keep backward compatibility with single chat_id
        self.chat_id = self.chat_ids[0] if self.chat_ids else None

        if not self.bot_token or not self.chat_ids:
            logger.warning("Telegram credentials not configured. Notifier will not function.")

        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.last_send_time = 0
        
        # IST timezone for proper time display
        self.ist_timezone = pytz.timezone('Asia/Kolkata')

    def _rate_limit(self):
        """Enforce rate limiting between messages"""
        elapsed = time.time() - self.last_send_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_send_time = time.time()

    def _convert_to_ist(self, dt: datetime) -> datetime:
        """
        Convert datetime to IST timezone.
        
        Args:
            dt: datetime object (timezone-aware or naive)
            
        Returns:
            datetime object in IST timezone
        """
        if dt is None:
            return datetime.now(self.ist_timezone)
        
        # If naive, assume UTC
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        
        # Convert to IST
        return dt.astimezone(self.ist_timezone)

    def _send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a single message to all configured Telegram chats with retry logic

        Args:
            text: Message text
            parse_mode: Parsing mode (Markdown or HTML)

        Returns:
            bool: True if sent successfully to at least one chat
        """
        if not self.bot_token or not self.chat_ids:
            logger.error("Telegram credentials not configured")
            return False

        self._rate_limit()

        success_count = 0

        for chat_id in self.chat_ids:
            payload = {
                'chat_id': chat_id,
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
                        logger.info(f"Telegram message sent to {chat_id} (attempt {attempt + 1})")
                        success_count += 1
                        break
                    else:
                        logger.warning(f"Telegram API error for {chat_id}: {response.status_code} - {response.text}")

                except requests.exceptions.RequestException as e:
                    logger.error(f"Telegram send error to {chat_id} (attempt {attempt + 1}): {e}")

                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                    time.sleep(delay)

            if success_count == 0 or (self.chat_ids.index(chat_id) == len(self.chat_ids) - 1 and success_count == 0):
                logger.error(f"Failed to send to {chat_id} after all retries")

        return success_count > 0

    def _split_message(self, text: str, max_length: int = 0) -> List[str]:
        """
        Split long messages into chunks that fit Telegram's limit

        Args:
            text: Message text to split
            max_length: Maximum chunk length (defaults to MAX_MESSAGE_LENGTH)

        Returns:
            List of message chunks
        """
        import textwrap

        limit = max_length or self.MAX_MESSAGE_LENGTH

        if len(text) <= limit:
            return [text]

        chunks = []
        lines = text.split('\n')
        current_chunk = ""

        for line in lines:
            # Handle single lines longer than limit
            if len(line) > limit:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                # Split the long line into word-boundary-aware segments
                segments = textwrap.wrap(line, width=limit,
                                        replace_whitespace=False, drop_whitespace=False)
                chunks.extend(segments if segments else [line[:limit]])
            elif len(current_chunk) + len(line) + 1 <= limit:
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
        Format digest for Telegram display with IST timezone

        Args:
            digest: Digest dictionary

        Returns:
            Formatted message string
        """
        digest_type = digest.get('type', 'unknown').upper()
        generated_at = digest.get('generated_at', datetime.now())
        
        # Convert to datetime if string
        if isinstance(generated_at, str):
            try:
                generated_at = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                generated_at = datetime.now()
        
        # Convert to IST for display
        generated_at_ist = self._convert_to_ist(generated_at)
        
        news_items = digest.get('news_items', [])

        # Select emoji based on digest type
        emoji_map = {
            'MORNING': '🌅',
            'EVENING': '🌆',
            'EVENT': '⚡'
        }
        emoji = emoji_map.get(digest_type, '📰')

        # Build message header with IST time
        message = f"{emoji} *{digest_type} DIGEST* - Magic Bricks Daily Brief\n"
        message += f"📅 {generated_at_ist.strftime('%Y-%m-%d %H:%M IST')}\n\n"
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

                # Escape Markdown special characters (backslash first)
                for ch in ('\\', '*', '_', '`', '[', ']'):
                    title = title.replace(ch, f'\\{ch}')
                    source = source.replace(ch, f'\\{ch}')

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

        # Escape Markdown special characters (backslash first)
        def _escape_md(text):
            for ch in ('\\', '*', '_', '`', '[', ']'):
                text = text.replace(ch, f'\\{ch}')
            return text

        title = _escape_md(title)

        message = f"🚨 *HIGH-IMPACT ALERT* (Score: {score}/10)\n\n"
        message += f"*{title}*\n\n"
        message += f"📊 IMPACT: {impact} | DISCOVER: {discover}%\n\n"

        if celebrity:
            message += f"⭐ Celebrity: {_escape_md(celebrity)}\n\n"

        # Extract keyword strings if they're dictionaries
        if keywords:
            kw_list = []
            for kw in keywords[:5]:  # Limit to 5 keywords
                if isinstance(kw, dict):
                    kw_list.append(_escape_md(kw.get('keyword', str(kw))))
                else:
                    kw_list.append(_escape_md(str(kw)))
            message += f"🎯 Keywords: {', '.join(kw_list)}\n\n"

        verification = "✅ Verified" if verified else "⚠️ Unverified"
        message += f"{verification}\n\n"

        if url:
            # Encode parentheses to prevent Markdown link breakage
            safe_url = url.replace('(', '%28').replace(')', '%29')
            message += f"🔗 [Read More]({safe_url})"

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

            # Two-pass split: first pass to estimate chunk count
            initial_chunks = self._split_message(message)
            num_chunks = len(initial_chunks)

            if num_chunks <= 1:
                return self._send_message(message) if message else True

            # Second pass: compute actual prefix length and re-split
            prefix_len = len(f"*[Continued {num_chunks}/{num_chunks}]*\n\n")
            chunks = self._split_message(message, max_length=self.MAX_MESSAGE_LENGTH - prefix_len)

            success = True
            for i, chunk in enumerate(chunks):
                if i > 0:
                    prefix = f"*[Continued {i+1}/{len(chunks)}]*\n\n"
                    chunk = prefix + chunk

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

            chunks = self._split_message(message)
            if len(chunks) <= 1:
                return self._send_message(message) if message else True

            success = True
            for chunk in chunks:
                if not self._send_message(chunk):
                    success = False
                    break

            return success

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
