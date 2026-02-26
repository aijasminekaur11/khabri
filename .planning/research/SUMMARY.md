# Project Research Summary

**Project:** Khabri
**Domain:** Automated news aggregation and curated delivery — Indian infrastructure & real estate
**Researched:** 2026-02-26
**Confidence:** HIGH (stack and architecture), MEDIUM-HIGH (features and pitfalls)

## Executive Summary

Khabri is a domain-specialized, zero-infrastructure-cost news aggregation system targeting two users who co-write content about Indian real estate and infrastructure. Research confirms the build approach: a split-deployment model with GitHub Actions handling all scheduled data processing (RSS fetching, AI classification, deduplication, delivery) and Vercel hosting only a thin Telegram webhook that fires async GitHub Actions dispatches. The entire system requires no database — mutable state (seen articles, config, keyword library) lives as JSON files committed back to the repo after each run. This architecture is well-documented, free to operate at the target scale, and avoids the complexity of a persistent server.

The recommended stack is Python 3.12 throughout, with FastAPI for the Vercel webhook, python-telegram-bot v22 for Telegram integration, feedparser + httpx for RSS fetching, and the Anthropic SDK with Claude Sonnet as the primary AI classifier. The critical version decision is to use `google-genai` (not `google-generativeai`, which reached EOL November 2025) for the Gemini fallback. Semantic deduplication via local sentence-transformers embeddings keeps AI costs below the $5/month budget by avoiding LLM-based dedup.

The top risks are operational, not architectural: GitHub's 60-day inactivity policy silently disables scheduled workflows; GNews.io's 100 req/day free limit can be exhausted by naive per-keyword API calls; and the Vercel cold-start window can trigger Telegram webhook retry storms if the immediate-acknowledge pattern is not implemented. All three risks have clear prevention strategies that must be baked into the earliest phases rather than retrofitted. The combination of Indian wire-service republication patterns (PTI/ANI stories appearing across 5+ outlets simultaneously) and domain-specific vocabulary overlap also requires a two-stage deduplication strategy rather than simple cosine similarity.

## Key Findings

### Recommended Stack

The stack is clean and well-validated. Python 3.12 is the correct runtime — it is the default on Vercel's Python runtime and supported natively by GitHub Actions. The split-deployment model means two distinct dependency surfaces: a lightweight Vercel function (`FastAPI` + `python-telegram-bot`) and a heavier GitHub Actions pipeline (`feedparser`, `httpx`, `anthropic`, `google-genai`, `sentence-transformers`, `Jinja2`). Using `uv` for dependency management gives reproducible installs across both environments via `uv.lock` and the `astral-sh/setup-uv` GitHub Action.

**Core technologies:**
- **Python 3.12:** Primary runtime — matches Vercel default, best RSS/AI ecosystem
- **FastAPI 0.133.1:** Vercel webhook receiver — ASGI-native, async, official Vercel support
- **python-telegram-bot 22.6:** Telegram framework — full async, ConversationHandler for bot menus
- **feedparser 6.0.12 + httpx 0.28.1:** RSS fetching — industry-standard parser with async HTTP transport
- **anthropic 0.84.0:** Claude AI classification — primary analyzer with batch API for 50% cost savings
- **google-genai 1.65.0:** Gemini AI — fallback only; replaces deprecated `google-generativeai` (EOL Nov 2025)
- **sentence-transformers:** Local embedding dedup — free, fast (~5ms/article), avoids LLM dedup costs
- **Jinja2 3.1.6 + smtplib:** HTML email rendering and Gmail SMTP delivery
- **GitHub repo as data store:** `seen.json`, `config.json`, `keywords.json` committed back via `EndBug/add-and-commit`
- **uv:** Dependency management — faster than pip, proper lockfile for CI reproducibility

### Expected Features

Research confirms a clear feature hierarchy. The MVP is defined by the dependency chain: fetching enables filtering, filtering enables AI classification, classification enables deduplication, and deduplication enables reliable scheduled delivery. Nothing in the core pipeline is optional.

