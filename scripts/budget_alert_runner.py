#!/usr/bin/env python3
"""
Union Budget 2026 - Event Alert Runner
Khabri - News Intelligence System

High-frequency alerts during Union Budget presentation
Scrapes budget-specific news every 10 minutes during the event

Usage:
    python budget_alert_runner.py scrape
    python budget_alert_runner.py process
    python budget_alert_runner.py notify
"""

import os
import sys
import json
import asyncio
import logging
import hashlib
from datetime import datetime
from pathlib import Path

import feedparser
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('BudgetAlert')

# Temp files
ARTICLES_FILE = '/tmp/budget_articles.json'
PROCESSED_FILE = '/tmp/budget_processed.json'
SENT_FILE = '/tmp/budget_sent.json'  # Track already sent articles

# Budget-specific keywords
BUDGET_KEYWORDS = [
    'budget 2026',
    'union budget',
    'finance minister',
    'nirmala sitharaman',
    'real estate budget',
    'housing budget',
    'pmay',
    'pradhan mantri awas',
    'affordable housing',
    'stamp duty',
    'home loan',
    'tax rebate',
    'section 80c',
    'hra',
    'gst real estate',
    'infrastructure',
    'smart city',
    'metro',
    'rera',
    'property tax',
    'capital gains',
    'ltcg',
    'stcg',
    'interest rate',
    'rbi',
    'fiscal deficit',
]


def load_sent_articles():
    """Load previously sent article IDs"""
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, 'r') as f:
            return set(json.load(f))
    return set()


def save_sent_articles(sent_ids):
    """Save sent article IDs"""
    with open(SENT_FILE, 'w') as f:
        json.dump(list(sent_ids), f)


def scrape_budget_news():
    """Scrape budget-related news"""
    logger.info("🏛️ Scraping Budget 2026 news...")

    # Budget-specific RSS feeds
    rss_feeds = [
        {
            'name': 'Budget 2026',
            'url': 'https://news.google.com/rss/search?q=union+budget+2026+india&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Budget Real Estate',
            'url': 'https://news.google.com/rss/search?q=budget+2026+real+estate+housing&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Budget Housing',
            'url': 'https://news.google.com/rss/search?q=budget+2026+PMAY+affordable+housing&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Budget Tax',
            'url': 'https://news.google.com/rss/search?q=budget+2026+home+loan+tax+benefit&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Budget Infrastructure',
            'url': 'https://news.google.com/rss/search?q=budget+2026+infrastructure+smart+city&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Nirmala Sitharaman',
            'url': 'https://news.google.com/rss/search?q=nirmala+sitharaman+budget&hl=en-IN&gl=IN&ceid=IN:en'
        }
    ]

    all_articles = []

    for feed_config in rss_feeds:
        try:
            logger.info(f"  Fetching: {feed_config['name']}...")
            feed = feedparser.parse(feed_config['url'])

            for entry in feed.entries[:15]:
                article_id = hashlib.md5(entry.get('link', '').encode()).hexdigest()

                published_at = datetime.now().isoformat()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published_at = datetime(*entry.published_parsed[:6]).isoformat()
                    except:
                        pass

                article = {
                    'id': article_id,
                    'title': entry.get('title', 'No title'),
                    'url': entry.get('link', ''),
                    'source': feed_config['name'],
                    'content': entry.get('summary', ''),
                    'published_at': published_at,
                    'scraped_at': datetime.now().isoformat()
                }
                all_articles.append(article)

            logger.info(f"    Got {min(15, len(feed.entries))} articles")

        except Exception as e:
            logger.error(f"  {feed_config['name']}: Failed - {e}")

    logger.info(f"Total scraped: {len(all_articles)} articles")

    with open(ARTICLES_FILE, 'w') as f:
        json.dump(all_articles, f, default=str)

    return all_articles


def process_budget_articles():
    """Filter for budget-relevant articles only"""
    logger.info("Processing budget articles...")

    if not os.path.exists(ARTICLES_FILE):
        logger.warning("No articles file found")
        with open(PROCESSED_FILE, 'w') as f:
            json.dump([], f)
        return []

    with open(ARTICLES_FILE, 'r') as f:
        all_articles = json.load(f)

    # Load already sent articles
    sent_ids = load_sent_articles()

    # Filter and deduplicate
    seen_titles = set()
    processed = []

    for article in all_articles:
        # Skip if already sent
        if article['id'] in sent_ids:
            continue

        # Deduplicate by title
        title_key = article.get('title', '').lower()[:50]
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)

        # Check for budget keywords
        text = (article.get('title', '') + ' ' + article.get('content', '')).lower()

        relevance_score = sum(1 for kw in BUDGET_KEYWORDS if kw in text)

        if relevance_score >= 1:  # At least 1 keyword match
            article['relevance_score'] = relevance_score
            article['matched_keywords'] = [kw for kw in BUDGET_KEYWORDS if kw in text]
            processed.append(article)

    # Sort by relevance
    processed.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

    # Limit to top 10
    processed = processed[:10]

    logger.info(f"Filtered: {len(processed)} budget-relevant articles")

    with open(PROCESSED_FILE, 'w') as f:
        json.dump(processed, f, default=str)

    return processed


async def send_budget_alert():
    """Send budget alert via Telegram"""
    logger.info("Sending Budget alert...")

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        logger.error("Telegram credentials not set!")
        sys.exit(1)

    if not os.path.exists(PROCESSED_FILE):
        logger.warning("No processed articles")
        return

    with open(PROCESSED_FILE, 'r') as f:
        articles = json.load(f)

    if not articles:
        logger.info("No new budget articles to send")
        return

    # Format message
    message = format_budget_alert(articles)

    # Send via Telegram
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    async with aiohttp.ClientSession() as session:
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                logger.info(f"Budget alert sent! ({len(articles)} articles)")

                # Mark articles as sent
                sent_ids = load_sent_articles()
                for article in articles:
                    sent_ids.add(article['id'])
                save_sent_articles(sent_ids)
            else:
                error = await response.text()
                logger.error(f"Telegram send failed: {error}")
                sys.exit(1)


def format_budget_alert(articles):
    """Format budget alert message"""
    now = datetime.now()
    time_str = now.strftime('%I:%M %p')

    lines = [
        "🏛️ <b>UNION BUDGET 2026 - LIVE UPDATE</b>",
        f"⏰ {time_str} IST",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        ""
    ]

    for i, article in enumerate(articles[:5], 1):
        title = article.get('title', 'No title')[:80]
        url = article.get('url', '')
        keywords = article.get('matched_keywords', [])[:3]

        lines.append(f"<b>{i}.</b> {'<a href=\"' + url + '\">' + title + '</a>' if url else title}")
        if keywords:
            lines.append(f"   🏷️ {', '.join(keywords[:3])}")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("🔔 <i>Live alerts every 10 min during Budget</i>")
    lines.append("🤖 <i>Powered by Khabri</i>")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python budget_alert_runner.py [scrape|process|notify]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'scrape':
        scrape_budget_news()
    elif command == 'process':
        process_budget_articles()
    elif command == 'notify':
        asyncio.run(send_budget_alert())
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
