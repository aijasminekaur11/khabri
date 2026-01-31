# Event Payloads Contract

**Owner**: CLI 1 (Core Builder)
**Consumers**: CLI 2, CLI 3, CLI 4
**Version**: 1.0.0

---

## Overview

This contract defines the data structures passed between modules.

---

## Core Data Types

### NewsItem

```python
@dataclass
class NewsItem:
    id: str                    # Unique hash of URL
    title: str                 # Article title
    url: str                   # Source URL
    source: str                # Source name
    source_id: str             # Source ID from config
    category: str              # Category name
    content: str               # Article excerpt/content
    published_at: datetime     # Publication timestamp
    scraped_at: datetime       # When we fetched it

    # Optional fields
    author: Optional[str] = None
    image_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
```

### ProcessedNews

```python
@dataclass
class ProcessedNews(NewsItem):
    # Added by processor pipeline
    signal_score: int          # 1-10 importance score
    impact_level: str          # HIGH | MEDIUM | LOW
    discover_potential: int    # 0-100 percentage

    # Celebrity detection
    celebrity_match: Optional[str] = None
    celebrity_deal_amount: Optional[str] = None

    # SEO data
    keywords: List[KeywordData] = field(default_factory=list)

    # Verification
    verified: bool = False
    confidence: str = "LOW"    # HIGH | MEDIUM | LOW
    sources_checked: List[str] = field(default_factory=list)
```

### KeywordData

```python
@dataclass
class KeywordData:
    keyword: str
    search_volume: int
    difficulty: str            # HIGH | MEDIUM | LOW
    type: str                  # primary | secondary | long_tail
```

### CompetitorAlert

```python
@dataclass
class CompetitorAlert:
    competitor: str            # Competitor name
    article_url: str
    article_title: str
    published_at: datetime
    gaps: List[str]            # What they missed
    opportunity_window: int    # Minutes to beat them
```

### Digest

```python
@dataclass
class Digest:
    type: str                  # morning | evening | event
    generated_at: datetime
    news_items: List[ProcessedNews]
    competitor_alerts: List[CompetitorAlert]
    content_plan: Optional[ContentPlan] = None
```

### ContentPlan

```python
@dataclass
class ContentPlan:
    date: date
    priority_1: List[ContentIdea]
    priority_2: List[ContentIdea]
    quick_ideas: List[str]
    keyword_opportunities: List[KeywordData]
```

### ContentIdea

```python
@dataclass
class ContentIdea:
    headline: str
    angle: str
    keywords: List[str]
    source_news: str           # NewsItem ID
```

---

## Event Types (for internal messaging)

### SCRAPER_COMPLETE

```json
{
  "event": "SCRAPER_COMPLETE",
  "scraper": "news_scraper",
  "items_found": 15,
  "timestamp": "2026-01-30T07:00:00Z"
}
```

### PROCESSING_COMPLETE

```json
{
  "event": "PROCESSING_COMPLETE",
  "items_processed": 15,
  "high_priority": 3,
  "timestamp": "2026-01-30T07:01:00Z"
}
```

### NOTIFICATION_SENT

```json
{
  "event": "NOTIFICATION_SENT",
  "channel": "telegram | email",
  "recipient": "user_id",
  "digest_type": "morning | evening | event",
  "items_count": 10,
  "timestamp": "2026-01-30T07:02:00Z"
}
```

---

## Serialization

All data types must be JSON-serializable for:
- Logging
- State persistence
- API responses

Use `dataclasses_json` or manual `to_dict()` methods.

---

**Contract Status**: PUBLISHED ✅

## Implementation Notes

The event payload structures defined in this contract are implemented in `src/processors/` module:

- **NewsItem**: Dictionary-based structure processed by ProcessorPipeline
- **ProcessedNews**: Enhanced with categorization, celebrity matching, and summarization
- **Deduplication**: Handled by Deduplicator class
- **Categorization**: Handled by Categorizer class
- **Celebrity Matching**: Handled by CelebrityMatcher class
- **Summarization**: Handled by Summarizer class

All processors add their respective fields to news items as they flow through the pipeline.

**Published by**: CLI 1 (Core Builder)
**Date**: 2026-01-30
**Status**: Ready for use by CLI 2, CLI 3, and CLI 4