**Must have (table stakes — all P1):**
- RSS feed fetching (10-15 curated Indian real estate feeds) — without this, nothing works
- GNews.io API integration with keyword queries — extends coverage beyond RSS
- Keyword-based filtering with category library (Infrastructure / Regulatory / Celebrity) — defines relevance
- AI priority classification (HIGH/MEDIUM/LOW) via Claude Sonnet with domain-primed system prompt
- Semantic deduplication against 7-day history — without this, repeated PTI/ANI stories destroy trust
- Scheduled delivery at 7 AM and 4 PM IST via GitHub Actions cron
- Telegram message delivery to both users (formatted, priority-labelled)
- HTML email digest via Gmail SMTP — secondary channel users expect
- Basic bot commands: /help, /status, /pause, /resume
- Source health monitoring — surfaced in /status to prevent silent failures

**Should have (P2 — add after core delivery is validated):**
- Breaking news alerts (30-60 min separate cron, HIGH-only threshold)
- Natural language Telegram commands ("add keyword metro rail")
- Geographic tier priority scoring (Tier 1 city bias in ranking)
- Source credibility tier (ET Realty, Business Standard weighted higher)
- Delivery stats via /stats command

**Defer (v2+):**
- Event-based dynamic scheduling (Budget Day, RERA deadlines)
- Hindi-language source support
- Social media signal layer (Twitter/LinkedIn)
- Web UI / analytics dashboard

**Anti-features to explicitly reject:** full article scraping, per-user personalized keyword sets, ML-based recommendation learning, real-time WebSocket streaming, PDF report generation.

### Architecture Approach

The architecture is a strict two-tier split: a thin, stateless control plane (Vercel webhook) and a heavy, scheduled data plane (GitHub Actions). The webhook does nothing except parse intent, fire a `repository_dispatch` to GitHub, and return HTTP 200 within 2 seconds. All computation — fetching, normalizing, deduplicating, classifying, formatting, and delivering — runs in GitHub Actions with no time pressure. The shared communication medium between the two tiers is the GitHub repository itself (JSON files and `repository_dispatch` events). This eliminates the need for any external database, queue, or persistent server.

**Major components:**
1. **Vercel Webhook (`api/webhook.py`)** — receives Telegram updates, parses command intent, fires GitHub dispatch, returns 200 immediately
2. **GitHub Actions Scheduler (`.github/workflows/deliver.yml`)** — orchestrates the full pipeline on cron (01:30 UTC / 10:30 UTC) and on `repository_dispatch` events
3. **Fetcher (`pipeline/fetchers/`)** — GNews.io API + parallel RSS fetching via feedparser + httpx
4. **Normalizer (`pipeline/normalizer.py`)** — unified article schema (title, url, source, published_at, summary)
5. **Deduplicator (`pipeline/deduplicator.py`)** — two-stage: title hash fast-path + embedding similarity, 7-day rolling window
6. **AI Analyzer (`pipeline/analyzer.py`)** — batch Claude Sonnet call (all articles per run in one prompt), Gemini fallback on error
7. **Selector (`pipeline/selector.py`)** — keyword/geo/tier scoring, top-15 selection
8. **Formatters + Delivery (`pipeline/formatters/`, `delivery/`)** — Telegram Markdown and HTML email rendering; split into 4096-char chunks for Telegram
9. **Data Store (`data/`)** — `seen.json`, `config.json`, `keywords.json` committed back after each run
10. **Breaking News Watcher (`.github/workflows/breaking.yml`)** — lightweight 30-60 min cron, keyword-only fast-path (no AI unless confirmed HIGH)

**Key patterns to follow:**
- Thin webhook / heavy worker separation — never put pipeline logic inside Vercel function
- AI batch-per-run — one Claude API call per pipeline run, not per article
- Idempotent pipeline with title-hash deduplication — GitHub Actions retries are safe
- GitHub repo as flat-file data store — viable at 2-user, <1MB data scale

### Critical Pitfalls

1. **GitHub 60-day scheduled workflow disable** — Add `gautamkrishnar/keepalive-workflow` from the start; ensure the pipeline always commits back to the repo (even a no-news status update) to satisfy the activity requirement.

2. **GNews.io quota exhaustion (100 req/day)** — Design Boolean-grouped keyword queries (OR-combined) from day one; target max 20-25 API calls per combined daily run. Implement a daily quota tracker in JSON state. Never design one-query-per-keyword.

3. **Vercel cold-start causing Telegram webhook retry storms** — Implement the immediate-acknowledge pattern unconditionally: validate format, send "Processing..." to user, return HTTP 200 before doing any work. Store `update_id` to prevent duplicate processing on retries.

