# 📰 On-Demand News Feature

## Overview

Users can now request **instant real estate news** by simply typing `news` in the Telegram bot chat. The bot will immediately fetch and send the latest news articles.

---

## 🚀 How to Use

### Method 1: Simple Keyword (Recommended)
Just type:
```
news
```

Or variations:
- `latest news`
- `get news`
- `show news`
- `send me news`
- `fetch news`

### Method 2: Command
Type:
```
/news
```

---

## ⚡ What Happens

1. **Bot acknowledges**: "🔍 Fetching latest real estate news..."
2. **Scrapes 4 sources**:
   - Real Estate India (Google News)
   - Property Prices
   - Home Loan
   - Infrastructure
3. **Filters & categorizes** articles by relevance
4. **Sends formatted message** with:
   - 📰 Latest headlines
   - 📁 Grouped by category (Policy, Market, Infrastructure, etc.)
   - 🔗 Clickable links
   - 📰 Source attribution

---

## 🛡️ Rate Limiting

To prevent spam and ensure fair usage:
- **1 request per 5 minutes** per user
- If rate limited, bot shows: "⏱️ Please wait Xm Ys before requesting news again"

---

## 💾 Caching

- News is **cached for 2 minutes**
- Multiple users requesting within 2 minutes get the same cached results
- Ensures fast response and reduces server load

---

## 📋 Categories Included

Articles are automatically categorized:

| Category | Keywords |
|----------|----------|
| 📋 **Policy** | RERA, regulation, policy, government, PMAY |
| 📈 **Market Updates** | price, rate, market, demand, sales |
| 🏗️ **Infrastructure** | metro, airport, highway, smart city |
| 🏢 **Launches** | new project, launch, upcoming, development |
| 💰 **Finance** | loan, EMI, interest, RBI, mortgage |

---

## 🔧 Technical Details

### Files Modified
- `src/notifiers/telegram_bot_handler.py` - Added on-demand news handling

### New Methods Added
1. `_is_news_trigger()` - Detects news keyword patterns
2. `_check_rate_limit()` - Enforces rate limiting
3. `_fetch_news_on_demand()` - Scrapes RSS feeds
4. `_format_news_message()` - Formats for Telegram
5. `handle_news_command()` - Main handler
6. `_send_chat_action()` - Shows "typing" indicator

### Dependencies
Uses existing dependencies:
- `feedparser` - RSS feed parsing
- `requests` - HTTP requests
- `asyncio` - Async handling

---

## 📝 Example Output

```
📰 Latest Real Estate News
📅 February 16, 2026 | ⏰ 02:30 PM
📊 8 articles

━━━━━━━━━━━━━━━━━━━━

📁 POLICY

• New RERA guidelines announced for 2026
  📰 Real Estate India

• PMAY scheme extended till March 2027
  📰 Property Prices

📁 INFRASTRUCTURE

• Mumbai Metro Line 3 to open next month
  📰 Infrastructure

• New airport terminal inaugurated in Bangalore
  📰 Real Estate India

📁 MARKET UPDATES

• Property prices rise 5% in major cities
  📰 Property Prices

━━━━━━━━━━━━━━━━━━━━
🤖 On-demand news via Khabri Bot
⏱️ Rate limit: 1 request per 5 minutes
```

---

## 🐛 Troubleshooting

### "Couldn't fetch news right now"
- Try again in a few minutes
- Check if RSS sources are accessible
- Check bot logs for errors

### Rate limit too strict?
Edit `telegram_bot_handler.py`:
```python
_NEWS_RATE_LIMIT_MINUTES = 5  # Change to desired value
```

### Want different news sources?
Edit the `rss_feeds` list in `_fetch_news_on_demand()` method.

---

## 🎯 Future Enhancements

Possible improvements:
- [ ] Filter by category: `news policy` or `news infrastructure`
- [ ] Search news: `news about DLF`
- [ ] Set news alerts: `alert me about RERA changes`
- [ ] News digest: `send me daily news summary`

---

## ✅ Testing

To test the feature:

1. Start the Telegram bot:
   ```bash
   python scripts/run_telegram_bot.py
   ```

2. Send `news` to your bot

3. Should receive news within 5-10 seconds

---

**Enjoy instant real estate news! 📰**
