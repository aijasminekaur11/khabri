# Claude.ai Project Instructions
# Copy everything below the line into your Claude.ai Project Instructions

---

## Project Overview

You are assisting with the **Magic Bricks News Intelligence System** - a Python-based real estate news aggregation and notification platform.

## System Architecture

### Core Components

1. **Config Module** (`src/config/`)
   - `config_loader.py` - Loads YAML configuration
   - `config_validator.py` - Validates config against schema
   - `config_manager.py` - Unified config access interface

2. **Scrapers** (`src/scrapers/`)
   - `news_scraper.py` - Scrapes real estate news from websites
   - `rss_reader.py` - Reads RSS feeds
   - `competitor_tracker.py` - Monitors competitor updates
   - `igrs_scraper.py` - Scrapes IGRS (property registration) data

3. **Processors** (`src/processors/`)
   - `processor_pipeline.py` - Main processing pipeline
   - `categorizer.py` - Categorizes news articles
   - `summarizer.py` - Generates article summaries
   - `deduplicator.py` - Removes duplicate content
   - `celebrity_matcher.py` - Identifies celebrity mentions

4. **Notifiers** (`src/notifiers/`)
   - `telegram_notifier.py` - Sends Telegram alerts
   - `email_notifier.py` - Sends email digests
   - `keyword_engine.py` - Keyword matching and filtering

5. **Orchestrator** (`src/orchestrator/`)
   - `orchestrator.py` - Main workflow coordinator
   - `event_scheduler.py` - Schedules tasks and events

## Technology Stack

- **Language**: Python 3.10+
- **Testing**: pytest with 90%+ coverage
- **Config**: YAML-based configuration
- **Notifications**: Telegram Bot API, SMTP Email
- **Data Processing**: BeautifulSoup, feedparser

## Project Conventions

### File Organization
- Production code: `src/` directory only
- All tests: `testing/` directory
- Documentation: `docs/` directory
- Logs: `logs/` directory

### Testing Standards
- Every feature requires unit + integration tests
- Use mocks for external APIs
- Fixtures stored in `testing/fixtures/`

### Code Style
- Prefer clarity over cleverness
- Keep functions small and single-purpose
- Document complex logic only
- Follow PEP 8 guidelines

## Key Data Structures

### Article Object
```python
{
    "id": "unique-article-id",
    "title": "Article Title",
    "content": "Full article content",
    "summary": "AI-generated summary",
    "source": "source_name",
    "url": "https://...",
    "published_at": "2026-01-31T10:00:00Z",
    "category": "market_updates|policy|launches|...",
    "keywords": ["keyword1", "keyword2"],
    "celebrities": ["name1", "name2"]
}
```

### Notification Payload
```python
{
    "type": "alert|digest",
    "articles": [...],
    "recipients": ["telegram_chat_id", "email@example.com"],
    "priority": "high|medium|low"
}
```

## Common Tasks

When asked to:

1. **Add a new scraper**: Create in `src/scrapers/`, follow `news_scraper.py` pattern, add tests in `testing/test_cases/unit/`

2. **Add notification channel**: Extend `base_notifier.py`, create new notifier in `src/notifiers/`

3. **Modify processing logic**: Update relevant processor in `src/processors/`, ensure pipeline integration

4. **Debug issues**: Check `logs/` for CLI-specific logs, review `testing/issues/` for known issues

5. **Add configuration options**: Update schema in `docs/contracts/config_schema.md`, implement in `config_manager.py`

## Important Files to Reference

- `docs/BLUEPRINT.md` - Full technical documentation
- `docs/FEATURE_SUMMARY.md` - Feature list and workflows
- `docs/project_state.json` - Current project state
- `docs/contracts/` - Interface contracts

## Response Guidelines

1. Always consider the existing architecture before suggesting changes
2. Maintain test coverage - suggest tests for any new code
3. Follow the established patterns in the codebase
4. Keep changes minimal and focused
5. Reference specific files when discussing code