4. **AI cost overrun** — Truncate article input to title + first 150 words before AI calls. Use Anthropic Message Batches API (50% discount). Use prompt caching for the static system prompt (up to 90% reduction on repeated context). Track monthly spend in JSON state file.

5. **PTI/ANI wire-service duplicate detection failure** — Use two-stage dedup: (1) normalized title hash fast-path, (2) sentence-transformer embedding similarity at 0.85-0.90 threshold (not generic 0.95 — Indian real estate vocabulary inflates similarity scores). Keep only the highest-authority source when 3+ outlets publish the same story within 2 hours.

6. **RSS feed unreliability from Indian sources** — Always use `requests.get(url, timeout=10)` as the feedparser transport (not bare `feedparser.parse(url)` which has no timeout). Always check the `bozo` flag. Test each RSS source individually before committing it to production config.

7. **IST/UTC cron miscalculation** — Document UTC equivalents as comments in workflow YAML (7 AM IST = `30 1 * * *`; 4 PM IST = `30 10 * * *`). Always use `zoneinfo.ZoneInfo("Asia/Kolkata")` in Python, never a hardcoded `timedelta(hours=5, minutes=30)`.

## Implications for Roadmap

Based on the component dependency graph in ARCHITECTURE.md and the pitfall-to-phase mapping in PITFALLS.md, the build order is clear. Each phase delivers independently testable functionality before the next begins.

### Phase 1: Foundation — Data Layer, Scheduling, Feed Ingestion

**Rationale:** Everything downstream depends on reliable data ingestion and a working pipeline skeleton. The three critical pitfalls (60-day disable, GNews quota, IST/UTC cron) must all be addressed here, not retrofitted. This phase has no external AI dependency — it can be built and validated cheaply.

**Delivers:** Working GitHub Actions skeleton that fetches RSS + GNews, normalizes to unified schema, deduplicates, and logs results to stdout. JSON data schemas defined and committed. Keepalive workflow deployed.

**Addresses features:** RSS feed fetching, GNews.io integration, keyword filtering, source health logging, deduplication (data layer).

**Avoids pitfalls:** GitHub 60-day disable (keepalive), GNews quota exhaustion (Boolean-grouped queries designed upfront), IST/UTC cron drift (correct expressions documented), RSS unreliability (timeout + bozo checks), dedup history unbounded growth (7-day rolling window from day one).

**No deeper research needed:** All patterns are well-documented and stack choices are finalized.

### Phase 2: AI Classification Pipeline + Delivery

**Rationale:** With reliable normalized articles available from Phase 1, AI classification and delivery can be layered on top. AI cost controls and dedup quality must be proven before scheduling is enabled — a misconfigured AI loop is expensive to discover in production.

**Delivers:** Full pipeline from normalized articles through AI classification (Claude batch call), priority filtering, formatting, and delivery to both Telegram users and email. Includes two-stage semantic dedup.

**Addresses features:** AI priority classification, semantic deduplication, Telegram delivery, HTML email digest.

**Uses stack elements:** `anthropic` batch API, `google-genai` fallback, `sentence-transformers`, `Jinja2`, `smtplib`, `python-telegram-bot` (outbound send).

**Avoids pitfalls:** AI cost overrun (truncation + batch API + prompt caching from day one), PTI/ANI duplicate failure (two-stage dedup with domain-calibrated threshold), Telegram message length limits (4096-char chunking), Gmail SMTP connection reuse and retry logic.

**Research flag:** AI prompt engineering for Indian real estate domain classification accuracy may need iteration — build in budget for 2-3 prompt revision cycles before committing to final system prompt.

### Phase 3: GitHub Actions Scheduling + Production Wiring

**Rationale:** After the pipeline is proven in isolation (manual triggers), wire it to the cron schedule. This phase transforms a working script into a production-grade automated system.

**Delivers:** Fully automated scheduled delivery at 7 AM and 4 PM IST via GitHub Actions cron. Seen-article state committed back to repo after each run. `workflow_dispatch` for manual triggers.

**Addresses features:** Scheduled delivery (7 AM / 4 PM IST), source health monitoring in logs.

