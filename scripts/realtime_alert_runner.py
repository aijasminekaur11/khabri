#!/usr/bin/env python3
"""
Real-time Breaking News Alert Runner
Khabri - News Intelligence System

Checks for high-priority breaking news every 15 minutes
Only alerts on important keywords to avoid alert fatigue

Usage:
    python realtime_alert_runner.py scrape
    python realtime_alert_runner.py process
    python realtime_alert_runner.py notify
"""

import os
import sys
import json
import asyncio
import logging
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

# IST timezone (UTC + 5:30)
IST = timezone(timedelta(hours=5, minutes=30))

import feedparser
import aiohttp
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('RealtimeAlert')

# Temp files
ARTICLES_FILE = '/tmp/realtime_articles.json'
PROCESSED_FILE = '/tmp/realtime_processed.json'
SENT_FILE = '/tmp/realtime_sent.json'

# Config file path
KEYWORDS_PATH = Path(__file__).parent.parent / 'config' / 'keywords.yaml'

# HIGH PRIORITY keywords - only alert on these
HIGH_PRIORITY_KEYWORDS = [
    'breaking',
    'just in',
    'flash',
    'urgent',
    'rbi',
    'reserve bank',
    'repo rate',
    'interest rate cut',
    'interest rate hike',
    'pmay',
    'pradhan mantri awas',
    'rera',
    'stamp duty',
    'budget 2026',
    'finance minister',
    'home loan',
    '₹100 crore',
    '₹500 crore',
    '₹1000 crore',
    'major deal',
    'dlf',
    'godrej properties',
    'oberoi realty',
]

# RSS feeds to monitor for breaking news
REALTIME_FEEDS = [
    {
        'name': 'Breaking Real Estate',
        'url': 'https://news.google.com/rss/search?q=breaking+india+real+estate&hl=en-IN&gl=IN&ceid=IN:en'
    },
    {
        'name': 'RBI News',
        'url': 'https://news.google.com/rss/search?q=RBI+interest+rate&hl=en-IN&gl=IN&ceid=IN:en'
    },
    {
        'name': 'Real Estate Breaking',
        'url': 'https://news.google.com/rss/search?q=india+property+breaking+news&hl=en-IN&gl=IN&ceid=IN:en'
    },
    {
        'name': 'Housing Policy',
        'url': 'https://news.google.com/rss/search?q=PMAY+housing+policy+india&hl=en-IN&gl=IN&ceid=IN:en'
    },
]


def load_sent_articles():
    """Load previously sent article IDs"""
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, 'r') as f:
            data = json.load(f)
            # Only keep last 24 hours of sent IDs
            return set(data.get('ids', []))
    return set()


def save_sent_articles(sent_ids):
    """Save sent article IDs"""
    # Keep only last 500 to prevent file bloat
    ids_list = list(sent_ids)[-500:]
    with open(SENT_FILE, 'w') as f:
        json.dump({'ids': ids_list, 'updated': datetime.now().isoformat()}, f)


def scrape_breaking_news():
    """Scrape breaking news from RSS feeds"""
    logger.info("⚡ Scraping for breaking news...")

    all_articles = []

    for feed_config in REALTIME_FEEDS:
        try:
            logger.info(f"  Fetching: {feed_config['name']}...")
            feed = feedparser.parse(feed_config['url'])

            for entry in feed.entries[:10]:
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

            logger.info(f"    Got {min(10, len(feed.entries))} articles")

        except Exception as e:
            logger.error(f"  {feed_config['name']}: Failed - {e}")

    logger.info(f"Total scraped: {len(all_articles)} articles")

    with open(ARTICLES_FILE, 'w') as f:
        json.dump(all_articles, f, default=str)

    return all_articles


def process_breaking_articles():
    """Filter for HIGH PRIORITY breaking news only"""
    logger.info("Processing for breaking news...")

    if not os.path.exists(ARTICLES_FILE):
        logger.warning("No articles file found")
        with open(PROCESSED_FILE, 'w') as f:
            json.dump([], f)
        return []

    with open(ARTICLES_FILE, 'r') as f:
        all_articles = json.load(f)

    # Load already sent articles
    sent_ids = load_sent_articles()

    # Filter for high-priority breaking news
    breaking_articles = []
    seen_titles = set()

    for article in all_articles:
        # Skip if already sent
        if article['id'] in sent_ids:
            continue

        # Deduplicate by title
        title_key = article.get('title', '').lower()[:50]
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)

        # Check for HIGH PRIORITY keywords
        text = (article.get('title', '') + ' ' + article.get('content', '')).lower()

        matched_keywords = [kw for kw in HIGH_PRIORITY_KEYWORDS if kw in text]

        # Must match at least 1 high-priority keyword
        if matched_keywords:
            article['priority'] = 'HIGH'
            article['matched_keywords'] = matched_keywords
            article['priority_score'] = len(matched_keywords)
            breaking_articles.append(article)

    # Sort by priority score
    breaking_articles.sort(key=lambda x: x.get('priority_score', 0), reverse=True)

    # Limit to top 5 breaking news
    breaking_articles = breaking_articles[:5]

    logger.info(f"Found {len(breaking_articles)} HIGH PRIORITY articles")

    with open(PROCESSED_FILE, 'w') as f:
        json.dump(breaking_articles, f, default=str)

    return breaking_articles


async def send_breaking_alert():
    """Send breaking news alert via Telegram"""
    logger.info("Checking for breaking news alerts...")

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        logger.error("Telegram credentials not set!")
        sys.exit(1)

    if not os.path.exists(PROCESSED_FILE):
        logger.warning("No processed file found")
        return

    with open(PROCESSED_FILE, 'r') as f:
        articles = json.load(f)

    if not articles:
        logger.info("No breaking news to alert")
        return

    # Format message
    message = format_breaking_alert(articles)

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
                logger.info(f"Breaking news alert sent! ({len(articles)} articles)")

                # Mark articles as sent
                sent_ids = load_sent_articles()
                for article in articles:
                    sent_ids.add(article['id'])
                save_sent_articles(sent_ids)
            else:
                error = await response.text()
                logger.error(f"Telegram send failed: {error}")
                sys.exit(1)


def format_breaking_alert(articles):
    """Format breaking news alert message"""
    # Convert to IST timezone
    now_ist = datetime.now(IST)
    time_str = now_ist.strftime('%I:%M %p')

    lines = [
        "⚡ <b>BREAKING NEWS ALERT</b>",
        f"⏰ {time_str} IST",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        ""
    ]

    for i, article in enumerate(articles[:5], 1):
        title = article.get('title', 'No title')[:80]
        url = article.get('url', '')
        keywords = article.get('matched_keywords', [])[:3]

        if url:
            lines.append(f'🔴 <b>{i}.</b> <a href="{url}">{title}</a>')
        else:
            lines.append(f"🔴 <b>{i}.</b> {title}")
        if keywords:
            keyword_str = ', '.join(keywords[:3])
            lines.append(f"   🏷️ {keyword_str}")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("⚡ <i>High-priority alert</i>")
    lines.append("🤖 <i>Powered by Khabri</i>")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python realtime_alert_runner.py [scrape|process|notify]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'scrape':
        scrape_breaking_news()
    elif command == 'process':
        process_breaking_articles()
    elif command == 'notify':
        asyncio.run(send_breaking_alert())
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
