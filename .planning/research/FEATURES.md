# Feature Research

**Domain:** Automated news aggregation and curated delivery — Indian infrastructure & real estate
**Researched:** 2026-02-26
**Confidence:** MEDIUM-HIGH (table stakes from multiple verified sources; differentiators from competitor analysis + domain reasoning)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| RSS feed fetching | Core of any aggregator; industry standard since Google Reader era | LOW | feedparser (Python) is battle-tested; handle feed timeouts, malformed XML gracefully |
| News API integration (GNews.io) | Extends reach beyond RSS-only sources; covers outlets without public feeds | LOW | GNews free tier: 100 req/day hard cap; must be budgeted carefully across scheduled runs |
| Keyword-based filtering | Users must be able to define what's relevant; no filter = noise flood | MEDIUM | Multi-keyword matching with AND/OR logic; Indian domain requires Hinglish-aware matching (e.g., "crore" alongside "RERA") |
| Duplicate article detection | Without dedup, same story appears 4-8x from different outlets; degrades trust immediately | MEDIUM | Minimum: URL hash + headline fuzzy match. Better: semantic similarity on title+snippet against 7-day window |
| Priority classification (HIGH/MEDIUM/LOW) | Users need to know what to read first; flat list requires manual triage | MEDIUM | LLM-based classification works well for domain-specific scoring; rule-based fallback needed if API fails |
| Scheduled delivery (morning + afternoon) | Aggregation without delivery is just a database; users expect push not pull | LOW | GitHub Actions cron in UTC mapped to 7 AM / 4 PM IST is standard pattern; well-understood |
| Telegram message delivery | Primary channel; must reliably deliver formatted text with article titles, URLs, priority label | LOW | Telegram Bot API is stable; sendMessage with parse_mode=HTML or Markdown is table stakes |
| Email delivery (HTML digest) | Secondary channel; users expect formatted, scannable email; plain text feels unfinished | MEDIUM | Gmail SMTP + HTML template; must handle mobile rendering; inline CSS required for Gmail compatibility |
| Basic bot commands (help, status, pause) | Users need ability to control a running system; no controls = black box | LOW | /help, /status, /pause, /resume — standard Telegram bot UX patterns |
| Source health monitoring | If a feed silently breaks, user gets incomplete news without knowing why | LOW | Log fetch failures per source; surface in /status; alert if 3+ consecutive failures |

### Differentiators (Competitive Advantage)

