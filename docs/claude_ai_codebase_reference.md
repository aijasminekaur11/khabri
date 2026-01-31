# Codebase Reference for Claude.ai Project

This document provides a condensed reference of the codebase structure for upload to Claude.ai.

## Directory Structure

```
News_Update/
├── src/
│   ├── config/
│   │   ├── config_loader.py      # YAML config loading
│   │   ├── config_validator.py   # Schema validation
│   │   └── config_manager.py     # Unified config access
│   ├── scrapers/
│   │   ├── news_scraper.py       # Website scraping
│   │   ├── rss_reader.py         # RSS feed parsing
│   │   ├── competitor_tracker.py # Competitor monitoring
│   │   └── igrs_scraper.py       # Property registration data
│   ├── processors/
│   │   ├── processor_pipeline.py # Main processing flow
│   │   ├── categorizer.py        # Article categorization
│   │   ├── summarizer.py         # Text summarization
│   │   ├── deduplicator.py       # Duplicate removal
│   │   └── celebrity_matcher.py  # Celebrity detection
│   ├── notifiers/
│   │   ├── base_notifier.py      # Abstract base class
│   │   ├── telegram_notifier.py  # Telegram Bot API
│   │   ├── email_notifier.py     # SMTP email
│   │   └── keyword_engine.py     # Keyword filtering
│   └── orchestrator/
│       ├── orchestrator.py       # Main coordinator
│       └── event_scheduler.py    # Task scheduling
├── testing/
│   ├── test_cases/
│   │   ├── unit/                 # Unit tests
│   │   ├── integration/          # Integration tests
│   │   ├── e2e/                  # End-to-end tests
│   │   └── smoke/                # Smoke tests
│   ├── fixtures/                 # Test data
│   └── reports/                  # Test reports
├── docs/
│   ├── BLUEPRINT.md              # Full architecture
│   ├── FEATURE_SUMMARY.md        # Features & workflows
│   └── contracts/                # Interface specs
├── logs/                         # CLI logs
└── config.yaml                   # Main configuration
```

## Key Interfaces

### 1. Config Manager Interface

```python
from src.config import ConfigManager

config = ConfigManager()
config.load("config.yaml")

# Access settings
telegram_token = config.get("notifications.telegram.token")
sources = config.get("sources.news")
keywords = config.get("keywords.priority")
```

### 2. Scraper Interface

```python
from src.scrapers import NewsScraper, RSSReader

# All scrapers follow this pattern
scraper = NewsScraper(config)
articles = await scraper.fetch()

# Returns list of Article objects
for article in articles:
    print(article.title, article.source, article.url)
```

### 3. Processor Pipeline

```python
from src.processors import ProcessorPipeline

pipeline = ProcessorPipeline(config)

# Process articles through the pipeline
processed = await pipeline.process(articles)
# Applies: categorization → summarization → deduplication → keyword matching
```

### 4. Notifier Interface

```python
from src.notifiers import TelegramNotifier, EmailNotifier

# All notifiers inherit from BaseNotifier
telegram = TelegramNotifier(config)
email = EmailNotifier(config)

# Send alert
await telegram.send_alert(article, priority="high")

# Send digest
await email.send_digest(articles, digest_type="morning")
```

### 5. Orchestrator

```python
from src.orchestrator import Orchestrator

orchestrator = Orchestrator(config)

# Run morning digest workflow
await orchestrator.run_morning_digest()

# Run real-time monitoring
await orchestrator.run_realtime_monitor()

# Schedule event-based scraping
orchestrator.schedule_event("budget_2026", datetime(2026, 2, 1, 11, 0))
```

## Data Models

### Article

```python
@dataclass
class Article:
    id: str                    # Unique identifier
    title: str                 # Article headline
    content: str               # Full text
    summary: str               # AI-generated summary
    source: str                # Source name
    url: str                   # Original URL
    published_at: datetime     # Publication time
    scraped_at: datetime       # Scrape time
    category: str              # Assigned category
    keywords: List[str]        # Matched keywords
    celebrities: List[str]     # Detected celebrities
    priority: int              # 1-10 priority score
    metadata: Dict             # Additional data
```

