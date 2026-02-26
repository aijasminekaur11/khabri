# Architecture Research

**Domain:** Automated news aggregation and delivery system (GitHub Actions + Python + Vercel + Telegram)
**Researched:** 2026-02-26
**Confidence:** HIGH (core patterns well-established; specific integration topology confirmed via official docs)

---

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CONTROL PLANE (Event-Driven)                     │
├─────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │           Vercel Serverless Function (/api/webhook)            │  │
│  │  Telegram Bot API  →  Command Parser  →  GitHub API Dispatch   │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                  │                                    │
│                    repository_dispatch (HTTP POST)                    │
│                                  ↓                                    │
├─────────────────────────────────────────────────────────────────────┤
│                     DATA PLANE (Scheduled / Triggered)               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │  GH Actions  │  │  GH Actions  │  │       GH Actions         │   │
│  │  Scheduled   │  │  on:dispatch │  │  Breaking News Watcher   │   │
│  │  (7AM/4PM    │  │  (bot cmds:  │  │  (on:schedule frequent   │   │
│  │  IST→UTC)    │  │  run-now,    │  │   polling, lighter job)  │   │
│  │              │  │  update-kw)  │  │                          │   │
│  └──────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘   │
│         └─────────────────┴──────────────────────┘                  │
│                                 │                                     │
│                                 ↓                                     │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                   Python Processing Pipeline                  │    │
│  │                                                               │    │
│  │  [Fetcher] → [Normalizer] → [Deduplicator] → [AI Analyzer]  │    │
│  │                                         ↓                    │    │
│  │  [Priority Filter] → [Story Selector] → [Formatter]         │    │
│  │                                         ↓                    │    │
│  │              [Telegram Sender] + [Gmail SMTP Sender]         │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                 │                                     │
├─────────────────────────────────────────────────────────────────────┤
│                      STORAGE LAYER (GitHub Repo Files)               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │  seen.json   │  │  config.json │  │   keywords.json          │   │
│  │  (7-day      │  │  (schedules, │  │   (categories, filters,  │   │
│  │  dedup hash  │  │  user prefs, │  │   geographic tiers)      │   │
│  │  store)      │  │  events)     │  │                          │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Vercel Webhook** | Receive Telegram updates, parse commands, dispatch to GitHub Actions via `repository_dispatch`, respond 200 immediately | Python FastAPI or raw WSGI in `/api/webhook.py`; runs in <1s (well within 10s Hobby timeout) |
| **GitHub Actions Scheduler** | Trigger processing pipeline on cron (7AM IST = 01:30 UTC, 4PM IST = 10:30 UTC); trigger on `repository_dispatch` for bot-driven runs | `.github/workflows/deliver.yml` with `on: [schedule, repository_dispatch]` |
| **Fetcher** | Pull articles from GNews.io API (≤100 req/day) and RSS feeds via `feedparser`; return raw article list with source metadata | `fetchers/gnews.py`, `fetchers/rss.py` |
| **Normalizer** | Standardize raw articles into unified schema: title, url, source, published_at, summary; strip HTML | `pipeline/normalizer.py` |
| **Deduplicator** | Compare against 7-day `seen.json` hash store using title fingerprint (SimHash/normalized title hash); discard seen items; append new hashes | `pipeline/deduplicator.py` |
| **AI Analyzer** | Classify each article HIGH/MEDIUM/LOW priority using Claude Sonnet (primary) or Gemini (fallback); extract key entities; assess geographic tier relevance | `pipeline/analyzer.py` using Anthropic Messages API |
| **Priority Filter + Story Selector** | Apply keyword relevance scoring, geographic tier rules, and AI priority; select top 15 stories | `pipeline/selector.py` |
| **Formatter** | Render stories into Telegram Markdown and Gmail HTML email templates | `pipeline/formatters/telegram.py`, `pipeline/formatters/email.py` |
| **Telegram Sender** | POST formatted message to Telegram Bot API for each user chat ID | `delivery/telegram.py` |
| **Gmail SMTP Sender** | Send formatted HTML email via `smtplib` with Gmail app password | `delivery/email.py` |
| **Config Store** | Read/write `data/config.json` (schedules, user prefs, active events) and `data/keywords.json` (keyword library with categories/tiers) | Python `json` module; GitHub Actions commits changes back via `git commit + push` |
| **Dedup Store** | Read/write `data/seen.json` (rolling 7-day title hash list); prune entries older than 7 days | Appended and trimmed each pipeline run |
| **Bot Command Interpreter** | In Vercel function: parse `/add_keyword`, `/remove_keyword`, `/status`, `/run_now`, `/schedule`, `/events` etc.; mutate config via GitHub API or `repository_dispatch` | Inline logic in webhook handler; uses `python-telegram-bot` or direct API calls |

