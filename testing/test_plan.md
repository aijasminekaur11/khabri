# 🧪 MAGIC BRICKS NEWS INTELLIGENCE SYSTEM
## COMPREHENSIVE TEST PLAN
### Version 1.0 | January 2026

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Testing Objectives](#2-testing-objectives)
3. [Test Strategy](#3-test-strategy)
4. [Test Environment](#4-test-environment)
5. [Test Automation Framework](#5-test-automation-framework)
6. [Unit Tests](#6-unit-tests)
7. [Integration Tests](#7-integration-tests)
8. [End-to-End Tests](#8-end-to-end-tests)
9. [Performance Tests](#9-performance-tests)
10. [Security Tests](#10-security-tests)
11. [Test Data Management](#11-test-data-management)
12. [CI/CD Integration](#12-cicd-integration)
13. [Issue Management](#13-issue-management)
14. [Test Execution Schedule](#14-test-execution-schedule)
15. [Success Criteria](#15-success-criteria)

---

# 1. EXECUTIVE SUMMARY

## 1.1 Purpose

This test plan defines the **complete automated testing strategy** for the Magic Bricks News Intelligence System. The testing is designed to be **fully autonomous** - executable by Claude Code CLI without human intervention.

## 1.2 Scope

### In Scope
- ✅ Unit testing (all components)
- ✅ Integration testing (component interactions)
- ✅ End-to-end testing (user workflows)
- ✅ Performance testing (load, stress)
- ✅ Security testing (API keys, injection)
- ✅ Smoke testing (pre-commit checks)
- ✅ Health monitoring (external services)
- ✅ Automated issue generation
- ✅ Self-healing mechanisms

### Out of Scope
- ❌ Manual testing
- ❌ User acceptance testing (UAT)
- ❌ Browser-based UI testing (no UI exists)

## 1.3 Testing Philosophy

**"Test Everything. Automate Everything. Fix Everything."**

- Tests run autonomously without human intervention
- Failed tests generate detailed issue files automatically
- Another Claude CLI session can pick up issues and fix them
- System self-heals using retry logic and fallbacks
- All test results logged with full traceability

---

# 2. TESTING OBJECTIVES

## 2.1 Primary Objectives

| Objective | Target | Rationale |
|-----------|--------|-----------|
| **Code Coverage** | 90%+ | Ensure most code paths tested |
| **Test Reliability** | 99%+ pass rate | Minimize flaky tests |
| **Execution Speed** | <30 min full suite | Enable frequent testing |
| **Issue Detection** | 100% failures logged | No silent failures |
| **Auto-Fix Rate** | 80%+ | Self-healing capability |

## 2.2 Quality Gates

Tests must verify:

1. **Functional Correctness**
   - All scrapers retrieve data correctly
   - All processors transform data correctly
   - All notifiers send messages correctly

2. **Data Integrity**
   - No duplicate news items
   - Celebrity matches are accurate
   - Categorization is correct

3. **Reliability**
   - System handles API failures gracefully
   - Retry mechanisms work correctly
   - Fallback sources activate properly

4. **Performance**
   - Scrapers complete within timeout
   - Notifications sent within 5 seconds
   - Memory usage stays below 512MB

5. **Security**
   - API keys never logged
   - No SQL/command injection vulnerabilities
   - HTTPS enforced for all external calls

---

# 3. TEST STRATEGY

## 3.1 Testing Pyramid

```
                    ▲
                   / \
                  /   \
                 /  E2E \ ────────── 20% (Slow, Few)
                /_______\
               /         \
              /Integration\ ──────── 30% (Medium, Some)
             /____________\
            /              \
           /   Unit Tests   \ ────── 50% (Fast, Many)
          /__________________\
```

## 3.2 Test Levels

### Level 1: Unit Tests (50% of total tests)
- **Target**: Individual functions and classes
- **Duration**: <30 seconds
- **Frequency**: Every commit
- **Tools**: pytest, pytest-mock
- **Coverage Target**: 95%

### Level 2: Integration Tests (30% of total tests)
- **Target**: Component interactions
- **Duration**: 3-5 minutes
- **Frequency**: Every PR
- **Tools**: pytest, fixtures
- **Coverage Target**: 85%

### Level 3: E2E Tests (20% of total tests)
- **Target**: Complete workflows
- **Duration**: 20-30 minutes
- **Frequency**: Daily
- **Tools**: pytest, real configs
- **Coverage Target**: All user journeys

## 3.3 Mock vs Real Testing

### Default: MOCK EVERYTHING

| Component | Mock Strategy |
|-----------|---------------|
| **News Websites** | Mock HTTP responses with fixtures |
| **IGRS Portals** | Mock with sample property data |
| **Telegram API** | Mock send_message() calls |
| **Email (Gmail)** | Mock SMTP connections |
| **RSS Feeds** | Mock with sample XML |

### Weekly Real Checks (Sandbox Mode)

| Component | Real Test Strategy |
|-----------|-------------------|
| **News Websites** | Scrape 1 article, validate structure |
| **IGRS Portals** | Check portal availability only |
| **Telegram API** | Send to test bot (not production) |
| **Email** | Send to test email account |

---

# 4. TEST ENVIRONMENT

## 4.1 Environment Configuration

### Development Environment
```
Location: D:\Jasmine\00001_Content_app\News_Update
Python: 3.9+
pytest: 7.4+
OS: Windows/Linux/macOS
```

### Test Modes

| Mode | Description | Trigger |
|------|-------------|---------|
| **LOCAL** | Developer's machine | Manual `pytest` |
| **CI** | GitHub Actions | On push/PR |
| **SANDBOX** | Isolated test env | Weekly schedule |
| **PRODUCTION** | Dry-run only | Pre-deployment |

## 4.2 Test Secrets Management

```bash
# GitHub Secrets (for CI)
TELEGRAM_BOT_TOKEN_TEST=<test_bot_token>
TELEGRAM_CHAT_ID_TEST=<test_chat_id>
GMAIL_ADDRESS_TEST=<test_email>
GMAIL_APP_PASSWORD_TEST=<test_password>
TEST_MODE=true
```

## 4.3 Test Database

```
testing/fixtures/
├── test_news.json          # Sample news articles
├── test_celebrities.json   # Sample celebrity data
├── test_igrs.json          # Sample property deals
├── test_sources.json       # Sample source configs
└── test_events.json        # Sample event configs
```

---

# 5. TEST AUTOMATION FRAMEWORK

## 5.1 Framework Architecture

```
testing/
├── conftest.py             # Shared fixtures & config
├── pytest.ini              # Pytest configuration
├── requirements-test.txt   # Testing dependencies
├── test_cases/
│   ├── unit/
│   │   ├── test_scrapers.py
│   │   ├── test_processors.py
│   │   └── test_notifiers.py
│   ├── integration/
│   │   ├── test_pipeline.py
│   │   ├── test_config_reload.py
│   │   └── test_scheduling.py
│   ├── e2e/
│   │   ├── test_morning_digest.py
│   │   ├── test_event_alerts.py
│   │   └── test_user_workflows.py
│   └── smoke/
│       └── test_smoke.py
├── fixtures/
│   ├── mock_responses.py
│   ├── test_data.py
│   └── sample_configs/
├── debug_logs/             # Auto-generated logs
├── issues/                 # Auto-generated issue files
└── sandbox/                # Experimental tests
```

## 5.2 Testing Tools Stack

### Core Framework
```bash
pytest==7.4.3               # Test framework
pytest-cov==4.1.0           # Coverage reporting
pytest-mock==3.12.0         # Mocking support
pytest-asyncio==0.21.1      # Async testing
pytest-timeout==2.2.0       # Timeout handling
pytest-retry==1.6.0         # Retry flaky tests
pytest-xdist==3.5.0         # Parallel execution
```

### Additional Tools
```bash
responses==0.24.0           # Mock HTTP responses
freezegun==1.4.0            # Mock datetime
faker==20.1.0               # Generate test data
coverage==7.3.2             # Code coverage
```

## 5.3 Pytest Configuration

```ini
# pytest.ini
[pytest]
testpaths = testing/test_cases
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --verbose
    --strict-markers
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=90
    --maxfail=5
    --timeout=300
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    smoke: Smoke tests
    slow: Slow running tests
    real: Tests using real external services
    security: Security tests
```

---

# 6. UNIT TESTS

## 6.1 Scraper Tests

### 6.1.1 News Scraper Tests

**File**: `testing/test_cases/unit/test_news_scraper.py`

| Test Case ID | Test Name | Description | Expected Result |
|--------------|-----------|-------------|-----------------|
| NS-UT-001 | `test_scrape_economic_times_success` | Scrape ET with valid response | Returns list of NewsItem objects |
| NS-UT-002 | `test_scrape_livemint_success` | Scrape Mint with valid response | Returns list of NewsItem objects |
| NS-UT-003 | `test_scrape_with_network_error` | Network timeout during scrape | Raises NetworkError exception |
| NS-UT-004 | `test_scrape_with_invalid_html` | Malformed HTML response | Returns empty list gracefully |
| NS-UT-005 | `test_scrape_with_rate_limit` | Rate limit exceeded (429) | Triggers retry with backoff |
| NS-UT-006 | `test_scrape_with_empty_page` | Page returns no articles | Returns empty list |
| NS-UT-007 | `test_extract_title_correctly` | Extract article title | Title extracted correctly |
| NS-UT-008 | `test_extract_date_correctly` | Extract publish date | Date parsed correctly |
| NS-UT-009 | `test_extract_url_correctly` | Extract article URL | URL normalized correctly |
| NS-UT-010 | `test_scrape_competitor_housing` | Scrape Housing.com | Competitor tagged correctly |

### 6.1.2 IGRS Scraper Tests

**File**: `testing/test_cases/unit/test_igrs_scraper.py`

| Test Case ID | Test Name | Description | Expected Result |
|--------------|-----------|-------------|-----------------|
| IS-UT-001 | `test_search_maharashtra_igr_success` | Search MH IGR portal | Returns property deals |
| IS-UT-002 | `test_search_delhi_revenue_success` | Search Delhi portal | Returns property deals |
| IS-UT-003 | `test_search_celebrity_name` | Search "Virat Kohli" | Finds matching deals |
| IS-UT-004 | `test_search_high_value_deals` | Search deals >₹5Cr | Filters by amount |
| IS-UT-005 | `test_extract_stamp_duty` | Extract stamp duty amount | Amount parsed correctly |
| IS-UT-006 | `test_extract_property_area` | Extract area in sq ft | Area extracted correctly |
| IS-UT-007 | `test_extract_document_number` | Extract doc registration number | Document ID correct |
| IS-UT-008 | `test_portal_unavailable` | Portal returns 503 | Graceful fallback |
| IS-UT-009 | `test_invalid_search_query` | Search with special chars | Sanitizes input correctly |
| IS-UT-010 | `test_pagination_handling` | Multiple pages of results | Paginates correctly |

### 6.1.3 RSS Reader Tests

**File**: `testing/test_cases/unit/test_rss_reader.py`

| Test Case ID | Test Name | Description | Expected Result |
|--------------|-----------|-------------|-----------------|
| RS-UT-001 | `test_parse_valid_rss_feed` | Parse valid RSS XML | Returns list of items |
| RS-UT-002 | `test_parse_atom_feed` | Parse Atom format feed | Returns list of items |
| RS-UT-003 | `test_parse_pib_feed` | Parse PIB RSS feed | Extracts ministry name |
| RS-UT-004 | `test_parse_rbi_feed` | Parse RBI announcements | Extracts policy info |
| RS-UT-005 | `test_invalid_xml_format` | Malformed XML feed | Returns empty list |
| RS-UT-006 | `test_feed_with_missing_fields` | Feed missing required fields | Uses default values |
| RS-UT-007 | `test_filter_by_keywords` | Filter by "PMAY" keyword | Returns matching items only |
| RS-UT-008 | `test_feed_timeout` | Feed takes >10 seconds | Timeout error raised |
| RS-UT-009 | `test_feed_caching` | Cached feed not expired | Returns cached data |
| RS-UT-010 | `test_feed_etag_handling` | Feed uses ETag headers | Respects 304 Not Modified |

## 6.2 Processor Tests

### 6.2.1 Deduplicator Tests

**File**: `testing/test_cases/unit/test_deduplicator.py`

| Test Case ID | Test Name | Description | Expected Result |
|--------------|-----------|-------------|-----------------|
| DD-UT-001 | `test_detect_exact_duplicate` | Same title, same URL | Marked as duplicate |
| DD-UT-002 | `test_detect_similar_title` | 85% title similarity | Marked as duplicate |
| DD-UT-003 | `test_allow_different_news` | Completely different news | Not marked as duplicate |
| DD-UT-004 | `test_hash_generation` | Generate unique hash | Hash is consistent |
| DD-UT-005 | `test_url_normalization` | Different URL formats | Normalizes correctly |
| DD-UT-006 | `test_cleanup_old_cache` | Cache older than 24h | Old items removed |
| DD-UT-007 | `test_persistent_cache` | Save/load cache file | Cache persists correctly |
| DD-UT-008 | `test_edge_case_empty_title` | News with empty title | Handles gracefully |
| DD-UT-009 | `test_unicode_in_title` | Unicode characters in title | Handles correctly |
| DD-UT-010 | `test_duplicate_across_sources` | Same news from 2 sources | Deduplicates correctly |

### 6.2.2 Celebrity Matcher Tests

**File**: `testing/test_cases/unit/test_celebrity_matcher.py`

| Test Case ID | Test Name | Description | Expected Result |
|--------------|-----------|-------------|-----------------|
| CM-UT-001 | `test_match_celebrity_full_name` | "Virat Kohli" in text | Match found |
| CM-UT-002 | `test_match_celebrity_alias` | "King Kohli" in text | Match found via alias |
| CM-UT-003 | `test_extract_amount_crore` | "₹34 Cr" in text | Amount extracted: 34 |
| CM-UT-004 | `test_extract_amount_lakh` | "₹5.2 Lakh" in text | Amount extracted: 0.052 |
| CM-UT-005 | `test_high_value_detection` | Amount >₹5 Cr | Flagged as high-value |
| CM-UT-006 | `test_low_value_filtering` | Amount <₹5 Cr | Not flagged |
| CM-UT-007 | `test_multiple_celebrities` | 2 celebrities mentioned | Both matched |
| CM-UT-008 | `test_false_positive_prevention` | "Kohli Road" mentioned | No false match |
| CM-UT-009 | `test_confidence_scoring` | Match confidence level | Returns 0-100 score |
| CM-UT-010 | `test_celebrity_database_load` | Load 500+ celebrities | All loaded correctly |

### 6.2.3 Categorizer Tests

**File**: `testing/test_cases/unit/test_categorizer.py`

| Test Case ID | Test Name | Description | Expected Result |
|--------------|-----------|-------------|-----------------|
| CT-UT-001 | `test_categorize_real_estate_news` | News about property prices | Category: real_estate |
| CT-UT-002 | `test_categorize_infrastructure` | News about metro project | Category: infrastructure |
| CT-UT-003 | `test_categorize_celebrity_deal` | Celebrity property purchase | Category: celebrity_deal |
| CT-UT-004 | `test_categorize_policy_news` | PMAY scheme update | Category: policy |
| CT-UT-005 | `test_categorize_personal_interest` | BTS related news | Category: personal_interest |
| CT-UT-006 | `test_priority_scoring_high` | Budget announcement | Priority: 9-10 |
| CT-UT-007 | `test_priority_scoring_medium` | City price trend | Priority: 5-7 |
| CT-UT-008 | `test_priority_scoring_low` | General market news | Priority: 1-4 |
| CT-UT-009 | `test_add_city_tags` | News mentions Mumbai | Tags: ["Mumbai"] |
| CT-UT-010 | `test_filter_irrelevant_news` | Completely unrelated news | Filtered out |

## 6.3 Notifier Tests

### 6.3.1 Telegram Notifier Tests

**File**: `testing/test_cases/unit/test_telegram_notifier.py`

| Test Case ID | Test Name | Description | Expected Result |
|--------------|-----------|-------------|-----------------|
| TN-UT-001 | `test_send_message_success` | Send valid message | Returns success response |
| TN-UT-002 | `test_send_message_with_markdown` | Message with markdown | Formatted correctly |
| TN-UT-003 | `test_send_long_message` | Message >4096 chars | Splits into multiple |
| TN-UT-004 | `test_format_morning_digest` | Format morning template | Template applied correctly |
| TN-UT-005 | `test_format_event_alert` | Format event template | Template applied correctly |
| TN-UT-006 | `test_handle_telegram_error` | Telegram API error | Raises TelegramError |
| TN-UT-007 | `test_handle_network_timeout` | Network timeout | Retries 3 times |
| TN-UT-008 | `test_escape_special_chars` | Special markdown chars | Escaped correctly |
| TN-UT-009 | `test_add_category_icons` | News categories | Icons added correctly |
| TN-UT-010 | `test_truncate_long_title` | Very long title | Truncated with ... |

### 6.3.2 Email Notifier Tests

**File**: `testing/test_cases/unit/test_email_notifier.py`

| Test Case ID | Test Name | Description | Expected Result |
|--------------|-----------|-------------|-----------------|
| EN-UT-001 | `test_send_email_success` | Send valid email | Returns success |
| EN-UT-002 | `test_render_html_template` | Render HTML template | Valid HTML generated |
| EN-UT-003 | `test_send_morning_digest` | Morning digest email | Subject + body correct |
| EN-UT-004 | `test_send_event_alert` | Event alert email | Subject + body correct |
| EN-UT-005 | `test_handle_smtp_error` | SMTP connection error | Raises EmailError |
| EN-UT-006 | `test_handle_auth_failure` | Invalid Gmail password | Raises AuthError |
| EN-UT-007 | `test_attach_inline_images` | Email with images | Images embedded correctly |
| EN-UT-008 | `test_html_sanitization` | Untrusted HTML content | Sanitized correctly |
| EN-UT-009 | `test_email_size_limit` | Very large email | Stays under 25MB |
| EN-UT-010 | `test_fallback_plain_text` | HTML rendering fails | Falls back to plain text |

---

# 7. INTEGRATION TESTS

## 7.1 Pipeline Integration Tests

**File**: `testing/test_cases/integration/test_pipeline.py`

| Test Case ID | Test Name | Description | Expected Result |
|--------------|-----------|-------------|-----------------|
| PI-IT-001 | `test_full_pipeline_morning_digest` | Complete morning workflow | News → Process → Notify |
| PI-IT-002 | `test_full_pipeline_event_alert` | Complete event workflow | Event trigger → Scrape → Alert |
| PI-IT-003 | `test_scraper_to_processor` | Scraped data → Processor | Data flows correctly |
| PI-IT-004 | `test_processor_to_notifier` | Processed data → Notifier | Notifications sent |
| PI-IT-005 | `test_deduplication_in_pipeline` | Duplicate news filtered | Only unique news sent |
| PI-IT-006 | `test_celebrity_matching_in_pipeline` | Celebrity news detected | Flagged correctly |
| PI-IT-007 | `test_categorization_in_pipeline` | News categorized | Categories assigned |
| PI-IT-008 | `test_multiple_sources_aggregation` | News from 3+ sources | Aggregated correctly |
| PI-IT-009 | `test_error_in_middle_of_pipeline` | 1 scraper fails | Other scrapers continue |
| PI-IT-010 | `test_empty_pipeline_run` | No news found | Sends "No updates" message |

## 7.2 Configuration Tests

**File**: `testing/test_cases/integration/test_config_reload.py`

| Test Case ID | Test Name | Description | Expected Result |
|--------------|-----------|-------------|-----------------|
| CF-IT-001 | `test_hot_reload_sources_config` | Update sources.json | New source active |
| CF-IT-002 | `test_hot_reload_keywords_config` | Update keywords.json | New keywords tracked |
| CF-IT-003 | `test_hot_reload_celebrities_config` | Update celebrities.json | New celebrity tracked |
| CF-IT-004 | `test_hot_reload_events_config` | Update events.json | New event scheduled |
| CF-IT-005 | `test_invalid_config_handling` | Invalid JSON config | Falls back to previous |
| CF-IT-006 | `test_config_validation` | Config with missing fields | Validation errors shown |
| CF-IT-007 | `test_config_backup_restore` | Config corrupted | Restores from backup |
| CF-IT-008 | `test_config_migration` | Old config format | Migrates to new format |
| CF-IT-009 | `test_config_env_override` | Env vars override config | Env vars take precedence |
| CF-IT-010 | `test_config_secrets_loading` | Load secrets from GitHub | Secrets loaded correctly |

## 7.3 Scheduling Tests

**File**: `testing/test_cases/integration/test_scheduling.py`

| Test Case ID | Test Name | Description | Expected Result |
|--------------|-----------|-------------|-----------------|
| SC-IT-001 | `test_morning_digest_trigger` | 7:00 AM cron job | Job executes correctly |
| SC-IT-002 | `test_evening_digest_trigger` | 4:00 PM cron job | Job executes correctly |
| SC-IT-003 | `test_event_alert_trigger` | Every 15 min during event | Alerts sent on schedule |
| SC-IT-004 | `test_timezone_handling` | IST timezone correct | Times converted correctly |
| SC-IT-005 | `test_skip_if_already_running` | Job still running | Skips next execution |
| SC-IT-006 | `test_retry_on_failure` | Job fails | Retries after 5 minutes |
| SC-IT-007 | `test_event_activation` | Event day starts | 15-min alerts activated |
| SC-IT-008 | `test_event_deactivation` | Event day ends | 15-min alerts stopped |
| SC-IT-009 | `test_manual_trigger` | Manual workflow trigger | Executes immediately |
| SC-IT-010 | `test_missed_job_recovery` | Missed schedule | Catches up on next run |

---

# 8. END-TO-END TESTS

## 8.1 Morning Digest Workflow

**File**: `testing/test_cases/e2e/test_morning_digest.py`

| Test Case ID | Test Name | Description | Expected Result |
|--------------|-----------|-------------|-----------------|
| MD-E2E-001 | `test_morning_digest_complete_flow` | Full morning workflow | Telegram + Email sent |
| MD-E2E-002 | `test_morning_digest_with_real_estate_news` | 3 real estate articles | Categorized correctly |
| MD-E2E-003 | `test_morning_digest_with_celebrity_deal` | 1 celebrity deal | High priority alert |
| MD-E2E-004 | `test_morning_digest_with_bts_news` | 2 BTS articles | Personal interest tagged |
| MD-E2E-005 | `test_morning_digest_with_no_news` | No overnight news | "No updates" message |
| MD-E2E-006 | `test_morning_digest_with_duplicates` | 5 news, 2 duplicates | Only 3 sent |
| MD-E2E-007 | `test_morning_digest_competitor_tracking` | Competitor published 2 articles | Competitor alerts included |
| MD-E2E-008 | `test_morning_digest_formatting` | Check Telegram + Email format | Formatting correct |
| MD-E2E-009 | `test_morning_digest_timing` | Check execution time | Completes <2 minutes |
| MD-E2E-010 | `test_morning_digest_notification_order` | Telegram first, then email | Order correct |

## 8.2 Event Alert Workflow

**File**: `testing/test_cases/e2e/test_event_alerts.py`

| Test Case ID | Test Name | Description | Expected Result |
|--------------|-----------|-------------|-----------------|
| EA-E2E-001 | `test_budget_day_alerts` | Budget Feb 1st workflow | 15-min alerts active |
| EA-E2E-002 | `test_rbi_policy_alerts` | RBI policy day workflow | Live updates sent |
| EA-E2E-003 | `test_event_start_notification` | Event day starts 10:30 AM | "Event tracking active" msg |
| EA-E2E-004 | `test_event_end_notification` | Event day ends 6:00 PM | "Event tracking stopped" msg |
| EA-E2E-005 | `test_high_frequency_alerts` | 4 alerts in 1 hour | All sent, no rate limit hit |
| EA-E2E-006 | `test_breaking_news_priority` | Breaking Budget news | Sent immediately |
| EA-E2E-007 | `test_event_news_categorization` | Event-related news | Tagged with event name |
| EA-E2E-008 | `test_event_outside_hours` | Event news at 8 PM | Still sent (outside event hours) |
| EA-E2E-009 | `test_multiple_events_same_day` | Budget + RBI same day | Both tracked separately |
| EA-E2E-010 | `test_event_with_no_updates` | Event day, no news | "No updates yet" message |

## 8.3 User Workflow Tests

**File**: `testing/test_cases/e2e/test_user_workflows.py`

| Test Case ID | Test Name | Description | Expected Result |
|--------------|-----------|-------------|-----------------|
| UW-E2E-001 | `test_wife_typical_day` | Morning → Work → Evening | All alerts received |
| UW-E2E-002 | `test_wife_checks_telegram_first` | Telegram notification arrives | Brief summary shown |
| UW-E2E-003 | `test_wife_checks_email_details` | Email notification arrives | Full details shown |
| UW-E2E-004 | `test_wife_clicks_article_link` | Click source link | Link valid and works |
| UW-E2E-005 | `test_wife_adds_new_celebrity` | Update celebrities.json | New celebrity tracked |
| UW-E2E-006 | `test_wife_adds_new_event` | Update events.json | New event scheduled |
| UW-E2E-007 | `test_wife_changes_schedule` | Update schedules.json | New schedule active |
| UW-E2E-008 | `test_wife_on_slow_news_day` | No news all day | Evergreen topics suggested |
| UW-E2E-009 | `test_wife_on_busy_news_day` | 20+ news items | Top 10 prioritized |
| UW-E2E-010 | `test_wife_mobile_experience` | All on mobile phone | Formatting mobile-friendly |

---

# 9. PERFORMANCE TESTS

## 9.1 Load Tests

**File**: `testing/test_cases/performance/test_load.py`

| Test Case ID | Test Name | Description | Target |
|--------------|-----------|-------------|--------|
| PF-LD-001 | `test_scrape_100_articles` | Scrape 100 news articles | <60 seconds |
| PF-LD-002 | `test_process_100_articles` | Process 100 articles | <10 seconds |
| PF-LD-003 | `test_deduplicate_1000_items` | Dedup 1000 items | <5 seconds |
| PF-LD-004 | `test_categorize_500_articles` | Categorize 500 articles | <15 seconds |
| PF-LD-005 | `test_match_celebrities_1000_items` | Match celebs in 1000 items | <20 seconds |
| PF-LD-006 | `test_send_100_telegram_messages` | Send 100 Telegram msgs | <30 seconds |
| PF-LD-007 | `test_send_100_emails` | Send 100 emails | <60 seconds |
| PF-LD-008 | `test_memory_usage_under_load` | Process 1000 articles | <512MB RAM |
| PF-LD-009 | `test_cpu_usage_under_load` | Full pipeline run | <80% CPU |
| PF-LD-010 | `test_concurrent_scraping` | 10 scrapers parallel | Completes correctly |

## 9.2 Stress Tests

**File**: `testing/test_cases/performance/test_stress.py`

| Test Case ID | Test Name | Description | Expected Behavior |
|--------------|-----------|-------------|-------------------|
| PF-ST-001 | `test_handle_1000_news_items` | Extreme news volume | Graceful degradation |
| PF-ST-002 | `test_handle_50_scrapers` | Many scrapers running | Rate limiting kicks in |
| PF-ST-003 | `test_handle_network_latency` | 5-second response times | Timeouts trigger correctly |
| PF-ST-004 | `test_handle_memory_pressure` | RAM usage 90%+ | Garbage collection works |
| PF-ST-005 | `test_handle_cpu_saturation` | CPU usage 95%+ | Throttling activates |
| PF-ST-006 | `test_handle_disk_full` | Disk 95% full | Cleans up old logs |
| PF-ST-007 | `test_handle_continuous_failures` | 100 consecutive errors | Circuit breaker opens |
| PF-ST-008 | `test_handle_rapid_config_changes` | 50 config updates/min | Handles gracefully |
| PF-ST-009 | `test_handle_long_running_session` | 24-hour continuous run | No memory leaks |
| PF-ST-010 | `test_recover_after_stress` | System under stress → normal | Recovers correctly |

---

# 10. SECURITY TESTS

## 10.1 Security Validation Tests

**File**: `testing/test_cases/security/test_security.py`

| Test Case ID | Test Name | Description | Expected Result |
|--------------|-----------|-------------|-----------------|
| SC-SE-001 | `test_api_keys_not_logged` | Check all logs | No API keys in logs |
| SC-SE-002 | `test_secrets_not_in_repo` | Check git history | No secrets committed |
| SC-SE-003 | `test_sql_injection_prevention` | Inject SQL in search | Query sanitized |
| SC-SE-004 | `test_command_injection_prevention` | Inject shell commands | Commands escaped |
| SC-SE-005 | `test_xss_prevention_in_email` | XSS in news content | HTML sanitized |
| SC-SE-006 | `test_https_enforced` | HTTP URLs used | Upgraded to HTTPS |
| SC-SE-007 | `test_input_validation` | Invalid config inputs | Validation errors |
| SC-SE-008 | `test_rate_limiting` | 1000 requests/min | Rate limit enforced |
| SC-SE-009 | `test_secure_credential_storage` | Check credential files | Encrypted or in secrets |
| SC-SE-010 | `test_dependency_vulnerabilities` | Run `pip audit` | No critical vulns |

---

# 11. TEST DATA MANAGEMENT

## 11.1 Test Fixtures

### 11.1.1 Mock News Articles

**File**: `testing/fixtures/test_news.json`

```json
{
  "real_estate_news": [
    {
      "title": "Mumbai property prices up 4.9% in Q4 2026",
      "source": "Economic Times",
      "url": "https://example.com/news/1",
      "published_at": "2026-01-15T10:30:00Z",
      "category": "real_estate",
      "priority": 7
    }
  ],
  "celebrity_deals": [
    {
      "title": "Virat Kohli buys ₹34 Cr Worli apartment",
      "source": "Livemint",
      "url": "https://example.com/news/2",
      "published_at": "2026-01-16T08:00:00Z",
      "category": "celebrity_deal",
      "priority": 9,
      "celebrity": "Virat Kohli",
      "amount": 34,
      "location": "Worli, Mumbai"
    }
  ]
}
```

### 11.1.2 Mock Celebrity Database

**File**: `testing/fixtures/test_celebrities.json`

```json
{
  "celebrities": [
    {
      "name": "Virat Kohli",
      "aliases": ["King Kohli", "Chikoo", "Run Machine"],
      "category": "Sports",
      "high_value_threshold": 5
    },
    {
      "name": "Shah Rukh Khan",
      "aliases": ["SRK", "King Khan", "Badshah"],
      "category": "Bollywood",
      "high_value_threshold": 10
    }
  ]
}
```

### 11.1.3 Mock HTTP Responses

**File**: `testing/fixtures/mock_responses.py`

```python
ECONOMIC_TIMES_HTML = """
<html>
  <article class="story-box">
    <h2>Mumbai property prices up 4.9% in Q4 2026</h2>
    <time>2026-01-15</time>
    <a href="/news/property-prices">Read more</a>
  </article>
</html>
"""

IGRS_MAHARASHTRA_HTML = """
<html>
  <table id="property-deals">
    <tr>
      <td>Virat Kohli</td>
      <td>34,00,00,000</td>
      <td>Worli</td>
      <td>2,04,00,000</td>
    </tr>
  </table>
</html>
"""

TELEGRAM_SUCCESS_RESPONSE = {
  "ok": True,
  "result": {
    "message_id": 12345,
    "date": 1705392000
  }
}
```

---

# 12. CI/CD INTEGRATION

## 12.1 GitHub Actions Workflow

**File**: `.github/workflows/test.yml`

```yaml
name: Automated Testing Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight
  workflow_dispatch:  # Manual trigger

jobs:
  smoke-tests:
    name: Smoke Tests (30s)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r testing/requirements-test.txt
      - name: Run smoke tests
        run: |
          pytest testing/test_cases/smoke/ -v --tb=short
        timeout-minutes: 2

  unit-tests:
    name: Unit Tests (5min)
    runs-on: ubuntu-latest
    needs: smoke-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r testing/requirements-test.txt
      - name: Run unit tests
        run: |
          pytest testing/test_cases/unit/ -v --cov=src --cov-report=xml
        timeout-minutes: 10
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  integration-tests:
    name: Integration Tests (10min)
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r testing/requirements-test.txt
      - name: Run integration tests
        run: |
          pytest testing/test_cases/integration/ -v
        timeout-minutes: 15
        env:
          TEST_MODE: true

  e2e-tests:
    name: E2E Tests (30min)
    runs-on: ubuntu-latest
    needs: integration-tests
    if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r testing/requirements-test.txt
      - name: Run E2E tests
        run: |
          pytest testing/test_cases/e2e/ -v
        timeout-minutes: 45
        env:
          TEST_MODE: true
          TELEGRAM_BOT_TOKEN_TEST: ${{ secrets.TELEGRAM_BOT_TOKEN_TEST }}
          TELEGRAM_CHAT_ID_TEST: ${{ secrets.TELEGRAM_CHAT_ID_TEST }}
          GMAIL_ADDRESS_TEST: ${{ secrets.GMAIL_ADDRESS_TEST }}
          GMAIL_APP_PASSWORD_TEST: ${{ secrets.GMAIL_APP_PASSWORD_TEST }}

  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install pip-audit safety
      - name: Run security audit
        run: |
          pip-audit
          safety check

  generate-issue-on-failure:
    name: Generate Issue File
    runs-on: ubuntu-latest
    if: failure()
    needs: [unit-tests, integration-tests, e2e-tests]
    steps:
      - uses: actions/checkout@v4
      - name: Generate issue file
        run: |
          python testing/scripts/generate_issue.py
      - name: Upload issue artifact
        uses: actions/upload-artifact@v3
        with:
          name: test-failure-issue
          path: testing/issues/*.md
```

## 12.2 Pre-Commit Hooks

**File**: `.pre-commit-config.yaml`

```yaml
repos:
  - repo: local
    hooks:
      - id: smoke-tests
        name: Run Smoke Tests
        entry: pytest testing/test_cases/smoke/ -v
        language: system
        pass_filenames: false
        always_run: true
```

---

# 13. ISSUE MANAGEMENT

## 13.1 Automated Issue Generation

When tests fail, the system automatically generates issue files.

**File**: `testing/scripts/generate_issue.py`

```python
#!/usr/bin/env python3
"""
Auto-generate issue files for test failures.
Claude CLI can pick these up and fix them autonomously.
"""

import os
import datetime
from pathlib import Path

def generate_issue(test_failure):
    """Generate issue file from test failure."""

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    issue_file = Path(f"testing/issues/issue_{timestamp}.md")

    content = f"""# TEST FAILURE ISSUE
## Auto-Generated: {datetime.datetime.now().isoformat()}

---

## 🔴 FAILURE SUMMARY

**Test Case**: `{test_failure['test_name']}`
**Test File**: `{test_failure['test_file']}`
**Component**: `{test_failure['component']}`
**Priority**: `{test_failure['priority']}`

---

## 📝 ERROR DESCRIPTION

{test_failure['error_message']}

---

## 📚 STACK TRACE

```
{test_failure['stack_trace']}
```

---

## 🔍 ROOT CAUSE ANALYSIS

{test_failure['root_cause']}

---

## 🔧 SUGGESTED FIXES

{test_failure['suggested_fixes']}

---

## ✅ REPRODUCTION STEPS

1. {test_failure['reproduction_step_1']}
2. {test_failure['reproduction_step_2']}
3. {test_failure['reproduction_step_3']}

---

## 📎 RELATED FILES

- {test_failure['related_file_1']}
- {test_failure['related_file_2']}

---

## 🤖 CLAUDE CLI INSTRUCTIONS

**This issue can be fixed autonomously by Claude CLI.**

To fix this issue:
1. Read this issue file
2. Analyze the root cause
3. Implement the suggested fix
4. Run the failing test to verify
5. Mark this issue as resolved

---

## 📊 TEST CONTEXT

- **Test Suite**: {test_failure['test_suite']}
- **Test Duration**: {test_failure['duration']}ms
- **Test Run ID**: {test_failure['run_id']}
- **Environment**: {test_failure['environment']}

---

**Status**: 🔴 OPEN
**Assigned To**: Claude CLI (Next Session)
"""

    issue_file.write_text(content)
    return str(issue_file)
```

## 13.2 Issue File Template

**Example**: `testing/issues/issue_20260130_143052.md`

```markdown
# TEST FAILURE ISSUE
## Auto-Generated: 2026-01-30T14:30:52Z

---

## 🔴 FAILURE SUMMARY

**Test Case**: `test_scrape_economic_times_success`
**Test File**: `testing/test_cases/unit/test_news_scraper.py`
**Component**: `NewsScraper`
**Priority**: `HIGH`

---

## 📝 ERROR DESCRIPTION

AssertionError: Expected 5 news items, got 0. The scraper returned an empty list when scraping Economic Times.

---

## 📚 STACK TRACE

```
testing/test_cases/unit/test_news_scraper.py:45: in test_scrape_economic_times_success
    assert len(news_items) == 5
E   AssertionError: assert 0 == 5
```

---

## 🔍 ROOT CAUSE ANALYSIS

The Economic Times website structure changed. The CSS selector `article.story-box` no longer exists. The new structure uses `div.eachStory`.

---

## 🔧 SUGGESTED FIXES

1. **Update CSS Selector**: Change selector from `article.story-box` to `div.eachStory`
2. **Add Fallback Selector**: Implement multiple selector strategy
3. **Add Structure Validation**: Add test to detect structure changes early

**Proposed Code Change**:
```python
# Before
selector = "article.story-box"

# After
selectors = ["div.eachStory", "article.story-box"]  # Try new first, fallback to old
```

---

## ✅ REPRODUCTION STEPS

1. Run: `pytest testing/test_cases/unit/test_news_scraper.py::test_scrape_economic_times_success -v`
2. Observe: Test fails with assertion error
3. Verify: Scraper returns empty list

---

## 📎 RELATED FILES

- `src/scrapers/news_scraper.py` (line 78 - selector definition)
- `testing/fixtures/mock_responses.py` (line 12 - mock HTML)

---

## 🤖 CLAUDE CLI INSTRUCTIONS

**This issue can be fixed autonomously by Claude CLI.**

To fix this issue:
1. Read `src/scrapers/news_scraper.py`
2. Update the CSS selector on line 78
3. Update mock fixtures if needed
4. Run: `pytest testing/test_cases/unit/test_news_scraper.py::test_scrape_economic_times_success -v`
5. Verify test passes
6. Mark this issue as resolved

---

## 📊 TEST CONTEXT

- **Test Suite**: Unit Tests
- **Test Duration**: 243ms
- **Test Run ID**: run_20260130_143050
- **Environment**: GitHub Actions / ubuntu-latest

---

**Status**: 🔴 OPEN
**Assigned To**: Claude CLI (Next Session)
```

---

# 14. TEST EXECUTION SCHEDULE

## 14.1 Automated Test Schedule

| Schedule | Tests Run | Trigger | Duration | Purpose |
|----------|-----------|---------|----------|---------|
| **Every Commit** | Smoke tests | Pre-commit hook | 30s | Quick validation |
| **Every Push** | Unit + Integration | GitHub Actions | 10min | Full validation |
| **Every PR** | Unit + Integration + Security | GitHub Actions | 15min | PR approval gate |
| **Daily (Midnight)** | Full suite (Unit + Integration + E2E) | GitHub Actions | 30min | Nightly build |
| **Weekly (Sunday)** | Full suite + Real external deps | GitHub Actions | 2hr | External validation |
| **On Demand** | Any test suite | Manual trigger | Varies | Debugging |

## 14.2 Test Execution Commands

### Local Development

```bash
# Run all tests
pytest testing/

# Run smoke tests only
pytest testing/test_cases/smoke/ -v

# Run unit tests only
pytest testing/test_cases/unit/ -v

# Run integration tests only
pytest testing/test_cases/integration/ -v

# Run E2E tests only
pytest testing/test_cases/e2e/ -v

# Run specific test file
pytest testing/test_cases/unit/test_news_scraper.py -v

# Run specific test case
pytest testing/test_cases/unit/test_news_scraper.py::test_scrape_economic_times_success -v

# Run with coverage
pytest testing/ --cov=src --cov-report=html

# Run in parallel (faster)
pytest testing/ -n auto

# Run with debugging
pytest testing/ -v --tb=long --pdb

# Run only failed tests from last run
pytest --lf testing/
```

### CI/CD

```bash
# GitHub Actions (automatic)
git push origin main  # Triggers test workflow

# Manual trigger via GitHub CLI
gh workflow run test.yml

# View test results
gh run list --workflow=test.yml
gh run view <run-id>
```

---

# 15. SUCCESS CRITERIA

## 15.1 Test Coverage Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **Overall Code Coverage** | ≥90% | TBD | ⏳ Pending |
| **Unit Test Coverage** | ≥95% | TBD | ⏳ Pending |
| **Integration Test Coverage** | ≥85% | TBD | ⏳ Pending |
| **E2E Test Coverage** | 100% user workflows | TBD | ⏳ Pending |
| **Critical Path Coverage** | 100% | TBD | ⏳ Pending |

## 15.2 Test Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Test Reliability** | ≥99% pass rate | (Passed / Total) × 100 |
| **Test Execution Time** | <30 min (full suite) | Total time for all tests |
| **Flaky Test Rate** | <1% | Tests that intermittently fail |
| **Issue Detection Rate** | 100% | Failures with issue files |
| **Auto-Fix Success Rate** | ≥80% | Issues fixed by Claude CLI |

## 15.3 Definition of Done (DoD)

A test plan is considered complete when:

- ✅ All test files created and executable
- ✅ All tests pass on first run
- ✅ Code coverage meets targets (90%+)
- ✅ CI/CD pipeline configured and working
- ✅ Issue generation working for failures
- ✅ Test documentation complete
- ✅ Claude CLI can run tests autonomously
- ✅ Claude CLI can fix issues autonomously

## 15.4 Test Acceptance Criteria

### For Each Test Case:

1. **Clear Purpose**: Test name describes what it tests
2. **Reproducible**: Same input → same output
3. **Independent**: Can run in any order
4. **Fast**: Completes within timeout
5. **Isolated**: Uses mocks, doesn't hit real APIs
6. **Assertive**: Has clear pass/fail criteria
7. **Documented**: Has docstring explaining purpose

### For Test Suite:

1. **Complete Coverage**: All components tested
2. **Automated Execution**: No manual steps
3. **CI/CD Integration**: Runs on push/PR
4. **Issue Generation**: Creates issues on failure
5. **Self-Healing**: Retry logic for flaky tests
6. **Performance**: Full suite <30 minutes
7. **Maintainable**: Easy to add new tests

---

# 16. TEST EXECUTION LOGS

All test executions must generate logs in:

```
logs/phase_test_<timestamp>.log
```

## 16.1 Log Format

```
================================================================================
TEST EXECUTION LOG
================================================================================
Timestamp: 2026-01-30 14:30:52 IST
Test Suite: Full Suite (Unit + Integration + E2E)
Trigger: GitHub Actions (Daily Schedule)
Environment: ubuntu-latest, Python 3.9

--------------------------------------------------------------------------------
CONFIGURATION
--------------------------------------------------------------------------------
Working Directory: D:\Jasmine\00001_Content_app\News_Update
Test Mode: CI
Mock External APIs: Yes
Coverage Enabled: Yes

--------------------------------------------------------------------------------
TEST SUMMARY
--------------------------------------------------------------------------------
Total Tests: 245
Passed: 242
Failed: 3
Skipped: 0
Duration: 28m 34s

--------------------------------------------------------------------------------
COVERAGE REPORT
--------------------------------------------------------------------------------
Total Coverage: 92.5%
Unit Test Coverage: 95.3%
Integration Coverage: 87.2%
E2E Coverage: 100%

Files with <90% coverage:
- src/scrapers/igrs_scraper.py: 85.4%
- src/processors/celebrity_matcher.py: 88.1%

--------------------------------------------------------------------------------
FAILED TESTS
--------------------------------------------------------------------------------
1. test_scrape_economic_times_success
   File: testing/test_cases/unit/test_news_scraper.py:45
   Error: AssertionError: Expected 5 news items, got 0
   Issue: testing/issues/issue_20260130_143052.md

2. test_search_maharashtra_igr_success
   File: testing/test_cases/unit/test_igrs_scraper.py:78
   Error: ConnectionTimeout: Portal did not respond
   Issue: testing/issues/issue_20260130_143053.md

3. test_morning_digest_complete_flow
   File: testing/test_cases/e2e/test_morning_digest.py:23
   Error: Telegram API rate limit exceeded
   Issue: testing/issues/issue_20260130_143054.md

--------------------------------------------------------------------------------
PERFORMANCE METRICS
--------------------------------------------------------------------------------
Fastest Test: test_hash_generation (12ms)
Slowest Test: test_morning_digest_complete_flow (4m 32s)
Average Test Duration: 6.99s
Memory Peak: 387MB
CPU Peak: 72%

--------------------------------------------------------------------------------
ACTIONS TAKEN
--------------------------------------------------------------------------------
✅ Generated 3 issue files for failures
✅ Uploaded coverage report to Codecov
✅ Sent notification to monitoring channel
⏳ Awaiting Claude CLI to pick up issues

--------------------------------------------------------------------------------
NEXT STEPS
--------------------------------------------------------------------------------
1. Claude CLI should pick up issue files
2. Fix failed tests based on issue descriptions
3. Re-run failed tests to verify fixes
4. Update this log with resolution status

================================================================================
END OF LOG
================================================================================
```

---

# 17. APPENDIX

## 17.1 Testing Best Practices

### For Claude CLI Operators:

1. **Always read test failures carefully** - Issue files contain all info needed to fix
2. **Run tests locally before pushing** - Use pre-commit hooks
3. **Update tests when changing code** - Keep tests in sync
4. **Mock external dependencies** - Don't hit real APIs during testing
5. **Write descriptive test names** - `test_user_can_login` not `test_1`
6. **One assertion per test** - Makes failures easier to debug
7. **Use fixtures** - DRY principle applies to tests too
8. **Test edge cases** - Empty inputs, null values, boundary conditions
9. **Keep tests fast** - Mock slow operations
10. **Document complex test logic** - Future you will thank you

### For Test Maintenance:

1. **Review test coverage weekly** - Identify gaps
2. **Refactor flaky tests immediately** - Don't let them accumulate
3. **Update fixtures when schemas change** - Keep test data realistic
4. **Archive old test logs** - Keep last 30 days only
5. **Monitor test execution time** - Optimize slow tests
6. **Keep CI/CD pipeline green** - Fix failures within 24h

## 17.2 Common Test Patterns

### Pattern 1: Arrange-Act-Assert (AAA)

```python
def test_scrape_news_article():
    # Arrange - Set up test data
    mock_html = load_fixture("sample_article.html")
    scraper = NewsScraper()

    # Act - Execute the test
    result = scraper.parse(mock_html)

    # Assert - Verify the result
    assert result.title == "Expected Title"
    assert result.date == "2026-01-30"
```

### Pattern 2: Fixture-Based Testing

```python
@pytest.fixture
def sample_news_items():
    return [
        NewsItem(title="Article 1", date="2026-01-30"),
        NewsItem(title="Article 2", date="2026-01-30")
    ]

def test_deduplication(sample_news_items):
    deduplicator = Deduplicator()
    result = deduplicator.remove_duplicates(sample_news_items)
    assert len(result) == 2
```

### Pattern 3: Parameterized Testing

```python
@pytest.mark.parametrize("amount,expected", [
    ("₹34 Cr", 34.0),
    ("₹5.2 Lakh", 0.052),
    ("₹100 Cr", 100.0)
])
def test_extract_amount(amount, expected):
    matcher = CelebrityMatcher()
    result = matcher.extract_amount(amount)
    assert result == expected
```

## 17.3 Troubleshooting Guide

### Issue: Tests failing locally but passing in CI

**Cause**: Environment differences (timezone, file paths, dependencies)

**Solution**:
- Check `TEST_MODE` environment variable
- Verify Python version matches CI (3.9+)
- Check timezone settings (should be IST)
- Clear pytest cache: `pytest --cache-clear`

### Issue: Flaky tests (intermittently failing)

**Cause**: Race conditions, timing issues, external dependencies

**Solution**:
- Add `@pytest.mark.retry(count=3)` decorator
- Increase timeouts for slow operations
- Mock external dependencies
- Use `freezegun` to mock time-dependent code

### Issue: Tests taking too long

**Cause**: Hitting real APIs, not using parallelization

**Solution**:
- Ensure all external APIs are mocked
- Run tests in parallel: `pytest -n auto`
- Profile slow tests: `pytest --durations=10`
- Optimize or split slow tests

### Issue: Coverage not meeting target

**Cause**: Missing test cases, unreachable code

**Solution**:
- Generate coverage report: `pytest --cov=src --cov-report=html`
- Open `htmlcov/index.html` to see uncovered lines
- Write tests for uncovered code
- Remove dead code if unreachable

---

# 18. CONCLUSION

This comprehensive test plan ensures the Magic Bricks News Intelligence System is:

✅ **Fully tested** - 90%+ code coverage across all components
✅ **Reliably tested** - Automated CI/CD pipeline with multiple test levels
✅ **Autonomously tested** - Claude CLI can run tests without human intervention
✅ **Self-healing** - Automatic issue generation and resolution
✅ **Well-documented** - Clear test descriptions and maintenance guides

**The system is designed to never fail silently. Every failure is logged, analyzed, and actionable.**

---

**Test Plan Version**: 1.0
**Last Updated**: 2026-01-30
**Next Review**: 2026-02-15
**Owner**: Claude CLI Autonomous Testing System
