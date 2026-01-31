# Notifier Interface Contract

**Owner**: CLI 1 (Core Builder)
**Implementer**: CLI 3 (Notifier Builder)
**Version**: 1.0.0

---

## Overview

This contract defines the interface that all notifiers must implement.

---

## Base Interface

```python
from abc import ABC, abstractmethod
from typing import List
from src.processors.models import ProcessedNews, Digest

class BaseNotifier(ABC):
    """Abstract base class for all notifiers."""

    @abstractmethod
    def send(self, digest: Digest) -> bool:
        """
        Send a digest to the recipient.

        Args:
            digest: The Digest object to send

        Returns:
            bool: True if sent successfully, False otherwise
        """
        pass

    @abstractmethod
    def send_alert(self, news: ProcessedNews) -> bool:
        """
        Send a single high-priority alert.

        Args:
            news: The ProcessedNews item to alert

        Returns:
            bool: True if sent successfully, False otherwise
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the notifier service is available.

        Returns:
            bool: True if service is healthy, False otherwise
        """
        pass
```

---

## Telegram Notifier

```python
class TelegramNotifier(BaseNotifier):
    """
    Implementation requirements:
    - Use python-telegram-bot library
    - Respect 4096 char message limit
    - Support markdown formatting
    - Handle rate limiting (30 msgs/sec)
    """

    def __init__(self, bot_token: str, chat_id: str):
        pass

    def send(self, digest: Digest) -> bool:
        # Format digest for Telegram
        # Split if > 4096 chars
        # Send with retry logic
        pass

    def send_alert(self, news: ProcessedNews) -> bool:
        # Format single alert
        # Include: score, impact, keywords, social hooks
        pass

    def health_check(self) -> bool:
        # Call getMe API
        pass
```

---

## Email Notifier

```python
class EmailNotifier(BaseNotifier):
    """
    Implementation requirements:
    - Use smtplib with Gmail SMTP
    - Support HTML email with templates
    - Support attachments (optional)
    - Handle connection pooling
    """

    def __init__(self, smtp_server: str, username: str, password: str, recipient: str):
        pass

    def send(self, digest: Digest) -> bool:
        # Render HTML template
        # Include all sections
        # Send via SMTP
        pass

    def send_alert(self, news: ProcessedNews) -> bool:
        # Render alert template
        # Send immediately
        pass

    def health_check(self) -> bool:
        # Test SMTP connection
        pass
```

---

## Keyword Engine

```python
class KeywordEngine:
    """
    NOT a notifier, but provides data TO notifiers.

    Implementation requirements:
    - Use pytrends for Google Trends
    - Cache results (15 min TTL)
    - Handle rate limiting
    """

    def get_trending_keywords(self, topic: str) -> List[KeywordData]:
        # Query Google Trends
        # Return top 5 related keywords
        pass

    def get_seo_suggestions(self, news: ProcessedNews) -> List[KeywordData]:
        # Analyze news content
        # Suggest primary, secondary, long-tail
        pass

    def calculate_discover_potential(self, news: ProcessedNews) -> int:
        # Score 0-100 based on:
        # - Celebrity name in title
        # - Trending topic
        # - Visual content
        # - Fresh news
        pass
```

---

## Message Templates

### Telegram Digest Template

```
{emoji} {DIGEST_TYPE} - Magic Bricks Daily Brief
📅 {date}

━━━━━━━━━━━━━━━━━━━━━━

{for each category}
{category_emoji} {CATEGORY_NAME} ({count})
{for each item}
• {headline}
  └ {source}
{end for}
{end for}

━━━━━━━━━━━━━━━━━━━━━━

📧 Full details in email
```

### Telegram Alert Template

```
🚨 HIGH-IMPACT ALERT (Score: {score}/10)

{headline}

📊 IMPACT: {impact} | DISCOVER: {discover}%

🧠 Why: {why_it_matters}

✍️ Idea: {content_idea}

🎯 Keywords: {keywords}

✅ {verification_status}
```

---

## Error Handling

All notifiers must:
1. Catch and log all exceptions
2. Return `False` on failure (don't raise)
3. Implement retry with exponential backoff
4. Fall back gracefully (email if Telegram fails)

---

## Configuration

Notifiers read credentials from environment:

```
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
GMAIL_ADDRESS
GMAIL_APP_PASSWORD
RECIPIENT_EMAIL
```

---

**Contract Status**: PUBLISHED ✅

## Implementation Guidelines for CLI 3

The notifier interface contract is now finalized. CLI 3 (Notifier Builder) should implement:

1. **TelegramNotifier** - Following the exact interface specified above
2. **EmailNotifier** - Following the exact interface specified above
3. **KeywordEngine** - For SEO keyword generation

All notifiers must:
- Implement the BaseNotifier abstract class
- Handle errors gracefully without raising exceptions
- Return boolean success/failure status
- Support both digest and alert modes

**Published by**: CLI 1 (Core Builder)
**Date**: 2026-01-30
**Status**: Ready for implementation by CLI 3