**Avoids pitfalls:** GitHub 60-day disable (keepalive + commit-back both active), IST/UTC cron (expressions validated against first 3 live runs).

**No deeper research needed:** Standard GitHub Actions patterns, well-documented.

### Phase 4: Vercel Webhook + Telegram Bot Commands

**Rationale:** The Vercel webhook is the last piece because it depends on all prior components (pipeline must be triggerable, keywords must be configurable). Building it last ensures it has a stable system to dispatch into.

**Delivers:** Telegram bot command interface (/help, /status, /pause, /resume, /run_now). Vercel webhook with immediate-acknowledge pattern. Basic keyword management commands.

**Addresses features:** Basic bot commands, Telegram control interface.

**Uses stack elements:** `FastAPI`, `python-telegram-bot` webhook mode, Vercel deployment, GitHub `repository_dispatch`.

**Avoids pitfalls:** Vercel cold-start webhook timeout (immediate-acknowledge + update_id dedup), Telegram flood control (rate limiting on command responses).

**Research flag:** Vercel cold-start behavior for Python functions — verify actual cold-start times on Hobby tier before assuming the 2-3 second estimate. If cold starts exceed 4 seconds consistently, fallback to polling mode in GitHub Actions.

### Phase 5: Enhanced Delivery Features (v1.x)

**Rationale:** After core delivery is validated and trusted by users, add the differentiators. These features require user feedback to calibrate correctly (breaking news alert threshold, geo-tier bias weights).

**Delivers:** Breaking news alerts (separate 30-60 min cron), /stats command, source credibility tier, geographic tier priority scoring, natural language bot commands.

**Addresses features:** All P2 features from FEATURES.md.

**Avoids pitfalls:** Breaking news alert fatigue (batch at most one alert per hour), AI cost creep from more frequent runs (breaking news uses keyword-only fast-path before AI confirmation).

**Research flag:** Natural language command parsing (Claude/regex hybrid) needs UX design — define the exact command vocabulary and confidence thresholds before implementation. Low-risk technically but high-risk for user experience if too permissive or too strict.

### Phase 6: Event-Based Scheduling + v2 Features (future)

**Rationale:** Defer until Phase 5 features are validated and user feedback confirms the need for event-calendar-aware delivery.

**Delivers:** Budget Day / RERA deadline-aware scheduling, potential Hindi-language source support, social media signal layer.

**Research flag:** This entire phase needs a dedicated research cycle — event calendar design, Hindi NLP tooling, and social API access patterns are all underspecified in current research.

### Phase Ordering Rationale

- **Data before AI:** Phase 1 validates fetch + dedup with zero AI cost. Bugs in the data layer are cheap to fix before the AI loop amplifies them.
- **AI before scheduling:** Phase 2 validates the pipeline in isolation (manual runs). Discovering a broken prompt or cost overrun before production scheduling avoids a week of bad automated runs.
- **Scheduling before webhook:** Phase 3 makes the system autonomous before the bot controls are added. The webhook (Phase 4) is the polish layer on top of an already-working system.
- **Core before enhancements:** Phases 5-6 add features only after Phase 3-4 have proven the system reliable enough that users trust it. Breaking news alerts on an unreliable system create noise.
- **Pitfalls addressed in earliest possible phase:** All three critical pitfalls (60-day disable, GNews quota, IST/UTC cron) land in Phase 1 because retrofitting them requires re-testing the entire system.

### Research Flags

Phases needing deeper research during planning:

- **Phase 2 (AI classification):** Domain-specific prompt engineering for Indian real estate will require iteration. Initial prompt quality is uncertain — plan for 2-3 revision cycles with real article sets before locking the system prompt.
- **Phase 4 (Vercel webhook):** Python cold-start times on Vercel Hobby tier need live verification before committing to the webhook architecture. If cold starts exceed 4 seconds reliably, the fallback is GitHub Actions long-polling mode — a significant architecture change.
- **Phase 6 (event scheduling + v2):** Needs a dedicated research phase. Event calendar design, Hindi NLP, and social media API access are all underspecified.

Phases with standard patterns (no additional research needed):

