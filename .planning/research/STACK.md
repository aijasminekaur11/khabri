# Stack Research

**Domain:** Automated news aggregation with Telegram bot control, GitHub Actions scheduling, and AI-powered analysis
**Project:** Khabri
**Researched:** 2026-02-26
**Confidence:** HIGH (core stack verified via PyPI + official docs) / MEDIUM (patterns and integration choices verified via multiple sources)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12 | Primary runtime | Default on Vercel serverless (3.12/3.13/3.14 supported); GitHub Actions supports all modern versions; best RSS/scraping ecosystem |
| FastAPI | 0.133.1 | Telegram webhook receiver on Vercel | ASGI-native, async by default, zero-config on Vercel, official Vercel template exists; superior to Flask for this use case because it handles async I/O without blocking |
| python-telegram-bot | 22.6 | Telegram bot framework | Latest stable (Jan 2026); full async since v20; ConversationHandler for multi-step menus; InlineKeyboard for interactive controls; best-maintained Python Telegram library |
| feedparser | 6.0.12 | RSS feed parsing | Industry standard, 20+ year track record, handles RSS 0.9x/1.0/2.0/Atom; synchronous parser (pair with httpx for async fetching) |
| httpx | 0.28.1 | Async HTTP client for feed fetching | Async + sync in one library; HTTP/1.1 + HTTP/2; already a transitive dep of anthropic SDK; cleaner API than aiohttp; used internally by Anthropic SDK |
| anthropic | 0.84.0 | Claude API (primary AI analysis) | Latest stable (Feb 25 2026); built-in batch processing via `client.messages.batches`; async client with httpx backend; `claude-sonnet-4-5` recommended for cost/quality balance |
| google-genai | 1.65.0 | Gemini API (fallback AI analysis) | New unified SDK (Feb 26 2026) — replaces deprecated `google-generativeai` which reached EOL Nov 30 2025; GA status since May 2025 |
| Jinja2 | 3.1.6 | HTML email template rendering | Standard Python templating; Gmail SMTP + MIMEMultipart + Jinja2 is the idiomatic Python email stack; no external service dependency |
| python-dotenv | 1.2.1 | Local secrets management | Maps `.env` keys to `os.getenv()` — same code works locally (dotenv) and in GitHub Actions (env from secrets); do not use in production directly |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| newspaper4k | 0.9.4.1 | Full article text extraction from URLs | When you need article body beyond RSS snippet; fork of unmaintained newspaper3k; requires Python >=3.10; use after feedparser gives you the URL |
| pydantic | 2.12.5 | Data models + validation for news articles and config | Define `NewsArticle`, `DeliverySchedule`, `UserConfig` models; v2 is Rust-backed, ~5-10x faster than v1; replaces manual dict validation |
| sentence-transformers | latest (3.x) | Semantic duplicate detection | Use `all-MiniLM-L6-v2` model for embedding news titles/summaries; cosine similarity at threshold 0.85–0.92 catches near-duplicate stories across sources without LLM calls |
| pytest | latest (8.x) | Test runner | Standard Python test runner |
| pytest-asyncio | 1.3.0 | Async test support | Required for testing async feedparser+httpx fetch routines and Telegram handler coroutines; v1.0+ removed `event_loop` fixture — use new API |
| uv | latest | Dependency management and virtualenv | Rust-based, significantly faster than pip; `astral-sh/setup-uv` GitHub Action available; use `uv.lock` for reproducible installs in CI |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| GitHub Actions (`schedule` trigger) | Cron scheduling for 7 AM / 4 PM IST deliveries | Free tier; cron runs in UTC — 7 AM IST = `30 1 * * *` UTC, 4 PM IST = `30 10 * * *` UTC; add `workflow_dispatch` for manual testing; minimum interval is 5 minutes; **timing is approximate, not guaranteed** |
| Vercel (Python 3.12 runtime) | Host Telegram webhook endpoint | Free hobby tier; 10s timeout on hobby (sufficient for webhook acknowledgement — process async); FastAPI ASGI supported natively; max bundle 250MB unzipped |
| GitHub Secrets | Store API tokens and credentials | `TELEGRAM_BOT_TOKEN`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GMAIL_APP_PASSWORD` stored as repo secrets; mapped to env vars in workflow YAML |
| `EndBug/add-and-commit` action | Persist JSON state back to repo | Use for `data/seen_articles.json` (7-day dedup history) and `data/config.json` (user settings); commit after each run so next execution has fresh state |
| Gmail SMTP (`smtp.gmail.com:587`) | Email delivery | Use App Password (not account password); `smtplib` + `ssl.create_default_context()` + `MIMEMultipart("alternative")`; TLS on port 587; supports HTML + plaintext multipart |

---

## Installation

```bash
# Core runtime dependencies (requirements.txt for Vercel webhook)
pip install fastapi==0.133.1
pip install "python-telegram-bot[webhooks]==22.6"
pip install uvicorn[standard]  # local dev only, Vercel uses its own ASGI server