Features that set this product apart. Not expected at launch, but create meaningful advantage.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Geographic tier priority (Tier 1/2/3 cities) | Delhi NCR/Mumbai/Bangalore/Hyderabad news matters more than tier-3 city news for the target users' audience on MagicBricks; no generic aggregator does this | MEDIUM | Requires city name entity extraction from headline/snippet; maintain geo-keyword mapping; Tier 1 bias in ranking score |
| Domain-specific keyword library with categories | Infrastructure / RERA-Regulatory / Celebrity real estate are distinct content verticals; pre-built library eliminates cold-start problem | LOW | Already partially built per PROJECT.md; needs category-aware classification scoring |
| Event-based dynamic scheduling (Budget Day, RERA deadlines, policy announcements) | On high-importance days, 2x/day delivery is insufficient; competitors have no event calendar concept | MEDIUM | Event calendar stored in config (JSON/YAML); scheduler checks event calendar before each run; adjusts frequency and priority thresholds accordingly |
| Breaking news alerts (outside scheduled delivery) | Critical stories (major RERA enforcement, large land acquisition announcements) can't wait for 4 PM digest | MEDIUM | Requires near-real-time polling (every 30-60 min via GitHub Actions on a separate cron) with strict HIGH-only filter to avoid alert fatigue |
| Natural language Telegram commands | "Add keyword metro rail" is far better UX than /addkeyword metro_rail; lowers barrier to management for non-technical users | MEDIUM | Small vocabulary NLP (Claude/regex hybrid); parse intent + entity from free-text message; confirm before executing |
| Context-aware AI analysis with Indian real estate domain priming | Generic sentiment is useless; "project delayed" in Indian real estate context implies RERA liability, not just schedule slip | MEDIUM | System prompt engineering with domain context baked in; Claude Sonnet is well-suited; Gemini as fallback |
| Two-user support with shared preferences | Couple who co-write content; single shared keyword set with individual delivery preferences (Telegram IDs) is simpler than full multi-tenancy | LOW | Two Telegram chat IDs in config; same curated digest to both; no user-specific filtering needed in v1 |
| Delivery stats via Telegram (/stats command) | Users want to know system is working; "how many stories fetched today, how many were HIGH priority" builds trust | LOW | Count metrics stored in GitHub-repo JSON; /stats parses and formats; no database needed |
| Source credibility tier (tier-A vs tier-B sources) | ET Realty, Business Standard carry more weight than obscure portals; this improves signal quality | LOW | Static source-weight mapping in config; factor into priority scoring; easily adjustable |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create disproportionate complexity or conflict with the project's constraints.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Full article content fetching and summarization | "Give me the full article summary, not just the headline" sounds great | GNews free plan does not provide full article content. Scraping article bodies risks ToS violations, CAPTCHAs, paywalls, and rate limits. Adds 10-30x AI cost. | Use headline + snippet for classification; include article URL for user to click through. Summaries from snippet are sufficient for triage. |
| Web scraping as primary source | More sources = more coverage | Scrapers break silently when sites update HTML. Maintenance burden is unbounded for a two-person household system. | Stick to RSS + GNews API; add new RSS feeds when needed — 5-minute config change vs ongoing scraper maintenance. |
| Per-user personalized keyword sets | "I want different keywords from my spouse" | Doubles the classification workload, doubles the config surface, adds user identity complexity. The users share a content vertical and co-write; shared config is sufficient. | Shared keyword library with category toggles per delivery session if differentiation is ever needed. |
| Read receipt / open-rate tracking | "Did they actually read the email?" | Email open tracking is broken: Apple MPP inflates open rates by 50-60%. Telegram has no read receipt API for bot messages. Metrics would be misleading and add no actionable value. | Implicit engagement signal: if user runs /addkeyword or /pause, they're engaged. No metrics infra needed. |
| Web UI / analytics dashboard | "A dashboard would be nice" | Explicitly out of scope per PROJECT.md. Adds a full frontend stack. Two users, Telegram-native context. | All stats via /stats Telegram command. GitHub Actions log is the admin dashboard. |
| ML-based recommendation learning (collaborative filtering) | "The system should learn what I like over time" | Requires click/engagement data, user behavior storage, model training pipeline. For two users with a stable domain focus, the keyword library IS the preference model. | Tune the keyword library and priority thresholds based on periodic manual review; far simpler and more transparent. |
| Multi-language support (Hindi/regional) | India has many languages; Hindi sources have broader reach | English-only sources cover the target outlets (ET Realty, Business Standard, MagicBricks blog, RERA portals). Hindi NLP for classification adds significant complexity. Out of scope per PROJECT.md. | English-only in v1; add Hindi as a named v2 feature with a clear trigger condition. |
| PDF report generation | "Weekly summary as a PDF would be great" | Adds PDF templating library, storage, email attachment handling. Out of scope per PROJECT.md. | HTML email digest IS the formatted report; users can print-to-PDF from email if needed. |
| Real-time streaming (WebSocket-based live feed) | "Show me news as it happens" | GitHub Actions minimum interval is ~5 minutes. Vercel serverless is stateless. Real-time requires a persistent server (cost, complexity). | Near-real-time via 30-60 minute GitHub Actions cron for breaking news; fully sufficient for the domain. |
| Social media monitoring (Twitter/X, LinkedIn) | More signals from social | API access is now paid and rate-limited. Social noise-to-signal ratio is very high for this domain. Adds auth complexity. Out of scope per PROJECT.md. | May add in v2 if specific social signals (celebrity real estate transactions) prove valuable. |

---

## Feature Dependencies

```
[RSS + GNews Fetching]
    └──required by──> [Keyword Filtering]
                          └──required by──> [Priority Classification (AI)]
                                                └──required by──> [Deduplication]
                                                                      └──required by──> [Delivery Scheduling]
                                                                                            └──required by──> [Telegram Delivery]
                                                                                            └──required by──> [Email Delivery]

[Breaking News Alerts]
    └──requires──> [Priority Classification (AI)]
    └──requires──> [Telegram Delivery]
    └──note: runs on separate cron, not delivery scheduler]

[Natural Language Bot Commands]
    └──requires──> [Telegram Delivery] (bot must be running)
    └──enhances──> [Keyword Library Management]
    └──enhances──> [Event-Based Scheduling]

[Event-Based Scheduling]
    └──requires──> [Delivery Scheduling] (extends it)
    └──requires──> [Breaking News Alerts] (increased frequency during events)

[Geographic Tier Priority]
    └──enhances──> [Priority Classification (AI)]
    └──requires──> [Keyword Filtering] (city names as geo-keywords)

[Source Credibility Tier]
    └──enhances──> [Priority Classification (AI)]

[Delivery Stats (/stats)]
    └──requires──> [Telegram Delivery]
    └──requires──> [Delivery Scheduling] (needs run logs)

[Two-User Support]
    └──requires──> [Telegram Delivery] (fan-out to two chat IDs)
    └──requires──> [Email Delivery] (two email addresses)
```

