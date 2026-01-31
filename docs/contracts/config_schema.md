# Config Schema Contract

**Owner**: CLI 1 (Core Builder)
**Consumers**: CLI 2, CLI 3, CLI 4
**Version**: 1.0.0

---

## Overview

This contract defines the configuration file schemas that all CLIs must use.

---

## Config Files

### 1. sources.json

```json
{
  "sources": [
    {
      "id": "string (unique)",
      "name": "string",
      "url": "string (valid URL)",
      "type": "scrape | rss | api",
      "category": "real_estate | infrastructure | policy | celebrity | competitor",
      "enabled": "boolean",
      "rate_limit_ms": "number (milliseconds between requests)",
      "selectors": {
        "title": "string (CSS selector)",
        "content": "string (CSS selector)",
        "date": "string (CSS selector)",
        "link": "string (CSS selector)"
      }
    }
  ]
}
```

### 2. keywords.json

```json
{
  "categories": {
    "category_name": {
      "primary": ["string"],
      "secondary": ["string"],
      "exclude": ["string"]
    }
  }
}
```

### 3. events.json

```json
{
  "events": [
    {
      "id": "string (unique)",
      "name": "string",
      "date": "YYYY-MM-DD",
      "start_time": "HH:MM",
      "end_time": "HH:MM",
      "timezone": "string (IANA timezone)",
      "interval_minutes": "number",
      "keywords": ["string"],
      "sources": ["string (source IDs)"],
      "active": "boolean"
    }
  ]
}
```

### 4. celebrities.json

```json
{
  "celebrities": [
    {
      "name": "string",
      "aliases": ["string"],
      "category": "bollywood | cricket | business | politics",
      "priority": "high | medium | low"
    }
  ]
}
```

### 5. schedules.json

```json
{
  "timezone": "string (IANA timezone)",
  "digests": {
    "morning": {
      "enabled": "boolean",
      "time": "HH:MM",
      "include": ["string (category names)"]
    },
    "evening": {
      "enabled": "boolean",
      "time": "HH:MM",
      "include": ["string (category names)"]
    }
  }
}
```

---

## Validation Rules

1. All IDs must be unique within their file
2. All URLs must be valid and accessible
3. All times must be in 24-hour format
4. All timezones must be valid IANA timezone strings
5. Boolean fields must be actual booleans, not strings

---

## Access Pattern

```python
from src.config import ConfigManager

config = ConfigManager()
sources = config.get_sources()
events = config.get_active_events()
```

---

**Contract Status**: PUBLISHED ✅

## Implementation Details

The configuration module has been implemented in `src/config/` with the following components:

- **ConfigManager**: Main interface for all configuration access
- **ConfigLoader**: Handles loading JSON files with caching
- **ConfigValidator**: Validates all configuration schemas

All methods defined in this contract are fully implemented and tested.

**Published by**: CLI 1 (Core Builder)
**Date**: 2026-01-30
**Status**: Ready for use by CLI 2, CLI 3, and CLI 4
