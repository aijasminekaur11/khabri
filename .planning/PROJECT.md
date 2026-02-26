# Khabri

## What This Is

An automated news aggregation system that curates infrastructure and real estate news for India-focused content writers. Fetches from Google News API and RSS feeds, uses AI (Claude/Gemini) for priority classification and deduplication, and delivers curated briefs via Telegram and Email on a schedule. Controlled entirely through natural language Telegram commands.

## Core Value

Deliver the right infrastructure and real estate news at the right time — so the user never misses critical developments and saves 2+ hours of daily manual research.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Automated news fetching from Google News API + curated RSS feeds
- [ ] AI-powered priority classification (HIGH/MEDIUM/LOW) with context-aware analysis
- [ ] Semantic duplicate detection against 7-day history
- [ ] Scheduled delivery at 7 AM and 4 PM IST via Telegram + Email
- [ ] Breaking news alerts for critical developments
- [ ] Natural language Telegram bot for keyword management, schedule control, event creation
- [ ] Event-based dynamic scheduling (e.g., Budget Day with custom frequency)
- [ ] Keyword library with categories: Infrastructure, Authorities/Regulatory, Celebrity real estate
- [ ] Geographic tier-based priority (Tier 1: Delhi NCR/Mumbai/Bangalore/Hyderabad, Tier 2/3 filtered)
- [ ] Max 15 stories per delivery with priority-based selection
- [ ] Interactive Telegram menu for settings, keywords, stats
- [ ] Two-user support (shared bot, individual notifications)

### Out of Scope

- Video news monitoring — text only in v1
- Automatic content writing/article drafting — news delivery only
- Image/photo analysis from news sources
- Multi-language sources — English only in v1
- Voice notifications
- CMS integration — standalone system
- News archives beyond 7 days
- Paid news sources — free sources only
- PDF report generation
- Social media sentiment analysis — may add in v2
- Analytics dashboard web UI — Telegram stats only
- Competitor tracking

## Context

- **Target users:** Two users (husband and wife) who write content for Magic Bricks, a real estate platform in India
- **Current pain:** 2-3 hours daily manual research across scattered sources, risk of missing critical news
- **Domain:** Indian infrastructure (metro, highways, airports, smart cities) + real estate regulatory (RERA, PMAY) + celebrity property transactions
- **Existing assets:** Comprehensive keyword library pre-configured, RSS feed list curated, AI prompt templates designed
- **Delivery channels:** Telegram (primary, interactive) + Gmail SMTP (secondary, formatted HTML)
- **Infrastructure:** GitHub Actions for scheduling, Vercel for Telegram webhook, Gmail SMTP for email
- **AI strategy:** Claude (Sonnet) primary for analysis, Gemini as fallback. Batch processing for cost optimization (~$1-4/month)

## Constraints

- **Cost:** $0 infrastructure, <$5/month AI API calls — all free tiers (GitHub Actions, Vercel, GNews.io)
- **API Limits:** GNews.io 100 requests/day, Gmail SMTP rate limits
- **Tech Stack:** Python (GitHub Actions), Vercel serverless (Telegram webhook)
- **Timezone:** All user-facing times in IST, GitHub Actions cron in UTC
- **Scale:** Two users, single bot instance — no multi-tenancy needed

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Gmail SMTP over Resend | Already configured, simpler setup | — Pending |
| GitHub repo as data store | Free, version-controlled, no DB needed | — Pending |
| Claude primary, Gemini fallback | Better analysis quality, fallback for reliability | — Pending |
| Python over Node for core | Better RSS/scraping ecosystem, GitHub Actions native | — Pending |
| Single bot, two users | Simple architecture, shared preferences sufficient | — Pending |

---
*Last updated: 2026-02-26 after initialization*
