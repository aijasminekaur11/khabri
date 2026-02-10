#!/usr/bin/env python3
"""
Competitor Early-Warning System
Khabri - News Intelligence System

Monitors competitor blogs for new articles
Alerts when competitors publish new content

Usage:
    python competitor_alert_runner.py scrape
    python competitor_alert_runner.py process
    python competitor_alert_runner.py notify
"""

import os
import sys
import json
import html as html_module
import asyncio
import logging
import hashlib
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

# IST timezone (UTC + 5:30)
IST = timezone(timedelta(hours=5, minutes=30))

import feedparser
import aiohttp
import yaml

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('CompetitorAlert')

# Temp files - use tempfile module for cross-platform compatibility
_temp_dir = tempfile.gettempdir()
ARTICLES_FILE = os.path.join(_temp_dir, 'competitor_articles.json')
PROCESSED_FILE = os.path.join(_temp_dir, 'competitor_processed.json')

# Persistent sent tracking
CACHE_DIR = os.getenv('GITHUB_WORKSPACE', _temp_dir)
SEEN_FILE = os.path.join(CACHE_DIR, '.khabri_cache', 'competitor_seen.json')

# Config file path
CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'sources.yaml'


def load_competitors():
    """Load competitor configs"""
    if not CONFIG_PATH.exists():
        logger.error(f"Config file not found: {CONFIG_PATH}")
        return []

    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)

    competitors = []
    for comp in config.get('competitors', []):
        if comp.get('enabled', True):
            competitors.append({
                'name': comp['name'],
                'url': comp['url'],
                'alert_on_new': comp.get('alert_on_new', True)
            })

    return competitors


def load_seen_articles():
    """Load previously seen article IDs from persistent cache"""
    try:
        cache_dir = os.path.dirname(SEEN_FILE)
        os.makedirs(cache_dir, exist_ok=True)

        if os.path.exists(SEEN_FILE):
            with open(SEEN_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return set(data)
                return set(data.get('ids', []))
    except Exception as e:
        logger.warning(f"Could not load seen articles: {e}")
    return set()


def save_seen_articles(seen_ids):
    """Save seen article IDs with timestamp"""
    try:
        cache_dir = os.path.dirname(SEEN_FILE)
        os.makedirs(cache_dir, exist_ok=True)

        ids_list = list(seen_ids)[-300:]  # Keep last 300

        with open(SEEN_FILE, 'w') as f:
            json.dump({
                'ids': ids_list,
                'updated': datetime.now(IST).isoformat(),
                'count': len(ids_list)
            }, f, indent=2)
        logger.info(f"Saved {len(ids_list)} seen article IDs")
    except Exception as e:
        logger.error(f"Could not save seen articles: {e}")


def scrape_rss_for_competitor(name, url):
    """Try to find and scrape RSS feed for competitor"""
    articles = []

    # Common RSS feed paths to try
    rss_attempts = [
        url.rstrip('/') + '/feed/',
        url.rstrip('/') + '/rss/',
        url.rstrip('/') + '/feed.xml',
        url.rstrip('/') + '/rss.xml',
    ]

    # Also try Google News for competitor
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.netloc:
        google_search = f"https://news.google.com/rss/search?q=site:{parsed.netloc}&hl=en-IN&gl=IN&ceid=IN:en"
        rss_attempts.append(google_search)

    for rss_url in rss_attempts:
        try:
            feed = feedparser.parse(rss_url)
            if feed.entries:
                logger.info(f"  Found RSS: {rss_url} ({len(feed.entries)} entries)")
                for entry in feed.entries[:10]:
                    article_id = hashlib.md5(entry.get('link', '').encode()).hexdigest()

                    published_at = datetime.now().isoformat()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            published_at = datetime(*entry.published_parsed[:6]).isoformat()
                        except:
                            pass

                    articles.append({
                        'id': article_id,
                        'title': entry.get('title', 'No title'),
                        'url': entry.get('link', ''),
                        'competitor': name,
                        'published_at': published_at,
                        'scraped_at': datetime.now().isoformat()
                    })
                break  # Found working RSS, stop trying
        except Exception as e:
            continue

    return articles


def scrape_html_for_competitor(name, url):
    """Scrape HTML page for articles (fallback)"""
    if not HAS_BS4:
        return []

    articles = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; KhabriBot/1.0)'}
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find article links (common patterns)
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text(strip=True)

                # Filter for likely article links
                if (len(text) > 30 and
                    ('article' in href or 'blog' in href or 'news' in href or
                     text[0].isupper()) and
                    'category' not in href.lower() and
                    'tag' not in href.lower()):

                    # Make URL absolute
                    if href.startswith('/'):
                        base = '/'.join(url.split('/')[:3])
                        href = base + href

                    article_id = hashlib.md5(href.encode()).hexdigest()

                    articles.append({
                        'id': article_id,
                        'title': text[:150],
                        'url': href,
                        'competitor': name,
                        'published_at': datetime.now().isoformat(),
                        'scraped_at': datetime.now().isoformat()
                    })

            # Limit to 10
            articles = articles[:10]
            logger.info(f"  Scraped HTML: {len(articles)} potential articles")

    except Exception as e:
        logger.error(f"  HTML scrape failed: {e}")

    return articles