# Core runtime dependencies (requirements.txt for GitHub Actions aggregator)
pip install feedparser==6.0.12
pip install httpx==0.28.1
pip install anthropic==0.84.0
pip install google-genai==1.65.0
pip install newspaper4k==0.9.4.1
pip install pydantic==2.12.5
pip install Jinja2==3.1.6
pip install sentence-transformers  # pin to latest 3.x after testing
pip install python-dotenv==1.2.1

# Dev / test dependencies
pip install pytest
pip install pytest-asyncio==1.3.0
pip install uv  # install globally, not in requirements.txt
```

**Recommended: Use `uv` for dependency management**
```bash
# Install uv globally
pip install uv

# Initialize project
uv init
uv add fastapi "python-telegram-bot[webhooks]" feedparser httpx anthropic google-genai newspaper4k pydantic jinja2 python-dotenv sentence-transformers

# Dev deps
uv add --dev pytest pytest-asyncio
```

**GitHub Actions workflow snippet (uv-based):**
```yaml
- uses: astral-sh/setup-uv@v5
  with:
    enable-cache: true
    cache-dependency-glob: "uv.lock"
- name: Install dependencies
  run: uv sync
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| FastAPI | Flask | Only if you have no async handlers at all; Flask is WSGI-only, blocks on I/O — bad for concurrent RSS fetching |
| FastAPI | Bare `http.server.BaseHTTPRequestHandler` | Vercel supports it, but no routing, no validation — only for trivial single-endpoint use |
| python-telegram-bot v22 | aiogram v3 | aiogram is more performant for high-throughput bots (1000s of users); overkill for a 2-user bot; python-telegram-bot has better ConversationHandler for interactive menus |
| python-telegram-bot v22 | Telebot (pyTelegramBotAPI) | Less actively maintained; no async-first design; simpler API but less suitable for stateful conversations |
| google-genai (new SDK) | google-generativeai (old SDK) | **Do NOT use** — EOL November 30 2025; no longer receives updates or new features |
| sentence-transformers (local) | AI-based dedup via Claude/Gemini | LLM-based dedup is 100x more expensive per article; local embeddings are free, fast (~5ms/article), and sufficient for headline-level similarity |
| httpx | aiohttp | Both work; httpx is simpler API, already a transitive dep of anthropic SDK, supports sync+async in same library |
| uv | pip + pip-tools | pip works fine; uv is faster and provides proper lockfile; worth adopting for CI reproducibility |
| GitHub repo as data store | SQLite / PostgreSQL | A DB adds cost and complexity; for 7-day rolling JSON with <1000 entries, a committed JSON file in the repo is free and version-controlled |
| Gmail SMTP | Resend / SendGrid / Mailgun | Gmail SMTP is already configured per project context; Resend/SendGrid add cost and external dependencies; for 2-user delivery, Gmail App Password is entirely sufficient |
| feedparser | pygooglenews | pygooglenews wraps Google News RSS via feedparser — useful only if Google News is the only source; this project also uses curated RSS feeds, so direct feedparser is more flexible |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `google-generativeai` (pip package) | **EOL November 30 2025** — no new features, no support; accessing Gemini API with this package is a dead end | `google-genai` (new unified Google Gen AI SDK, GA since May 2025) |
| newspaper3k | Unmaintained since September 2020; Python 3.10+ incompatibilities; no bug fixes | `newspaper4k` — active fork with Python 3.10+ support, same API |
| polling mode for Telegram bot on Vercel | Polling requires a persistent long-running process — Vercel serverless functions terminate after each request; polling would constantly respawn and miss updates | Webhook mode only on Vercel; polling only for local development |
| APScheduler embedded in the Telegram webhook | Vercel serverless functions are stateless and ephemeral — a scheduler embedded in a Vercel function cannot maintain state between invocations | GitHub Actions `schedule` trigger for all cron tasks; Vercel is webhook-only |
| Hardcoded credentials in source | GitHub repo is version-controlled; credentials in source = permanent exposure risk | GitHub Secrets + `os.getenv()` in all environments |
| `asyncio.run()` in top-level GitHub Actions script | Creates event loop conflicts when mixing with python-telegram-bot's own loop management | Use `asyncio.run()` only in `__main__` blocks; keep async boundaries clean |
| Saving state only to GitHub Actions runner filesystem | Runner is ephemeral — all files are lost when the job completes | Commit state JSON files back to repo using `EndBug/add-and-commit` action |
| `requests` library for async operations | `requests` is synchronous; using it inside async code blocks the event loop | `httpx` (both sync and async clients) or standard `asyncio` with `httpx.AsyncClient` |