- **Phase 1:** RSS fetching, GitHub Actions setup, JSON state management — all well-documented patterns with official documentation support.
- **Phase 3:** GitHub Actions scheduling, git commit-back — standard, extensively documented.
- **Phase 5 (breaking news):** The lightweight cron + keyword-filter-before-AI pattern is a straightforward extension of Phase 2 components.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All package versions verified against PyPI as of Feb 26 2026; official docs confirmed for Vercel Python runtime and GitHub Actions integration; `google-genai` EOL verified |
| Features | MEDIUM-HIGH | Table stakes from multiple sources; differentiators validated against competitor analysis; GNews API limits HIGH confidence from official docs; some feature priority judgments are inferential |
| Architecture | HIGH | Core patterns (thin webhook / heavy worker, flat-file data store, batch AI) verified against official Vercel, GitHub Actions, and Anthropic docs; specific integration topology confirmed |
| Pitfalls | MEDIUM-HIGH | Critical pitfalls verified against official or high-confidence community sources; some (feedparser user-agent blocking) are LOW confidence single-source reports; PTI/ANI wire-service behavior is domain knowledge with MEDIUM confidence |

**Overall confidence:** HIGH for core build decisions; MEDIUM for edge cases and operational behavior of free-tier services.

### Gaps to Address

- **GNews.io free-tier caching behavior:** Research notes that morning results could be cached for the evening run, but this needs validation against GNews's actual API contract (does it return cached results or fresh results for the same query 9 hours later?). Address during Phase 1 implementation.

- **Vercel Hobby cold-start timing:** The 2-3 second cold-start estimate is from a community discussion (MEDIUM confidence). Actual Python 3.12 cold-start times on Hobby tier must be measured before finalizing the webhook architecture. Address during Phase 4 kickoff.

- **sentence-transformers on GitHub Actions runners:** `all-MiniLM-L6-v2` model download on first run adds 90MB network fetch. This may add 30-60 seconds to the first pipeline run. Consider pre-caching the model in the repo or using `actions/cache` for the HuggingFace model cache. Address during Phase 2.

- **AI classification threshold calibration:** The 0.85-0.90 cosine similarity threshold for deduplication and the HIGH/MEDIUM/LOW classification accuracy are research estimates. Both require calibration against real Indian real estate article sets during Phase 2.

- **Telegram message formatting for Indian content:** Article titles with mixed Devanagari/ASCII or special characters may require MarkdownV2 escaping that is more complex than standard ASCII. Address during Phase 2 formatting work.

## Sources

### Primary (HIGH confidence)
- PyPI official package pages — all version numbers and compatibility matrices verified Feb 26 2026
- Vercel Python Runtime docs (vercel.com/docs/functions/runtimes/python) — Hobby tier timeout, Python version support, ASGI support
- GitHub Actions schedule docs (docs.github.com/actions) — UTC cron, 5-minute minimum interval
- Anthropic Message Batches API (anthropic.com/news/message-batches-api) — 50% batch discount confirmed
- GNews.io official docs (docs.gnews.io) — 100 req/day limit, Boolean operator support, no full-text on free tier
- Telegram Bot API (core.telegram.org/bots/api) — webhook requirements, message limits
- feedparser official docs (pythonhosted.org/feedparser) — bozo flag behavior
- python-telegram-bot official wiki — webhook architecture, flood control limits
- Google GenAI SDK deprecation notice — EOL Nov 30 2025 confirmed
- zoneinfo PyPI page — official recommendation to migrate from pytz
- Vercel Hobby timeout knowledge base (vercel.com/kb) — 10-second function limit confirmed

### Secondary (MEDIUM confidence)
- Community discussions on GitHub 60-day scheduled workflow disable
- Vercel cold-start discussion thread (github.com/vercel/vercel) — 2-3 second Python cold-start estimate
- GitHub Actions cron delay discussion — 15-30 minute drift confirmed by multiple reports
- Architecture pattern articles (TDS, Netlify) — flat-file GitHub data store pattern
- Competitor analysis (Feedly, Inoreader feature pages) — feature comparison
- NewsCatcher API deduplication docs — PTI/ANI wire-service republication behavior
- FeedSpot Indian real estate RSS list — source discovery

### Tertiary (LOW confidence)
- feedparser user-agent blocking (HTTP 406) — single GitHub issue report, needs empirical verification with target Indian RSS sources
- Telegram keyword monitoring bot patterns — single Medium article, pattern validated against official Telegram docs

---
*Research completed: 2026-02-26*
*Ready for roadmap: yes*