def scrape_competitors():
    """Scrape all competitor sources"""
    logger.info("🏢 Scraping competitor news...")

    competitors = load_competitors()
    logger.info(f"Checking {len(competitors)} competitors...")

    all_articles = []

    for comp in competitors:
        logger.info(f"  Checking: {comp['name']}...")

        # Try RSS first
        articles = scrape_rss_for_competitor(comp['name'], comp['url'])

        # If no RSS, try HTML scraping
        if not articles:
            articles = scrape_html_for_competitor(comp['name'], comp['url'])

        all_articles.extend(articles)

    logger.info(f"Total scraped: {len(all_articles)} articles")

    with open(ARTICLES_FILE, 'w') as f:
        json.dump(all_articles, f, default=str)

    return all_articles


def process_competitor_articles():
    """Filter for NEW articles only"""
    logger.info("Processing competitor articles...")

    if not os.path.exists(ARTICLES_FILE):
        logger.warning("No articles file found")
        with open(PROCESSED_FILE, 'w') as f:
            json.dump([], f)
        return []

    with open(ARTICLES_FILE, 'r') as f:
        all_articles = json.load(f)

    # Load seen articles
    seen_ids = load_seen_articles()

    # Filter for new articles
    new_articles = []
    seen_titles = set()

    for article in all_articles:
        # Skip if already seen
        if article['id'] in seen_ids:
            continue

        # Deduplicate by title
        title_key = article.get('title', '').lower()[:50]
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)

        new_articles.append(article)

    # Group by competitor
    by_competitor = {}
    for article in new_articles:
        comp = article['competitor']
        if comp not in by_competitor:
            by_competitor[comp] = []
        by_competitor[comp].append(article)

    result = {
        'new_count': len(new_articles),
        'by_competitor': by_competitor,
        'articles': new_articles
    }

    logger.info(f"Found {len(new_articles)} NEW articles")
    for comp, articles in by_competitor.items():
        logger.info(f"  {comp}: {len(articles)} new")

    with open(PROCESSED_FILE, 'w') as f:
        json.dump(result, f, default=str)

    return result


async def send_competitor_alert():
    """Send competitor alert via Telegram"""
    logger.info("Checking for alerts to send...")

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        logger.error("Telegram credentials not set!")
        sys.exit(1)

    if not os.path.exists(PROCESSED_FILE):
        logger.warning("No processed file found")
        return

    with open(PROCESSED_FILE, 'r') as f:
        result = json.load(f)

    new_count = result.get('new_count', 0)

    if new_count == 0:
        logger.info("No new competitor articles to alert")
        return

    # Format message
    message = format_competitor_alert(result)

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
                logger.info(f"Competitor alert sent! ({new_count} articles)")

                # Mark articles as seen
                seen_ids = load_seen_articles()
                for article in result.get('articles', []):
                    seen_ids.add(article['id'])
                save_seen_articles(seen_ids)
            else:
                error = await response.text()
                logger.error(f"Telegram send failed: {error}")
                sys.exit(1)


def format_competitor_alert(result):
    """Format competitor alert message"""
    now_ist = datetime.now(IST)
    time_str = now_ist.strftime('%I:%M %p')

    new_count = result.get('new_count', 0)
    by_competitor = result.get('by_competitor', {})

    lines = [
        "🚨 <b>COMPETITOR ALERT</b>",
        f"⏰ {time_str} IST",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
        f"📰 <b>{new_count} new articles detected!</b>",
        ""
    ]

    for comp_name, articles in by_competitor.items():
        lines.append(f"🏢 <b>{comp_name}</b> ({len(articles)} new)")
        lines.append("")

        for i, article in enumerate(articles[:3], 1):
            title = html_module.escape(article.get('title', 'No title')[:70])
            url = html_module.escape(article.get('url', ''), quote=True)

            if url:
                lines.append(f"  {i}. <a href=\"{url}\">{title}</a>")
            else:
                lines.append(f"  {i}. {title}")

        if len(articles) > 3:
            lines.append(f"  ... and {len(articles) - 3} more")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    lines.append("💡 <i>Stay ahead - check their angles!</i>")
    lines.append("🤖 <i>Powered by Khabri</i>")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python competitor_alert_runner.py [scrape|process|notify]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'scrape':
        scrape_competitors()
    elif command == 'process':
        process_competitor_articles()
    elif command == 'notify':
        asyncio.run(send_competitor_alert())
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