### Dependency Notes

- **Priority Classification requires Keyword Filtering:** Classification works on pre-filtered candidates. Running AI on all fetched articles would exceed cost budget ($1-4/month target) and the GNews API rate limit.
- **Breaking News Alerts requires Priority Classification:** Alerts must only fire for HIGH-priority stories; classification is the gate.
- **Deduplication requires at least 7-day article history:** This is the semantic memory window. History stored in GitHub repo JSON files (no DB needed).
- **Event-Based Scheduling conflicts with simple cron config:** The scheduling layer must be config-driven, not hardcoded cron strings. Design the scheduler to be event-calendar-aware from day one — retrofitting is painful.
- **Natural Language Commands depend on Telegram webhook (Vercel):** Webhook approach (vs polling) is required for real-time command response. GitHub Actions cannot receive inbound messages.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — validates that the system saves time and reliably surfaces relevant news.

- [ ] RSS feed fetching (10-15 curated Indian real estate/infrastructure feeds) — without this, nothing works
- [ ] GNews.io API integration with keyword queries — extends source coverage to 80,000+ outlets
- [ ] Keyword-based filtering using pre-built library (Infrastructure / Regulatory / Celebrity categories) — defines relevance
- [ ] AI priority classification (HIGH/MEDIUM/LOW) via Claude Sonnet with domain-primed system prompt — core value proposition
- [ ] Semantic deduplication against 7-day history (title embedding + cosine similarity, threshold ~0.85) — without this, repeated stories destroy trust
- [ ] Scheduled delivery at 7 AM and 4 PM IST via GitHub Actions cron — the "automation" in automated aggregation
- [ ] Telegram delivery to two users (formatted message with title, source, priority label, URL) — primary channel
- [ ] Email HTML digest delivery via Gmail SMTP — secondary channel; users expect it
- [ ] Basic bot commands: /help, /status, /pause, /resume — minimum control surface
- [ ] Source health logging — surfaced via /status; prevents silent failures

### Add After Validation (v1.x)

Features to add once core delivery is proven reliable.

- [ ] Breaking news alerts (30-60 min polling cron, HIGH-only threshold) — add when users confirm they want intraday alerts; risk of fatigue if added too early
- [ ] Natural language Telegram commands ("add keyword", "pause tomorrow") — add after basic /commands are working; UX upgrade not a prerequisite
- [ ] Geographic tier priority scoring (Tier 1 city bias in ranking) — add when users report Tier-2/3 noise is a problem
- [ ] Source credibility tier (weight ET Realty, Business Standard higher) — simple config change; add when source quality becomes a pain point
- [ ] Delivery stats via /stats command — add when users ask "is the bot working?" frequently; low effort, high trust signal

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] Event-based dynamic scheduling (Budget Day, RERA deadlines) — requires event calendar design; defer until user feedback confirms need
- [ ] Hindi-language source support — significant NLP complexity; only if English sources miss critical stories
- [ ] Social media signal layer (Twitter/LinkedIn for celebrity real estate) — API cost and noise concerns; needs v1 signal quality established first
- [ ] Source expansion beyond RSS + GNews (Newsdata.io, other APIs) — add if GNews rate limits become a constraint in practice

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| RSS + GNews fetching | HIGH | LOW | P1 |
| Keyword filtering | HIGH | LOW | P1 |
| AI priority classification | HIGH | MEDIUM | P1 |
| Semantic deduplication | HIGH | MEDIUM | P1 |
| Scheduled delivery (cron) | HIGH | LOW | P1 |
| Telegram message delivery | HIGH | LOW | P1 |
| Email HTML digest | MEDIUM | MEDIUM | P1 |
| Basic bot commands (/help /status) | HIGH | LOW | P1 |
| Source health logging | MEDIUM | LOW | P1 |
| Breaking news alerts | HIGH | MEDIUM | P2 |
| Natural language bot commands | MEDIUM | MEDIUM | P2 |
| Geographic tier priority | MEDIUM | LOW | P2 |
| Source credibility tier | MEDIUM | LOW | P2 |
| Delivery stats (/stats) | MEDIUM | LOW | P2 |
| Event-based scheduling | MEDIUM | MEDIUM | P3 |
| Hindi source support | LOW | HIGH | P3 |
| Social media monitoring | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