---

## Recommended Project Structure

```
khabri/
├── .github/
│   └── workflows/
│       ├── deliver.yml          # Scheduled + dispatch: main pipeline
│       └── breaking.yml         # Frequent lightweight poller for breaking news
├── api/
│   └── webhook.py               # Vercel serverless entry point
├── pipeline/
│   ├── fetchers/
│   │   ├── gnews.py             # GNews.io API client
│   │   └── rss.py               # feedparser RSS/Atom client
│   ├── normalizer.py            # Unified article schema
│   ├── deduplicator.py          # Hash-based 7-day dedup
│   ├── analyzer.py              # Claude/Gemini AI classification
│   ├── selector.py              # Priority filter + top-15 selection
│   └── formatters/
│       ├── telegram.py          # Telegram Markdown renderer
│       └── email.py             # HTML email renderer
├── delivery/
│   ├── telegram.py              # Telegram Bot API sender
│   └── email.py                 # Gmail SMTP sender
├── bot/
│   └── commands.py              # Command parsing + GitHub API dispatch
├── data/
│   ├── config.json              # User prefs, schedules, events
│   ├── keywords.json            # Keyword library with categories/tiers
│   └── seen.json                # 7-day dedup hash store
├── requirements.txt
└── vercel.json                  # Routes /api/webhook
```

### Structure Rationale

- **`api/`:** Vercel convention — any file in `api/` becomes a serverless function automatically
- **`pipeline/`:** All data transformation logic isolated from delivery and I/O; testable in isolation
- **`delivery/`:** Separated from pipeline so formatters can be tested without sending; easy to add new channels
- **`bot/`:** Command logic decoupled from Vercel handler so it can be unit tested independently
- **`data/`:** All mutable state in one place; every pipeline run reads and commits back to this directory

---

## Architectural Patterns

### Pattern 1: Thin Webhook / Heavy Worker Separation

**What:** The Vercel webhook does the minimum possible — receive Telegram update, parse command intent, fire `repository_dispatch` to GitHub, return HTTP 200 in under 1 second. All heavy work (fetching, AI, sending) runs in GitHub Actions.

**When to use:** Always for this system. Vercel Hobby functions have a 10-second execution limit. AI classification + RSS fetching + email sending cannot complete in 10 seconds.

**Trade-offs:** Introduces async gap between user command and execution. Acceptable because Telegram users tolerate "queued" responses; bot replies "Running now, will deliver in ~2 minutes."

**Example:**
```python
# api/webhook.py — Vercel serverless function
import json, os, httpx
from telegram import Update

async def handler(request):
    body = await request.body()
    update = Update.de_json(json.loads(body), bot=None)

    if update.message and update.message.text.startswith("/run_now"):
        # Fire GitHub dispatch — do NOT wait for pipeline to complete
        httpx.post(
            f"https://api.github.com/repos/{OWNER}/{REPO}/dispatches",
            headers={"Authorization": f"Bearer {GH_TOKEN}"},
            json={"event_type": "run_now", "client_payload": {"user_id": str(update.message.chat_id)}}
        )
        await send_telegram_ack(update.message.chat_id, "Running now — brief incoming in ~2 min.")

    return Response(status_code=200)  # Must respond within 10s
```

---

### Pattern 2: GitHub Repo as Flat File Data Store

**What:** Store all mutable state (seen article hashes, config, keywords) as JSON files committed back to the repo after each pipeline run. Use `stefanzweifel/git-auto-commit-action` or inline `git commit && git push` in the workflow.