### Notification

```python
@dataclass
class Notification:
    type: str                  # "alert" or "digest"
    articles: List[Article]    # Articles to send
    recipients: List[str]      # Telegram IDs or emails
    priority: str              # "high", "medium", "low"
    template: str              # Template name
    scheduled_at: datetime     # When to send
```

## Configuration Schema

```yaml
# config.yaml structure
notifications:
  telegram:
    enabled: true
    bot_token: "BOT_TOKEN"
    chat_ids: ["123456789"]
    templates:
      alert: "templates/telegram_alert.txt"
      digest: "templates/telegram_digest.txt"

  email:
    enabled: true
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    sender: "alerts@example.com"
    recipients: ["user@example.com"]

sources:
  news:
    - name: "economic_times"
      url: "https://economictimes.com/..."
      selector: "article.story"
      frequency: "15m"
    - name: "livemint"
      url: "https://livemint.com/..."
      selector: "div.article"
      frequency: "30m"

  rss:
    - name: "pib_housing"
      url: "https://pib.gov.in/rss..."
      frequency: "1h"

  competitors:
    - name: "99acres"
      url: "https://99acres.com/..."
      alert_on_publish: true

keywords:
  priority:
    - "PMAY"
    - "RBI"
    - "home loan"
    - "metro"

  categories:
    market_updates: ["price", "trend", "index"]
    policy: ["RERA", "stamp duty", "GST"]
    infrastructure: ["metro", "airport", "highway"]

celebrities:
  - "Shah Rukh Khan"
  - "Virat Kohli"
  - "Amitabh Bachchan"

schedule:
  morning_digest: "07:00"
  evening_update: "16:00"

events:
  - name: "union_budget"
    date: "2026-02-01"
    start_time: "11:00"
    frequency: "15m"
```

## Testing Patterns

### Unit Test Example

```python
# testing/test_cases/unit/test_news_scraper.py
import pytest
from unittest.mock import AsyncMock, patch
from src.scrapers import NewsScraper

@pytest.fixture
def mock_config():
    return {"sources": {"news": [...]}}

@pytest.fixture
def scraper(mock_config):
    return NewsScraper(mock_config)

@pytest.mark.asyncio
async def test_fetch_articles(scraper):
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value.text = AsyncMock(
            return_value="<html>...</html>"
        )
        articles = await scraper.fetch()
        assert len(articles) > 0
```

### Integration Test Example

```python
# testing/test_cases/integration/test_pipeline.py
@pytest.mark.asyncio
async def test_full_pipeline_flow():
    config = ConfigManager()
    config.load("testing/fixtures/test_config.yaml")

    # Scrape → Process → Notify
    scraper = NewsScraper(config)
    pipeline = ProcessorPipeline(config)
    notifier = TelegramNotifier(config)

    articles = await scraper.fetch()
    processed = await pipeline.process(articles)
    result = await notifier.send_digest(processed)

    assert result.success
```

## Error Handling

```python
# All modules use custom exceptions
from src.exceptions import (
    ConfigError,        # Config loading/validation errors
    ScraperError,       # Scraping failures
    ProcessorError,     # Processing failures
    NotificationError,  # Notification delivery failures
)

try:
    await scraper.fetch()
except ScraperError as e:
    logger.error(f"Scraping failed: {e}")
    # System continues with cached data
```

## Logging

```python
import logging

# Each module has its own logger
logger = logging.getLogger(__name__)

# Log levels used:
# DEBUG: Detailed debugging info
# INFO: Normal operation events
# WARNING: Recoverable issues
# ERROR: Failures requiring attention
# CRITICAL: System-breaking issues
```

## Environment Variables

```bash
# Required in .env file
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
EMAIL_RECIPIENT=recipient@example.com
```

---

## Quick Reference Commands

```bash
# Run all tests
pytest testing/ -v

# Run with coverage
pytest testing/ --cov=src --cov-report=html

# Run specific test layer
pytest testing/test_cases/unit/ -v
pytest testing/test_cases/integration/ -v

# Run the system
python -m src.orchestrator.orchestrator

# Validate config
python -m src.config.config_validator config.yaml
```