Key reference products: Feedly (with Leo AI), Inoreader, generic n8n/RSS-to-Telegram automations.

| Feature | Feedly (Leo) | Inoreader | Generic n8n RSS Bot | Khabri Approach |
|---------|--------------|-----------|---------------------|-----------------|
| RSS fetching | Yes — unlimited feeds on paid | Yes — unlimited, including social | Yes — via node | Yes — curated 10-15 feeds + GNews API |
| AI classification | Yes — Leo AI, trained on user prefs | No built-in AI | No | Yes — Claude Sonnet with domain-specific system prompt |
| Deduplication | Yes — automatic | No built-in | No | Yes — semantic similarity, 7-day window |
| Scheduled digest delivery | Via email/integrations only | Via email/integrations | Yes via cron | Yes — GitHub Actions cron, native Telegram + email |
| Telegram delivery | Via Zapier/IFTTT only | Via integrations only | Yes | Yes — native, primary channel |
| Keyword filtering | Yes — Leo topic rules | Yes — rules engine (steep learning curve) | Manual | Yes — category-based library, simpler UX |
| Natural language control | No — UI-only | No — UI-only | No | Yes — Telegram bot NLP (differentiator) |
| Domain specialization (India real estate) | None — generic | None — generic | None | Yes — geo-tier, domain prompt, curated source list |
| Event-based scheduling | No | No | No | Planned v1.x/v2 |
| Breaking news alerts | Via browser push (paid) | Via active search alerts | No | Planned v1.x |
| Cost | $6-15/month | $4-15/month | Self-hosted infra | $0 infra + <$5/month AI |
| Two-user delivery | Via shared team workspace (expensive) | Via shared account | Manual config | Native, simple config |

**Key insight:** No existing product combines (a) Indian real estate domain specialization, (b) Telegram-native control with natural language, (c) zero infrastructure cost, and (d) event-aware scheduling. The combination is the differentiator — not any single feature.

---

## Sources

- [Feedly Leo AI features](https://feedly.com/ai) — Feedly official documentation (MEDIUM confidence)
- [Inoreader rules and filters](https://www.inoreader.com/blog/2023/06/streamline-content-discovery-with-filters-and-rules.html) — Inoreader official blog (MEDIUM confidence)
- [GNews API documentation and limitations](https://gnews.io/) and [GNews docs](https://docs.gnews.io/) — official (HIGH confidence for rate limits)
- [Top 90 Indian Real Estate RSS Feeds](https://rss.feedspot.com/indian_real_estate_rss_feeds/) — FeedSpot (MEDIUM confidence — source list reference)
- [Semantic deduplication techniques](https://github.com/MinishLab/semhash) — GitHub, active 2025 (MEDIUM confidence)
- [AI news classification accuracy benchmarks](https://www.ijprems.com/uploadedfiles/paper/issue_7_july_2025/42854/final/fin_ijprems1752172068.pdf) — IJPREMS 2025 (MEDIUM confidence)
- [Telegram Bot Features (official)](https://core.telegram.org/bots/features) — Telegram official (HIGH confidence)
- [n8n RSS digest workflow pattern](https://n8n.io/workflows/6223-send-scheduled-rss-news-digest-emails-with-formatted-html-in-gmail/) — n8n templates (MEDIUM confidence)
- [Email open-rate tracking challenges (Apple MPP)](https://www.emailtooltester.com/en/blog/bot-clicks-in-email-marketing/) — EmailToolTester (MEDIUM confidence)
- [Telegram keyword monitoring bot patterns](https://stellaray777.medium.com/why-im-building-a-telegram-keyword-monitoring-bot-and-why-so-many-people-need-it-029304a6c0d1) — Medium 2026 (LOW confidence — single source)

---

*Feature research for: Automated news aggregation — Indian infrastructure & real estate*
*Researched: 2026-02-26*
