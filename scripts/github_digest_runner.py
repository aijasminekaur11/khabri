#!/usr/bin/env python3
"""
GitHub Actions Digest Runner
Khabri - News Intelligence System

This script is called by GitHub Actions to:
1. Scrape news from RSS feeds
2. Process articles
3. Send notifications via Telegram/Email

Usage:
    python github_digest_runner.py scrape
    python github_digest_runner.py process
    python github_digest_runner.py notify telegram
    python github_digest_runner.py notify email
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

# We'll use feedparser directly (it's a simple dependency)
import feedparser
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('GitHubDigest')

# Temp file to store scraped articles between steps - use tempfile for cross-platform compatibility
_temp_dir = tempfile.gettempdir()
ARTICLES_FILE = os.path.join(_temp_dir, 'khabri_articles.json')
PROCESSED_FILE = os.path.join(_temp_dir, 'khabri_processed.json')

# Persistent sent tracking to avoid duplicate notifications
CACHE_DIR = os.getenv('GITHUB_WORKSPACE', _temp_dir)
SENT_FILE = os.path.join(CACHE_DIR, '.khabri_cache', 'digest_sent.json')

class OrderedSet:
    """A set that preserves insertion order for correct recency-based pruning."""

    def __init__(self, iterable=None):
        self._dict = dict.fromkeys(iterable or [])

    def add(self, item):
        self._dict[item] = None

    def __contains__(self, item):
        return item in self._dict

    def __len__(self):
        return len(self._dict)

    def to_list(self):
        return list(self._dict.keys())


def load_sent_articles():
    """Load previously sent article IDs from persistent cache"""
    try:
        cache_dir = os.path.dirname(SENT_FILE)
        os.makedirs(cache_dir, exist_ok=True)

        if os.path.exists(SENT_FILE):
            with open(SENT_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return OrderedSet(data)
                return OrderedSet(data.get('ids', []))
    except Exception as e:
        logger.warning(f"Could not load sent articles: {e}")
    return OrderedSet()


def save_sent_articles(sent_ids):
    """Save sent article IDs with timestamp"""
    try:
        cache_dir = os.path.dirname(SENT_FILE)
        os.makedirs(cache_dir, exist_ok=True)

        # Keep only last 300 IDs to prevent bloat (preserves insertion order)
        ids_list = sent_ids.to_list()[-300:]

        with open(SENT_FILE, 'w') as f:
            json.dump({
                'ids': ids_list,
                'updated': datetime.now(IST).isoformat(),
                'count': len(ids_list)
            }, f, indent=2)
        logger.info(f"Saved {len(ids_list)} sent article IDs")
    except Exception as e:
        logger.error(f"Could not save sent articles: {e}")


# REAL ESTATE keywords - articles MUST contain at least one
REAL_ESTATE_KEYWORDS = [
    'real estate', 'property', 'housing', 'home loan', 'affordable housing',
    'pmay', 'pradhan mantri awas', 'rera', 'stamp duty', 'builder', 'developer',
    'residential', 'commercial property', 'realty', 'home buyer', 'rental',
    'apartment', 'flat', 'plot', 'land', 'construction', 'infrastructure',
    'metro', 'highway', 'airport', 'smart city', 'dlf', 'godrej properties',
    'oberoi realty', 'prestige', 'sobha', 'brigade', 'lodha', 'mahindra lifespace',
    'home loan rate', 'emi', 'mortgage', 'housing finance', 'property prices',
]


def scrape_rss_feeds():
    """Scrape news from RSS feeds using feedparser directly"""
    logger.info("Starting news scraping...")

    # RSS feeds to scrape - REAL ESTATE & INFRASTRUCTURE FOCUSED
    rss_feeds = [
        {
            'name': 'Real Estate India',
            'url': 'https://news.google.com/rss/search?q=indian+real+estate+property&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Property Prices',
            'url': 'https://news.google.com/rss/search?q=india+property+prices+housing+market&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Housing PMAY',
            'url': 'https://news.google.com/rss/search?q=india+housing+PMAY+affordable&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'RERA Builder',
            'url': 'https://news.google.com/rss/search?q=RERA+real+estate+builder&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Metro Property',
            'url': 'https://news.google.com/rss/search?q=mumbai+delhi+bangalore+property+real+estate&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Home Loan',
            'url': 'https://news.google.com/rss/search?q=home+loan+interest+rate+EMI&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Infrastructure',
            'url': 'https://news.google.com/rss/search?q=india+infrastructure+metro+highway+smart+city&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Real Estate Developers',
            'url': 'https://news.google.com/rss/search?q=DLF+Godrej+Oberoi+Prestige+real+estate&hl=en-IN&gl=IN&ceid=IN:en'
        }
    ]

    all_articles = []

    for feed_config in rss_feeds:
        try:
            logger.info(f"  Fetching: {feed_config['name']}...")
            feed = feedparser.parse(feed_config['url'])

            for entry in feed.entries[:10]:  # Limit to 10 per feed
                # Generate unique ID
                article_id = hashlib.md5(entry.get('link', '').encode()).hexdigest()

                # Parse date
                published_at = datetime.now(IST).isoformat()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        utc_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                        published_at = utc_dt.astimezone(IST).isoformat()
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Could not parse published date for {entry.get('link', 'unknown')}: {e}")

                article = {
                    'id': article_id,
                    'title': entry.get('title', 'No title'),
                    'url': entry.get('link', ''),
                    'source': feed_config['name'],
                    'content': entry.get('summary', entry.get('description', '')),
                    'published_at': published_at,
                    'scraped_at': datetime.now(IST).isoformat(),
                    'category': 'general'
                }
                all_articles.append(article)

            logger.info(f"    Got {min(10, len(feed.entries))} articles")

        except Exception as e:
            logger.error(f"  {feed_config['name']}: Failed - {e}")

    logger.info(f"Total scraped: {len(all_articles)} articles")

    # Save to temp file
    with open(ARTICLES_FILE, 'w') as f:
        json.dump(all_articles, f, default=str)

    return all_articles


def process_articles():
    """Process and deduplicate articles"""
    logger.info("Processing articles...")

    # Load scraped articles
    if not os.path.exists(ARTICLES_FILE):
        logger.warning("No articles file found. Creating empty.")
        all_articles = []
    else:
        with open(ARTICLES_FILE, 'r') as f:
            all_articles = json.load(f)

    if not all_articles:
        logger.warning("No articles to process")
        # Save empty list
        with open(PROCESSED_FILE, 'w') as f:
            json.dump([], f)
        return []

    # Load already sent articles to avoid duplicates
    sent_ids = load_sent_articles()
    logger.info(f"Loaded {len(sent_ids)} previously sent article IDs")

    # Simple deduplication by title similarity
    seen_titles = set()
    processed = []

    for article in all_articles:
        # Skip if already sent in previous digests
        if article.get('id') in sent_ids:
            continue

        # Normalize title for comparison
        title_key = article.get('title', '').lower()[:50]

        if title_key not in seen_titles:
            seen_titles.add(title_key)

            # Simple categorization based on keywords
            title_lower = article.get('title', '').lower()
            content_lower = article.get('content', '').lower()
            text = title_lower + ' ' + content_lower

            # MUST have at least one real estate keyword
            has_real_estate = any(kw in text for kw in REAL_ESTATE_KEYWORDS)
            if not has_real_estate:
                continue  # Skip non-real estate articles

            if any(kw in text for kw in ['rera', 'regulation', 'policy', 'government', 'pmay']):
                article['category'] = 'policy'
            elif any(kw in text for kw in ['price', 'rate', 'market', 'demand', 'sales']):
                article['category'] = 'market_updates'
            elif any(kw in text for kw in ['metro', 'infrastructure', 'airport', 'highway', 'smart city']):
                article['category'] = 'infrastructure'
            elif any(kw in text for kw in ['launch', 'new project', 'upcoming', 'new development']):
                article['category'] = 'launches'
            elif any(kw in text for kw in ['loan', 'emi', 'interest', 'rbi', 'mortgage']):
                article['category'] = 'finance'

            processed.append(article)

    logger.info(f"Processed: {len(processed)} unique articles (from {len(all_articles)})")

    # Save processed articles
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(processed, f, default=str)

    return processed


async def send_telegram():
    """Send digest via Telegram"""
    logger.info("Sending Telegram notification...")

    # Get credentials from environment
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    digest_type = os.getenv('DIGEST_TYPE', 'morning')

    if not bot_token or not chat_id:
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set!")
        sys.exit(1)

    # Load processed articles
    if not os.path.exists(PROCESSED_FILE):
        logger.warning("No processed articles file. Sending empty digest.")
        articles = []
    else:
        with open(PROCESSED_FILE, 'r') as f:
            articles = json.load(f)

    # Format message
    message = format_telegram_message(articles, digest_type)

    # Send via Telegram API
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }

        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info(f"Telegram digest sent! ({len(articles)} articles)")

                    # Mark articles as sent to avoid duplicates
                    sent_ids = load_sent_articles()
                    for article in articles:
                        if article.get('id'):
                            sent_ids.add(article['id'])
                    save_sent_articles(sent_ids)
                else:
                    error = await response.text()
                    logger.error(f"Telegram send failed: {error}")
                    sys.exit(1)
        except asyncio.TimeoutError:
            logger.error("Telegram API request timed out after 30s")
            sys.exit(1)
        except aiohttp.ClientError as e:
            logger.error(f"Telegram API request failed: {e}")
            sys.exit(1)


async def send_email():
    """Send digest via Email"""
    logger.info("Sending Email notification...")

    # Get credentials from environment
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    raw_port = os.getenv('SMTP_PORT')
    try:
        smtp_port = int(raw_port) if raw_port else 587
    except ValueError:
        logger.warning(f"Invalid SMTP_PORT value '{raw_port}', defaulting to 587")
        smtp_port = 587
    username = os.getenv('SMTP_USERNAME')
    password = os.getenv('SMTP_PASSWORD')
    sender = os.getenv('SMTP_USERNAME')
    recipient = os.getenv('EMAIL_RECIPIENT')
    digest_type = os.getenv('DIGEST_TYPE', 'morning')

    if not all([username, password, recipient]):
        logger.error("Email credentials not fully configured!")
        sys.exit(1)

    # Load processed articles
    if not os.path.exists(PROCESSED_FILE):
        logger.warning("No processed articles. Sending empty digest.")
        articles = []
    else:
        with open(PROCESSED_FILE, 'r') as f:
            articles = json.load(f)

    # Format email
    subject = f"Khabri {digest_type.title()} Digest - {datetime.now().strftime('%B %d, %Y')}"
    body = format_email_message(articles, digest_type)

    # Send via SMTP
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    html_part = MIMEText(body, 'html')
    msg.attach(html_part)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(sender, [recipient], msg.as_string())

        logger.info(f"Email digest sent to {recipient}!")

    except Exception as e:
        logger.error(f"Email send failed: {e}")
        sys.exit(1)


def format_telegram_message(articles, digest_type):
    """Format articles for Telegram"""
    now_ist = datetime.now(IST)
    date_str = now_ist.strftime('%B %d, %Y')
    time_str = now_ist.strftime('%I:%M %p')

    header = "🌅 Morning" if digest_type == "morning" else "🌆 Evening"

    lines = [
        f"<b>{header} News Digest</b>",
        f"📅 {date_str} | ⏰ {time_str}",
        f"📊 {len(articles)} articles",
        "",
        "━━━━━━━━━━━━━━━━━━━━"
    ]

    if not articles:
        lines.append("")
        lines.append("No new articles found today.")
    else:
        # Group by category
        categories = {}
        for article in articles[:15]:
            cat = article.get('category', 'general')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(article)

        for category, cat_articles in categories.items():
            lines.append("")
            lines.append(f"📁 <b>{category.upper().replace('_', ' ')}</b>")

            for article in cat_articles[:4]:
                title = html_module.escape(article.get('title', 'No title')[:70])
                url = html_module.escape(article.get('url', ''), quote=True)
                source = html_module.escape(article.get('source', 'Unknown').replace('Google News - ', ''))

                lines.append(f"")
                if url:
                    lines.append(f"• <a href='{url}'>{title}</a>")
                else:
                    lines.append(f"• {title}")
                lines.append(f"  📰 {source}")

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("🤖 <i>Powered by Khabri</i>")
    lines.append("⚡ <i>Auto-delivered via GitHub Actions</i>")

    return "\n".join(lines)


def format_email_message(articles, digest_type):
    """Format articles as HTML email"""
    now_ist = datetime.now(IST)
    date_str = now_ist.strftime('%B %d, %Y')

    header = "🌅 Morning" if digest_type == "morning" else "🌆 Evening"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 15px; margin-bottom: 20px; }}
            .meta {{ color: #7f8c8d; font-size: 14px; margin-bottom: 25px; }}
            .category {{ background: linear-gradient(135deg, #3498db, #2980b9); color: white; padding: 8px 20px; margin: 25px 0 15px 0; border-radius: 5px; font-weight: bold; }}
            .article {{ background: #f9f9f9; padding: 20px; margin: 15px 0; border-left: 4px solid #3498db; border-radius: 0 5px 5px 0; }}
            .article h3 {{ margin: 0 0 10px 0; color: #2c3e50; font-size: 16px; }}
            .article .source {{ color: #7f8c8d; font-size: 12px; margin-top: 10px; }}
            .article a {{ color: #3498db; text-decoration: none; }}
            .article a:hover {{ text-decoration: underline; }}
            .footer {{ text-align: center; color: #95a5a6; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }}
            .empty {{ text-align: center; padding: 40px; color: #95a5a6; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{header} News Digest</h1>
            <div class="meta">📅 {date_str} | 📊 {len(articles)} articles</div>
    """

    if not articles:
        html += '<div class="empty"><p>No new articles found today.</p></div>'
    else:
        categories = {}
        for article in articles[:15]:
            cat = article.get('category', 'general')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(article)

        for category, cat_articles in categories.items():
            html += f'<div class="category">{category.upper().replace("_", " ")}</div>'

            for article in cat_articles[:4]:
                title = html_module.escape(article.get('title', 'No title'))
                raw_url = article.get('url', '')
                safe_url = html_module.escape(raw_url, quote=True)
                source = html_module.escape(article.get('source', 'Unknown').replace('Google News - ', ''))

                html += f'''
                <div class="article">
                    <h3>{'<a href="' + safe_url + '">' + title + '</a>' if raw_url else title}</h3>
                    <div class="source">📰 {source}</div>
                </div>
                '''

    html += """
            <div class="footer">
                🤖 Powered by <strong>Khabri News Intelligence</strong><br>
                ⚡ Auto-delivered via GitHub Actions
            </div>
        </div>
    </body>
    </html>
    """

    return html


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python github_digest_runner.py [scrape|process|notify] [telegram|email]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'scrape':
        scrape_rss_feeds()

    elif command == 'process':
        process_articles()

    elif command == 'notify':
        if len(sys.argv) < 3:
            print("Usage: python github_digest_runner.py notify [telegram|email]")
            sys.exit(1)

        channel = sys.argv[2]

        if channel == 'telegram':
            asyncio.run(send_telegram())
        elif channel == 'email':
            asyncio.run(send_email())
        else:
            print(f"Unknown channel: {channel}")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