---

## Stack Patterns by Variant

**For scheduled delivery jobs (GitHub Actions):**
- Use: `feedparser` + `httpx.AsyncClient` for parallel feed fetching
- Use: `anthropic` batch API (`client.messages.batches.create()`) to process 15-50 articles in a single API call at 50% cost discount
- Use: `sentence-transformers` for local dedup before sending to AI (reduces tokens)
- Use: `Jinja2` + `smtplib` for email delivery

**For Telegram webhook (Vercel):**
- Use: `FastAPI` as ASGI app, single `api/index.py` entry point
- Use: `python-telegram-bot` Application in webhook mode, NOT polling
- Register webhook via: `https://your-app.vercel.app/webhook`
- Validate `X-Telegram-Bot-Api-Secret-Token` header on every incoming request
- Keep handler fast (<500ms): acknowledge immediately, defer heavy processing to GitHub Actions

**For local development:**
- Switch python-telegram-bot to polling mode (no webhook needed)
- Use `python-dotenv` to load `.env` file (same env var names as GitHub Secrets)
- Use `uvicorn api/index.py --reload` for Vercel FastAPI locally

**For the 7-day deduplication store:**
- Use a single `data/seen_articles.json` committed to repo
- Structure: `{"articles": [{"url": "...", "title_hash": "...", "seen_at": "ISO8601"}]}`
- Prune entries older than 7 days on every run before committing
- Use `EndBug/add-and-commit` at end of workflow to persist back

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| python-telegram-bot 22.6 | Python >=3.8 | httpx is a dep; requires `[webhooks]` extra for Tornado-based webhook support |
| FastAPI 0.133.1 | Python >=3.8, Pydantic v2 | Pydantic v2 is the default since FastAPI 0.100+; do not mix with Pydantic v1 |
| anthropic 0.84.0 | Python >=3.7; httpx ~0.28 | Async client available as `anthropic.AsyncAnthropic()`; uses httpx internally |
| google-genai 1.65.0 | Python >=3.9 | Replaces deprecated `google-generativeai`; different import paths: `from google import genai` |
| newspaper4k 0.9.4.1 | Python >=3.10 | Breaking: Python 3.8/3.9 no longer supported as of recent versions |
| pytest-asyncio 1.3.0 | Python >=3.10 | v1.0+ removed `event_loop` fixture; use `asyncio_mode = "auto"` in `pytest.ini` |
| Vercel Python runtime | Python 3.12 (default), 3.13, 3.14 | Pin via `.python-version` file at repo root |
| GitHub Actions | Python 3.10–3.13 via `actions/setup-python` | Use `python-version: "3.12"` to match Vercel |