**When to use:** When cost is $0 and data volume is small (seen.json for 7 days of ~30 articles/day = ~210 entries, well under 1MB). Eliminates database entirely.

**Trade-offs:** Introduces git commit delay (~5-10s); concurrent runs can cause merge conflicts (mitigated by ensuring scheduled runs don't overlap — cron gaps are 6+ hours). Write operations are slow compared to a database but irrelevant at this scale.

**Example:**
```yaml
# .github/workflows/deliver.yml (post-pipeline step)
- name: Commit updated data files
  uses: stefanzweifel/git-auto-commit-action@v5
  with:
    commit_message: "chore: update seen.json and config after delivery run"
    file_pattern: "data/*.json"
```

---

### Pattern 3: AI Batch-per-Run (Not Per-Article)

**What:** Collect all new articles from a single run (typically 20-60 after dedup), then send them to Claude in one or two batched API calls rather than one API call per article. Use structured JSON output.

**When to use:** Always. Batching reduces API latency from N round trips to 1-2, and Claude's context window (200K tokens) easily handles 60 article titles + summaries in one call. Directly cuts costs toward the $1-4/month target.

**Trade-offs:** If Claude fails mid-batch, re-run costs full batch. Mitigated by Gemini fallback on error.

**Example:**
```python
# pipeline/analyzer.py
def classify_articles(articles: list[dict]) -> list[dict]:
    prompt = build_classification_prompt(articles)  # All articles in one prompt
    response = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    return parse_json_classifications(response.content[0].text)
```

---

### Pattern 4: Idempotent Pipeline with Title-Hash Deduplication

**What:** Every article is fingerprinted using a normalized title hash (lowercase, stripped punctuation, SimHash or SHA256 of first 80 chars). `seen.json` stores hashes with ISO timestamps. Before processing, filter against seen hashes. After delivery, append new hashes and prune entries older than 7 days.

**When to use:** Every run, unconditionally. Prevents duplicate delivery if GitHub Actions retries a failed run, or if the same story appears across GNews and RSS feeds simultaneously.

**Trade-offs:** Title normalization must handle minor variations ("Budget 2025: key highlights" vs "Budget 2025 - Key Highlights") — use lowercase + strip punctuation + first 60 characters as the hash key.

**Example:**
```python
# pipeline/deduplicator.py
import hashlib, re
from datetime import datetime, timedelta

def fingerprint(title: str) -> str:
    normalized = re.sub(r'[^\w\s]', '', title.lower())[:60].strip()
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]

def filter_seen(articles: list[dict], seen: dict) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(days=7)
    active_seen = {k: v for k, v in seen.items() if datetime.fromisoformat(v) > cutoff}
    return [a for a in articles if fingerprint(a['title']) not in active_seen], active_seen
```

---

## Data Flow

### Scheduled Delivery Flow (Primary)

```
GitHub Actions cron (01:30 UTC / 10:30 UTC)
    ↓
checkout repo (reads data/seen.json, data/config.json, data/keywords.json)
    ↓
Fetcher: GNews.io API + RSS feeds → raw articles (50-150 items)
    ↓
Normalizer: raw → unified schema (title, url, source, published_at, summary)
    ↓
Deduplicator: filter against seen.json → new articles only (20-60 items)
    ↓
AI Analyzer: Claude Sonnet batch call → HIGH/MEDIUM/LOW + entity tags
    │ (on error) → Gemini fallback
    ↓
Priority Filter + Selector: apply keyword/geo/tier rules → top 15 stories
    ↓
Formatter: render Telegram Markdown + HTML email
    ↓
Telegram Sender → User 1 chat + User 2 chat (sequential, same message)
Email Sender → User 1 Gmail + User 2 Gmail
    ↓
Dedup Store Update: append new hashes to seen.json, prune >7 days
    ↓
git commit data/seen.json → push to repo
```

---

### Bot Command Flow (Control Path)

```
User types /run_now or /add_keyword "metro expansion" in Telegram
    ↓
Telegram servers send HTTP POST to https://khabri.vercel.app/api/webhook
    ↓
Vercel serverless function (cold start <500ms, execution <3s)
    ↓
Command Parser: identify intent + extract args
    ↓  (for run_now / schedule changes)
GitHub API: POST /repos/{owner}/khabri/dispatches
    → event_type: "bot_command"
    → client_payload: {command: "run_now", user_id: "..."}
    ↓  (for keyword changes — lightweight, do inline)
GitHub Contents API: read data/keywords.json → mutate → commit back
    ↓
Telegram Bot API: send acknowledgment to user ("Done. Delivery queued.")
    ↓  (async — user doesn't wait for this)
GitHub Actions workflow triggered by repository_dispatch
    → runs full pipeline → delivers news
    → user receives brief in ~2 minutes
```

---

### Breaking News Alert Flow

```
GitHub Actions frequent cron (every 30-60 min, lightweight)
    ↓
Lightweight Fetcher: GNews.io only (1-2 API calls, no RSS)
    ↓
Breaking Filter: check for HIGH-priority keywords only (no AI call)
    → if score > threshold: trigger immediate delivery
    → else: exit (no cost incurred)
    ↓ (only if triggered)
AI Analyzer (single article, not batch) → confirm HIGH priority
    ↓
Telegram alert: "BREAKING: {title}" to both users
    ↓
Mark as seen to prevent duplicate in next scheduled run
```

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 2 users (current) | Monolithic pipeline, single GitHub Actions job, flat JSON files, no queue needed |
| 10-50 users | Replace flat JSON seen store with SQLite (still free via Turso/Cloudflare D1); add user-specific config per chat_id; Vercel webhook unchanged |
| 100+ users | Move pipeline to proper cloud worker (Railway, Fly.io); replace GitHub repo storage with proper DB; keep Vercel webhook as fan-out dispatcher |

### Scaling Priorities

1. **First bottleneck (at current scale):** GNews.io 100 req/day limit — at 2 runs/day + breaking news checks, exhausts ~10 API calls/day; remaining 90 available for RSS (unlimited) — not a bottleneck at current volume.
2. **Second bottleneck (if breaking news added):** GitHub Actions minutes — free tier is 2,000 min/month; 2 runs/day × 5 min = 300 min/month, well within limits; breaking news checks cost ~30s each = negligible.

---

## Anti-Patterns

### Anti-Pattern 1: Running Heavy Pipeline Inside Vercel Function

**What people do:** Put the entire news fetch + AI + email logic inside the Vercel webhook handler to "keep it simple."

**Why it's wrong:** Vercel Hobby functions time out at 10 seconds. A pipeline that fetches 10 RSS feeds, calls Claude, and sends email takes 45-120 seconds. This guarantees timeouts and lost deliveries.

**Do this instead:** Vercel webhook fires `repository_dispatch` and returns 200 immediately. All heavy work runs in GitHub Actions with no time pressure (jobs can run up to 6 hours on free tier).

---

### Anti-Pattern 2: One AI API Call Per Article

**What people do:** Loop through articles and call `claude.messages.create()` once per article for classification.

**Why it's wrong:** 60 articles × 1 API call = 60 round trips (each ~1-2s latency) = 60-120s just in AI calls. At $3/MTok, 60 individual calls also loses the benefit of shared system prompt context, increasing token usage.

**Do this instead:** Collect all articles for the run, format them into a single structured prompt, make 1-2 API calls. Claude 3.5 Sonnet handles 60 article titles + summaries easily within context limits.

---

### Anti-Pattern 3: Storing Seen-Articles State Only In Memory

**What people do:** Track deduplication state in a Python dict that exists only for the duration of the GitHub Actions run.

**Why it's wrong:** Each GitHub Actions job starts fresh with a new runner. The seen-state is lost between runs, causing the same articles to re-appear in every delivery brief.

**Do this instead:** Persist `data/seen.json` in the repo, read it at job start, write it back at job end using `stefanzweifel/git-auto-commit-action` or inline git commands.

---

### Anti-Pattern 4: Hardcoding User Chat IDs and Config in Code

**What people do:** Embed Telegram chat IDs, email addresses, keywords in the Python source files.

**Why it's wrong:** Makes bot commands (add keyword, change schedule) impossible — those commands must mutate config at runtime without a code deployment. Also exposes PII in public git history.

**Do this instead:** Store all user config in `data/config.json` (committed to repo but with no secrets). Secrets (Telegram token, GNews key, Gmail credentials) in GitHub Actions secrets and Vercel environment variables only.

---

### Anti-Pattern 5: Treating the Telegram Webhook as Synchronous

**What people do:** Make the Vercel function wait for the full pipeline result before responding to Telegram.

**Why it's wrong:** Telegram retries webhook delivery if it doesn't receive a 200 within 5 seconds. If the pipeline takes 2 minutes, Telegram will retry the webhook dozens of times, triggering duplicate pipeline runs.

**Do this instead:** Respond HTTP 200 to Telegram immediately (within 1-2s), then fire the async dispatch. Send a separate acknowledgment message to the user ("Brief incoming in ~2 min...") using the Telegram API before returning.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **Telegram Bot API** | Webhook (inbound to Vercel) + HTTP POST to `api.telegram.org` (outbound from GitHub Actions and Vercel) | Register webhook URL once after Vercel deploy: `setWebhook?url=https://khabri.vercel.app/api/webhook` |
| **GNews.io API** | REST GET with `apikey` param; 100 req/day on free tier | Batch keywords into fewer queries; use `q=keyword1 OR keyword2` to reduce request count |
| **RSS Feeds** | `feedparser.parse(url)` — synchronous pull, no auth needed | Use `feedparser` + `concurrent.futures.ThreadPoolExecutor` for parallel fetching of multiple feeds |
| **Anthropic Claude API** | `anthropic.Anthropic().messages.create()` | Store `ANTHROPIC_API_KEY` in GitHub Actions secrets; use `claude-sonnet-4-6` for primary; batch all articles per run |
| **Google Gemini API** | `google.generativeai.GenerativeModel.generate_content()` | Fallback only; triggered on Claude API error or rate limit |
| **Gmail SMTP** | `smtplib.SMTP_SSL("smtp.gmail.com", 465)` with app password | Store credentials in GitHub Actions secrets; `GMAIL_USER` + `GMAIL_APP_PASSWORD` |
| **GitHub API** | `POST /repos/{owner}/{repo}/dispatches` with `Authorization: Bearer {PAT}` | Vercel uses a Personal Access Token (PAT) scoped to `repo` for `repository_dispatch`; PAT stored in Vercel env vars |

---

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **Vercel webhook ↔ GitHub Actions** | `repository_dispatch` HTTP POST via GitHub REST API | Async: webhook fires and forgets; Actions picks up within ~30s |
| **Pipeline ↔ Data Store** | Direct file read/write (`json.load` / `json.dump`) within same GitHub Actions job | Atomic: read at job start, write at job end; no concurrent access risk at 2x daily cadence |
| **Fetcher ↔ Normalizer** | In-process Python function call, returns `list[dict]` | No queue needed; pipeline runs sequentially in a single process |
| **Analyzer ↔ Selector** | In-process: analyzer returns articles enriched with `priority` and `tags` fields; selector consumes these | Keep analyzer output schema stable: `{..., "priority": "HIGH|MEDIUM|LOW", "tags": [...]}` |
| **Pipeline ↔ Delivery** | In-process: pipeline calls delivery functions with formatted content | Delivery layer is stateless — receives rendered strings, sends, returns success/failure |
| **Bot commands ↔ Config store** | Vercel function reads/writes `data/config.json` + `data/keywords.json` via GitHub Contents API | For simple keyword adds: inline in webhook. For schedule changes triggering immediate run: use `repository_dispatch` |

---

## Suggested Build Order

The component dependency graph determines safe build order. Each phase should be independently deployable and testable before the next begins.

**Phase 1 — Data Foundation (no external dependencies)**
Build first because all other components read from or write to these files.
- Define JSON schemas for `config.json`, `keywords.json`, `seen.json`
- Implement `deduplicator.py` (pure Python, no external APIs)
- Set up GitHub Actions skeleton workflow (checkout + setup Python + commit-back)

**Phase 2 — Fetching Layer (GNews + RSS)**
Build second because it feeds all downstream processing.
- `fetchers/gnews.py` with GNews.io API client
- `fetchers/rss.py` with feedparser + parallel fetch
- `pipeline/normalizer.py` to unified schema
- Integration test: fetch → normalize → print to stdout

**Phase 3 — AI Analysis + Delivery Pipeline**
Build third because it depends on normalized articles from Phase 2.
- `pipeline/analyzer.py` (Claude primary + Gemini fallback)
- `pipeline/selector.py` (priority filter + top-15 selection)
- `pipeline/formatters/telegram.py` + `formatters/email.py`
- `delivery/telegram.py` + `delivery/email.py`
- End-to-end test: fetch → analyze → select → format → deliver

**Phase 4 — GitHub Actions Scheduling**
Build fourth after the pipeline is proven.
- `.github/workflows/deliver.yml` with `on: schedule` cron (01:30 UTC, 10:30 UTC)
- Wire Phase 3 pipeline as `python -m pipeline.run`
- Add `stefanzweifel/git-auto-commit-action` to commit `data/seen.json`
- Smoke test: manually trigger `workflow_dispatch`, verify delivery

**Phase 5 — Vercel Webhook + Bot Commands**
Build last because it depends on all prior components being stable.
- `api/webhook.py` (receive Telegram updates, parse commands, return 200)
- `bot/commands.py` (command intent parsing, GitHub dispatch, config mutation)
- Register Telegram webhook URL with Bot API
- Add `on: repository_dispatch` trigger to deliver workflow
- End-to-end test: send `/run_now` → verify pipeline triggers → verify delivery

**Phase 6 — Breaking News + Event Scheduling (enhancement)**
Build after core is validated.
- `.github/workflows/breaking.yml` with 30-60 min cron
- Event-based scheduling logic in `config.json` + pipeline conditional logic

---

## Sources

- [GitHub Actions Data Pipeline Documentation](https://actions-pipeline.readthedocs.io/en/latest/) — MEDIUM confidence
- [Automating Data Pipelines with Python & GitHub Actions](https://towardsdatascience.com/automating-data-pipelines-with-python-github-actions-c19e2ef9ca90/) — MEDIUM confidence
- [GitHub Actions: Run a Python script on schedule and commit changes](https://canovasjm.netlify.app/2020/11/29/github-actions-run-a-python-script-on-schedule-and-commit-changes/) — MEDIUM confidence
- [Serverless Telegram Bot on Vercel](https://www.marclittlemore.com/serverless-telegram-chatbot-vercel/) — HIGH confidence (verified against Vercel behavior)
- [python-telegram-bot Architecture Wiki](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Architecture) — HIGH confidence (official library docs)
- [python-telegram-bot Webhooks Wiki](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks) — HIGH confidence (official library docs)
- [Vercel Limits — Official Docs](https://vercel.com/docs/limits) — HIGH confidence (official, 10s Hobby function timeout confirmed)
- [Using GitHub as a Flat Data Store](https://tryexceptpass.org/article/using-github-as-flat-data-store/) — MEDIUM confidence
- [How to Trigger GitHub Actions Remotely Using Webhooks](https://www.howtogeek.com/devops/how-to-trigger-github-actions-remotely-using-webhooks/) — MEDIUM confidence
- [Idempotency in Data Pipelines](https://airbyte.com/data-engineering-resources/idempotency-in-data-pipelines) — MEDIUM confidence
- [Anthropic Message Batches API](https://www.anthropic.com/news/message-batches-api) — HIGH confidence (official Anthropic docs)
- [AI Batch Processing: OpenAI, Claude, and Gemini (2025)](https://adhavpavan.medium.com/ai-batch-processing-openai-claude-and-gemini-2025-94107c024a10) — MEDIUM confidence

---
*Architecture research for: Automated news aggregation + delivery system (Khabri)*
*Researched: 2026-02-26*
