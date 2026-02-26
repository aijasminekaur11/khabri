# Pitfalls Research

**Domain:** Automated news aggregation system — Indian infrastructure/real estate domain
**Researched:** 2026-02-26
**Confidence:** MEDIUM-HIGH (WebSearch verified against official docs where possible)

---

## Critical Pitfalls

### Pitfall 1: GitHub Actions Scheduled Workflows Silently Die After 60 Days of Inactivity

**What goes wrong:**
GitHub automatically disables scheduled (cron-based) workflows when no commit activity has occurred in the repository for 60 days. Since Khabri's core data is stored in the repo itself (JSON history files committed by the Actions workflow), the workflow commits will satisfy the activity requirement during normal operation. However, if the system ever needs to stop committing (e.g., no new news, quiet periods, or bugs that prevent commits), the scheduled trigger silently disables itself. There is no email alert or bot notification — the cron just stops running.

**Why it happens:**
GitHub introduced this policy to prevent runaway abandoned repo workflows consuming their free runner capacity. It targets exactly the pattern Khabri uses: a scheduled workflow on a repo that may have periods of low human activity.

**How to avoid:**
- Add a dedicated "keepalive" workflow (using `gautamkrishnar/keepalive-workflow` from GitHub Marketplace) that makes a dummy commit or pings the GitHub API every 50 days.
- Alternatively, ensure the main workflow always makes a commit (even if it's a no-new-news status update), which counts as repository activity.
- Monitor Telegram delivery — if deliveries stop without bot error messages, check if the workflow is disabled in GitHub Actions UI.

**Warning signs:**
- Scheduled Telegram deliveries stop arriving silently.
- No error messages in Telegram — the workflow never started.
- GitHub Actions tab shows the workflow as "disabled."
- Last successful run was 60+ days ago.

**Phase to address:**
Phase 1 (core scheduling infrastructure). Build the keepalive mechanism before deploying the production schedule.

---

### Pitfall 2: GNews.io 100-Request Daily Quota Exhaustion Within a Single Run

**What goes wrong:**
GNews.io free tier provides 100 requests per day, reset at 00:00 UTC. Khabri's keyword library covers Infrastructure, Authorities/Regulatory, and Celebrity real estate — potentially 30-60 distinct keyword categories. If each keyword category triggers a separate API call, a single morning run could exhaust the entire day's quota before the 4 PM delivery runs. The API returns HTTP 403 after quota exhaustion with no partial results.

**Why it happens:**
Developers treat keyword searches as independent queries (one per keyword) rather than designing compound Boolean queries. GNews.io supports AND/OR/NOT operators in a single request, but this requires intentional query design upfront.

**How to avoid:**
- Design keyword groups using GNews.io's Boolean operators: combine related terms into one query (e.g., `"metro rail" OR "DMRC" OR "NMRC" OR "metro expansion"` is one request, not four).
- Target maximum 20-30 API calls per combined run (morning + evening), leaving 70+ requests as buffer.
- Cache GNews results per keyword group for both the 7 AM and 4 PM runs — use the morning call's results for the evening run with a timestamp filter instead of re-querying.
- Implement a daily quota tracker (stored in the repo's JSON state file) that prevents calls if fewer than 10 requests remain, falling back to RSS feeds only.

**Warning signs:**
- 4 PM delivery arrives with noticeably fewer articles than the 7 AM delivery.
- Logs show HTTP 403 errors from GNews mid-workflow.
- Daily request counter (if tracked) shows 80+ calls before noon.

**Phase to address:**
Phase 1 (data ingestion design). Query budget must be designed before writing fetch code, not retrofitted.

---

### Pitfall 3: GitHub Actions Cron Timing Drift — IST Deliveries Arrive Late or Wrong Day

**What goes wrong:**
GitHub Actions runs all cron schedules in UTC only. Deliveries targeted at 7 AM IST (01:30 UTC) and 4 PM IST (10:30 UTC) can drift by 15-30 minutes during high-load periods on GitHub's runners. During Daylight Saving Time transitions in countries where users may travel, IST (UTC+5:30) does not change — but mental models built around UTC offsets can produce wrong cron expressions that schedule runs on the wrong calendar day. The most common mistake: `30 20 * * *` instead of `30 1 * * *` for 7 AM IST, especially when working from local machine time.

**Why it happens:**
- GitHub does not support timezone configuration in scheduled workflows (only UTC).
- Runners queue cron jobs, and execution happens when a runner is available — not at the exact scheduled second.
- IST is UTC+5:30 (half-hour offset), which is non-intuitive and produces non-round UTC times.
- IST does not observe Daylight Saving Time, so no seasonal adjustment is needed — but developers from DST-observing regions incorrectly apply DST logic.

**How to avoid:**
- Document the UTC-to-IST conversion prominently in the workflow YAML as a comment:
  ```yaml
  # 7 AM IST = 01:30 UTC (IST = UTC+5:30, no DST)
  # 4 PM IST = 10:30 UTC
  - cron: '30 1 * * *'   # 7 AM IST
  - cron: '30 10 * * *'  # 4 PM IST
  ```
- Accept up to 30 minutes of drift as normal — do not build logic that depends on the workflow running at exactly 01:30:00 UTC.
- In Python code, always use `Asia/Kolkata` (not `Asia/Calcutta`, which is deprecated) via `zoneinfo` (Python 3.9+ standard library) or `pytz`. Never use fixed UTC offsets like `timedelta(hours=5, minutes=30)` — use named timezone objects.

**Warning signs:**
- Deliveries consistently arrive 25-35 minutes after the expected IST time.
- On certain days, a delivery is missing and a duplicate arrives the next day (day boundary miscalculation in UTC cron).
- Timestamps in news summaries show "Tomorrow's" date in IST despite being correct in UTC.

**Phase to address:**
Phase 1 (scheduler setup). Validate cron expressions against a UTC-to-IST converter before deploying. Add timezone assertions in Python code as unit tests.

---

### Pitfall 4: Vercel Serverless Cold Starts Causing Telegram Webhook Timeouts

**What goes wrong:**
Telegram's webhook system has a hard requirement: the webhook endpoint must respond with HTTP 200 within 5-10 seconds or Telegram marks the delivery as failed and retries. Vercel serverless functions on the free (Hobby) tier have cold start delays of 2-3 seconds for Python runtimes. When a user sends a Telegram command that triggers the webhook handler (which then calls an external API or performs processing), the combined cold start + processing time exceeds 5 seconds, causing Telegram to retry the webhook — potentially triggering duplicate command processing.

**Why it happens:**
- Vercel spins down functions after inactivity periods (serverless model).
- Python has a heavier cold start than Node.js on serverless platforms.
- Telegram's retry behavior on timeout creates a cascade: the same message is sent 2-3 times before the function finally responds.

**How to avoid:**
- Implement the "immediate acknowledgment" pattern: return HTTP 200 to Telegram instantly upon receiving the webhook, then process the command asynchronously.
  ```python
  # In Vercel handler: acknowledge immediately
  def handler(request):
      # Dispatch to background processing queue
      process_command_async(request.json)
      return Response("OK", status=200)  # Return before processing
  ```
- Since true async background processing is difficult in Vercel's stateless model, use a simpler approach: validate the command format in under 1 second, send an immediate "Processing..." message to the user via Telegram API, then complete the actual work.
- Add idempotency keys to prevent duplicate processing: check if the `update_id` from Telegram has already been processed (store in the repo's JSON state file or use Telegram's `update_id` ordering).

**Warning signs:**
- Users see duplicate responses to single commands ("I received two summaries when I asked for one").
- Vercel function logs show multiple calls with the same `update_id` within 30 seconds.
- Telegram's `getWebhookInfo` shows `last_error_message: "Wrong response from the webhook"`.

**Phase to address:**
Phase 2 (Telegram bot and webhook setup). Design the immediate-acknowledge pattern before building any command handlers.

---

### Pitfall 5: AI Cost Overrun from Unbounded Token Consumption

**What goes wrong:**
Each news cycle fetches up to 60+ articles (RSS + GNews combined). If all article full-text is passed to Claude for classification and deduplication without token management, a single run can consume 50,000-200,000 input tokens. At Claude Sonnet 3.7's pricing (~$3/million input tokens standard, $1.50/million with batch), two runs per day for 30 days = 60 runs × 100,000 tokens average = 6 million tokens = ~$9-18/month — well above the <$5/month budget.

**Why it happens:**
- RSS feeds often return full article text in the `<content>` field, not just headlines and summaries.
- Developers pass the full feed content to the AI without truncating to headline + first 200 words.
- Without prompt caching, the system prompt (which includes keyword lists, classification rules, geographic tier logic) is re-sent on every API call, consuming 2,000-5,000 tokens per request as non-cached overhead.

**How to avoid:**
- Truncate each article to: `title + source + published_date + first_150_words` before passing to AI. Full text is not needed for priority classification.
- Use Anthropic's Message Batches API (50% cost reduction) for non-time-sensitive classification tasks — submit all articles in a single batch rather than one API call per article.
- Use prompt caching: place the static system prompt (keyword library, classification rules, geographic tiers) at the top of every request so it gets cached after the first call (90% cost reduction on repeated context).
- Set a hard token budget per run: if total input tokens exceed 80,000, skip lowest-priority source categories and log a warning.
- Track cumulative monthly AI spend in the repo's JSON state file and alert via Telegram if it approaches $4.

**Warning signs:**
- Monthly Anthropic API invoice significantly exceeds $2.
- Individual run logs show input token counts above 50,000.
- Processing time per run exceeds 2 minutes (indicates too many sequential API calls).

**Phase to address:**
Phase 2 (AI classification pipeline). Token budgeting must be designed before the classification loop, not optimized after costs appear.

---

### Pitfall 6: Duplicate Detection Failing for Same-Story Variants from Indian Sources

**What goes wrong:**
Indian news aggregation is plagued by wire service republication: PTI (Press Trust of India) and ANI (Asian News International) feed the same story verbatim to Economic Times, Times of India, Business Standard, Hindustan Times, and NDTV simultaneously. These appear as 5 distinct articles with identical content but different URLs, authors, and sometimes slightly different headlines. Simple URL-based deduplication misses these entirely. Cosine similarity on full text catches them, but requires embedding inference, which adds latency and cost. A 0.95 similarity threshold that works for English Reuters content over-matches for Indian real estate news where legitimate stories about different projects share many domain-specific terms (RERA, PMAY, metro, crore, BHK).

**Why it happens:**
- Indian news ecosystem is heavily dependent on PTI/ANI wire services — virtually all major outlets republish wire stories.
- Real estate and infrastructure vocabulary is narrow: "RERA approval," "metro corridor," "crore investment," "Tier 1 city" appear across all genuine articles, inflating false-positive similarity scores.
- Title-only comparison fails when outlets rewrite PTI headlines but keep body text identical.

**How to avoid:**
- Use a two-stage deduplication strategy:
  1. **Fast stage (title hash):** Normalize title (lowercase, remove punctuation, sort words), compute hash. Deduplicate identical hashes first.
  2. **Semantic stage (embedding similarity):** Only run embedding comparison on articles that pass stage 1. Use headline + first_paragraph embeddings, not full text.
- Set a project-specific similarity threshold of 0.85-0.90 (not the generic 0.95) for this domain, accounting for shared real estate vocabulary.
- Add a "wire service" detection heuristic: if the same story appears from 3+ sources within 2 hours, keep only the highest-domain-authority version (e.g., prefer Economic Times over a local aggregator).
- Store seen articles as a 7-day rolling hash file in the repo (title hash + URL hash). Reset weekly to avoid unbounded file growth.

**Warning signs:**
- Users complain about receiving the same story 3-4 times in a single digest.
- Deduplication logs show very few articles being filtered (under 10%) — suggests duplication is not being caught.
- OR: too many articles being filtered (over 60%) — suggests threshold is too aggressive for this domain.

**Phase to address:**
Phase 2 (deduplication pipeline). The two-stage approach must be validated with real PTI/ANI stories before going to production.

---

### Pitfall 7: RSS Feed Unreliability from Indian Sources

**What goes wrong:**
Several major Indian news RSS feeds exhibit domain-specific reliability issues:

- **Economic Times** RSS entries often contain only headlines and 1-2 sentence teasers, with full content behind a soft paywall requiring JavaScript rendering.
- **Times of India** and **Hindustan Times** RSS feeds periodically return malformed XML (unclosed tags, illegal characters in article titles containing quotes or Hindi diacritics mixed with ASCII).
- **feedparser** (the standard Python RSS library) silently marks malformed feeds as `bozo=True` but still returns partial data — entries may have missing `published` dates, empty `summary` fields, or corrupt `title` encoding.
- Some Indian feeds block requests using Python's default `urllib` user-agent (returns HTTP 406), while the same feed works with a browser or `requests` library with a browser-mimicking user-agent.
- Feeds can hang indefinitely — `feedparser.parse()` has no built-in timeout, causing GitHub Actions jobs to run until they hit the 6-hour hard kill.

**Why it happens:**
- Indian news sites have inconsistent RSS implementation maturity — RSS is maintained as a secondary feature, not a primary product.
- Some sites use UTF-8 with BOM, or mix Devanagari in otherwise ASCII feeds, producing XML that violates the RSS spec.
- Aggressive CDN/WAF configurations at large Indian media groups block automated requests.

**How to avoid:**
- Always wrap `feedparser.parse()` with a timeout using the `requests` library as the transport layer:
  ```python
  import requests, feedparser
  response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0 ..."})
  feed = feedparser.parse(response.content)
  if feed.bozo:
      log.warning(f"Malformed feed: {url} — {feed.bozo_exception}")
  ```
- Check `bozo` flag and log a warning rather than silently skipping.
- For each RSS source, test encoding, timeout behavior, and user-agent requirements during Phase 1 before committing to that source in production.
- Always set a `published_parsed` fallback: if `entry.published_parsed` is None, use `datetime.utcnow()` minus 1 hour as the assumed publish time.
- Maintain a "feed health" tracker in the JSON state file: count consecutive failures per feed, and if a feed fails 3 consecutive runs, send a Telegram alert and temporarily disable it.

**Warning signs:**
- A GitHub Actions run takes more than 3 minutes for the fetch phase (feed hang).
- Logs show articles with publish dates in 1970 (Unix epoch 0 — missing date parsed as epoch).
- The same source consistently contributes 0 articles despite being in the active feed list.

**Phase to address:**
Phase 1 (data ingestion). Feed testing with real Indian sources before building the full pipeline.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| One GNews query per keyword (no Boolean grouping) | Simple code to write | Quota exhausted in hours; system degrades silently | Never — design queries with Boolean operators from the start |
| Pass full RSS article content to AI without truncation | No extra preprocessing code | AI costs 3-5x higher than necessary | Never for production; OK for initial prototyping if you cap test runs |
| Skip the `bozo` flag check in feedparser | Fewer lines of code | Silent data loss when Indian feeds serve malformed XML | Never — add `bozo` check in the same step as parsing |
| Hardcode UTC offset (+5:30) instead of using timezone library | Quicker to write | Breaks if Python version changes; invisible bugs when timestamps cross midnight | Never — use `zoneinfo.ZoneInfo("Asia/Kolkata")` always |
| Store deduplication history as an ever-growing flat file | Simple append logic | File grows unbounded; git history bloats; Actions checkout time increases | Only if bounded — enforce a 7-day rolling window with weekly cleanup |
| Run AI classification on every article including obvious irrelevant ones | Simplest loop | Wastes tokens on clearly off-topic articles | Add a fast keyword pre-filter before AI calls to drop obvious non-matches |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| GNews.io API | Call API once per keyword (30+ calls) | Group keywords into Boolean OR queries; max 15-20 calls per run |
| GNews.io API | Assume response includes full article text | Free tier returns title + description only; use RSS for article body |
| feedparser + Indian RSS | Trust `feedparser.parse(url)` with no timeout | Use `requests.get(url, timeout=10)` as transport, pass `response.content` to feedparser |
| Telegram webhook + Vercel | Process command synchronously before returning 200 | Return 200 immediately, send "Processing..." message, then complete work |
| Telegram Bot API | Send all 15 stories in a single Telegram message | Telegram has a 4096-character message limit; split into chunks or use multiple messages |
| Anthropic Claude API | Send one API call per article | Use Message Batches API for bulk classification; one batch per run cycle |
| GitHub Actions + git commit | Commit on every run even when nothing changed | Only commit when state files actually change; empty commits bloat history |
| Gmail SMTP | Open/close SMTP connection per email | Reuse one SMTP connection for both recipients; `smtplib.SMTP_SSL` context manager |
| Gmail SMTP | No retry logic | Gmail occasionally returns 421 (too many connections); add exponential backoff with 3 retries |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Sequential RSS feed fetching (one at a time) | Fetch phase takes 5+ minutes for 20 feeds | Use `asyncio` + `aiohttp` or `concurrent.futures.ThreadPoolExecutor` for parallel feed fetching | As soon as you add more than 5 RSS sources |
| Fetching full articles via HTTP for AI summarization | Run time balloons; costs spike | Use RSS summary + title only for classification; only fetch full text if truly needed | At 10+ sources simultaneously |
| Re-embedding all 7-day history for similarity check on every run | Run time grows linearly with history size | Pre-compute embeddings; store them in JSON history file alongside titles | At approximately 500+ stored articles in the 7-day window |
| Synchronous Telegram API calls in a loop for 15 articles | User experiences 15+ second delay before messages arrive | Use `asyncio` with `python-telegram-bot`'s async send methods | Every time you have more than 3 messages to send |
| GitHub Actions checkout of large repo on every run | Workflow startup takes 60+ seconds | Keep the repo lean; use `fetch-depth: 1` for shallow clone in workflow YAML | When deduplication JSON history exceeds 5MB |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing API keys in GitHub Actions workflow YAML files | Keys visible in repo history; compromised if repo ever goes public | Store all secrets in GitHub Repository Secrets; reference as `${{ secrets.KEY_NAME }}` |
| Storing API keys in the JSON state/history files committed to the repo | Keys committed to version control permanently | State files contain only news data — no credentials ever |
| No Telegram bot token validation on webhook | Anyone who discovers the webhook URL can send commands | Validate that incoming webhook `message.chat.id` matches the authorized user IDs before processing |
| Sending internal error tracebacks to Telegram chat | Exposes system internals, file paths, and API key patterns in error messages | Catch all exceptions; send sanitized user-friendly error messages to Telegram; log full traceback only to GitHub Actions logs |
| Using Gmail password directly in code/environment | Password exposure risk; Google now requires App Passwords for SMTP | Use Gmail App Password (16-character generated password), not the account password |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Sending 15 stories as one wall-of-text Telegram message | Unreadable; users stop engaging | Format as numbered list with clear HIGH/MEDIUM/LOW priority labels; use Telegram's MarkdownV2 formatting |
| No indication that a Telegram command was received | Users repeatedly send the same command, thinking it didn't work | Always send an immediate acknowledgment ("Got it, fetching news...") before processing begins |
| Delivering news at exact IST times even during GitHub cron drift | Users expect 7 AM delivery; it arrives at 7:28 AM | Set user expectations: "delivered around 7 AM IST" — don't promise exact times |
| Breaking news alerts for every HIGH priority story without rate limiting | Alert fatigue; users mute the bot | Batch breaking news: send at most one breaking alert per hour; queue multiple breaking stories |
| Error messages that say "Something went wrong" with no actionable info | Users don't know if news was delivered or not | Include: what failed, whether they'll still get news from other sources, and when to expect the next scheduled delivery |
| Monthly/weekly stats with no baseline comparison | Numbers are meaningless without context | Always show delta: "This week: 42 stories (vs 38 last week)" |

---

## "Looks Done But Isn't" Checklist

- [ ] **Telegram delivery:** Test with BOTH users (chat IDs), not just the developer's Telegram account — verify both receive messages independently.
- [ ] **IST timezone display:** Verify that article timestamps shown in digests display as IST, not UTC — a digest showing "3:30 AM" for a 9 AM IST article confuses users.
- [ ] **7-day deduplication:** Verify that an article seen Monday does NOT appear in Wednesday's digest — test with deliberately repeated test articles.
- [ ] **Gmail delivery:** Check that HTML email renders correctly in Gmail app on mobile (Indian users predominantly use mobile Gmail) — not just desktop web.
- [ ] **GitHub Actions cron:** Confirm workflow actually runs on time by checking the Actions tab on the first 3 scheduled runs — drift behavior varies by time of day.
- [ ] **GNews quota:** After a full day of real operation, check how many of the 100 daily requests were consumed — if above 70, redesign query grouping.
- [ ] **AI cost:** After first week of production operation, calculate actual token consumption vs. estimated — AI costs almost always exceed initial estimates.
- [ ] **Feed health:** Verify that every RSS feed in the configured list actually returns data — dead feeds are common and easy to miss.
- [ ] **Breaking news:** Verify the breaking news alert path works independently of the scheduled delivery path — they share code but should be tested separately.
- [ ] **Duplicate handling:** Confirm that the same PTI story appearing in ET, TOI, and Business Standard simultaneously counts as ONE story in the digest.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| GitHub scheduled workflow disabled after 60 days | LOW | Re-enable via GitHub Actions UI (one click); add keepalive workflow before next deployment |
| GNews quota exhausted mid-run | LOW | System falls back to RSS-only for remainder of day; next day quota resets at 00:00 UTC; no user action needed if fallback is coded |
| AI cost overrun discovered after one month | MEDIUM | Audit token logs to find which articles/prompts consume most; add truncation and batching; retroactive cost is sunk |
| Telegram webhook loop (duplicate processing) | MEDIUM | Add `update_id` deduplication check; redeploy Vercel function; retroactive duplicates already sent cannot be recalled |
| RSS deduplication history file grown too large | MEDIUM | Prune JSON file to last 7 days; force-push cleaned version; rebuild from recent runs |
| Critical IST timezone bug (wrong delivery day) | MEDIUM | Fix cron expression and UTC conversion in Python; validate with test runs before re-enabling production schedule |
| Vercel function cold start causing webhook 504s | HIGH | Migrate Telegram bot to polling mode (GitHub Actions long-poll job) instead of webhook; requires architecture change |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| GitHub 60-day workflow disable | Phase 1: Core infrastructure | Keepalive workflow deployed; test by manually disabling and re-enabling |
| GNews quota exhaustion | Phase 1: Data ingestion design | Query design targets <25 calls/run; tested against live API for 3 days |
| IST/UTC cron drift | Phase 1: Scheduler setup | Cron expressions documented with IST equivalents; Python timezone uses `Asia/Kolkata` |
| Vercel cold start webhook timeout | Phase 2: Telegram bot setup | Immediate-acknowledge pattern implemented; tested with `curl` before bot integration |
| AI cost overrun | Phase 2: AI classification pipeline | Token budgeting coded; batch API used; first-week cost monitored |
| Duplicate detection failure | Phase 2: Deduplication pipeline | Two-stage dedup tested with real PTI/ANI story set across 3+ sources |
| RSS feed unreliability | Phase 1: Data ingestion | Each configured feed tested individually with timeout + bozo checks |
| Gmail SMTP limits | Phase 3: Email delivery | App Password configured; connection reuse tested; retry logic present |
| Telegram message length limits | Phase 2: Delivery formatting | 15-story digest verified to split correctly at 4096 character boundary |
| Deduplication history file growth | Phase 2: State management | 7-day rolling window enforced; file size checked after first week |

---

## Sources

- [GitHub Actions: Scheduled workflow disable after 60 days](https://github.com/orgs/community/discussions/86087) — MEDIUM confidence (community discussion, confirmed by multiple reports)
- [GitHub Actions cron delay of 15-30 minutes](https://github.com/orgs/community/discussions/156282) — MEDIUM confidence (community discussion)
- [GNews.io free tier: 100 requests/day, HTTP 403 on exceed](https://docs.gnews.io/) — HIGH confidence (official documentation)
- [GNews.io free plan: no full article content](https://gnews.io/pricing) — HIGH confidence (official pricing page)
- [feedparser hanging without timeout](https://github.com/kurtmckee/feedparser/issues/263) — MEDIUM confidence (official repo issue)
- [feedparser bozo flag and malformed feed behavior](https://pythonhosted.org/feedparser/) — HIGH confidence (official documentation)
- [Vercel serverless cold start 2-3 seconds](https://github.com/vercel/vercel/discussions/7961) — MEDIUM confidence (community discussion)
- [Vercel free tier 10-second function timeout](https://vercel.com/kb/guide/what-can-i-do-about-vercel-serverless-functions-timing-out) — HIGH confidence (official Vercel knowledge base)
- [Telegram webhook 5-10 second response requirement](https://grammy.dev/hosting/vercel) — HIGH confidence (official grammY framework docs)
- [Telegram flood control: 1 message/second limit, 429 on exceed](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Avoiding-flood-limits) — HIGH confidence (official python-telegram-bot wiki)
- [Anthropic Message Batches API: 50% cost reduction](https://www.anthropic.com/news/message-batches-api) — HIGH confidence (official Anthropic announcement)
- [Claude Sonnet pricing + prompt caching up to 90% reduction](https://platform.claude.com/docs/en/about-claude/pricing) — HIGH confidence (official Claude pricing docs)
- [Gmail SMTP free account: 100 emails/day automated limit](https://support.google.com/mail/answer/22839) — HIGH confidence (official Gmail help)
- [feedparser user-agent blocking (HTTP 406)](https://github.com/kurtmckee/feedparser/issues/263) — LOW confidence (single issue report, unverified at scale)
- [PTI/ANI wire service cross-publication behavior](https://www.newscatcherapi.com/docs/v3/documentation/guides-and-concepts/articles-deduplication) — MEDIUM confidence (official NewsCatcher API deduplication docs)
- [Keyword false positives in news matching](https://amlwatcher.com/blog/5-keyword-search-challenges-in-negative-news-screening/) — MEDIUM confidence (domain-specific but non-news-aggregation context)
- [zoneinfo recommended over pytz in Python 3.9+](https://pypi.org/project/pytz/) — HIGH confidence (official pytz PyPI page recommends migration)

---
*Pitfalls research for: Khabri — automated news aggregation, Indian infrastructure/real estate domain*
*Researched: 2026-02-26*