---

## Architecture Fit Notes

- **Split deployment model**: The aggregator (feedparser + AI analysis + email) lives entirely in GitHub Actions. The Telegram webhook (receive commands + send notifications) lives on Vercel. These two components communicate via the shared GitHub repo JSON state.
- **Telegram bot for outbound delivery**: python-telegram-bot's `bot.send_message()` is called from the GitHub Actions job (not the Vercel webhook) for scheduled deliveries. The Vercel endpoint only receives inbound commands.
- **No database required**: All state (seen articles, user config, keyword lists) stored as JSON files in `data/` directory committed back to repo. This is viable because: (a) two users only, (b) data is <100KB, (c) GitHub provides version history for free.

---

## Sources

- PyPI — `anthropic` 0.84.0: https://pypi.org/project/anthropic/ — verified Feb 25 2026 release
- PyPI — `google-genai` 1.65.0: https://pypi.org/project/google-genai/ — verified Feb 26 2026 release; old SDK EOL confirmed
- PyPI — `python-telegram-bot` v22.6: https://github.com/python-telegram-bot/python-telegram-bot/releases — verified Jan 24 2026 release
- PyPI — `fastapi` 0.133.1: https://pypi.org/project/fastapi/ — verified Feb 25 2026
- PyPI — `feedparser` 6.0.12: https://pypi.org/project/feedparser/ — verified Sep 10 2025
- PyPI — `httpx` 0.28.1: https://pypi.org/project/httpx/ — verified stable release
- PyPI — `pydantic` 2.12.5: https://pypi.org/project/pydantic/ — verified Nov 26 2025
- PyPI — `newspaper4k` 0.9.4.1: https://pypi.org/project/newspaper4k/ — verified Nov 18 2025
- PyPI — `python-dotenv` 1.2.1 — verified Oct 26 2025
- Vercel Python Runtime docs: https://vercel.com/docs/functions/runtimes/python — Python 3.12 default, 3.13/3.14 available; confirmed FastAPI/ASGI support
- Vercel FastAPI docs: https://vercel.com/docs/frameworks/backend/fastapi — official framework guide
- GitHub Actions schedule docs: https://docs.github.com/actions/learn-github-actions/events-that-trigger-workflows — cron UTC, 5min minimum interval
- Anthropic Batch Processing: https://docs.claude.com/en/docs/build-with-claude/batch-processing — 50% discount on batch mode
- Google GenAI SDK deprecation notice: https://github.com/google-gemini/deprecated-generative-ai-python — EOL Nov 30 2025 confirmed
- uv GitHub Actions integration: https://docs.astral.sh/uv/guides/integration/github/ — official Astral docs
- python-telegram-bot webhook + Vercel: https://www.freecodecamp.org/news/how-to-build-and-deploy-python-telegram-bot-v20-webhooks/ — MEDIUM confidence (community article, pattern verified against official docs)
- Telegram X-Telegram-Bot-Api-Secret-Token: https://core.telegram.org/bots/api — official Telegram Bot API docs, header validation pattern
- EndBug/add-and-commit: https://github.com/EndBug/add-and-commit — v9, GitHub repo as JSON data store pattern

---
*Stack research for: Khabri — automated news aggregation with Telegram + GitHub Actions + Vercel + AI*
*Researched: 2026-02-26*
