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
import html as html_module
import asyncio
import logging
import hashlib
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

# IST timezone (UTC + 5:30)
IST = timezone(timedelta(hours=5, minutes=30))

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import feedparser
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('BudgetAlert')

# Temp files - use tempfile module for cross-platform compatibility
_temp_dir = tempfile.gettempdir()
ARTICLES_FILE = os.path.join(_temp_dir, 'budget_articles.json')
PROCESSED_FILE = os.path.join(_temp_dir, 'budget_processed.json')

# Persistent sent tracking - use environment variable or file in repo
# GitHub Actions will pass SENT_CACHE_DIR if available
CACHE_DIR = os.getenv('GITHUB_WORKSPACE', _temp_dir)
SENT_FILE = os.path.join(CACHE_DIR, '.khabri_cache', 'budget_sent.json')

# =============================================================================
# ACTUAL BUDGET ANNOUNCEMENT KEYWORDS
# Focus on what WAS announced, not speculation about what WILL be announced
# =============================================================================

# Keywords indicating ACTUAL announcements (not speculation)
ANNOUNCEMENT_KEYWORDS = [
    'announced',
    'announces',
    'declared',
    'unveils',
    'unveiled',
    'proposed',
    'proposes',
    'allocates',
    'allocated',
    'allocation',
    'hiked',
    'raised',
    'reduced',
    'cut',
    'increased',
    'decreased',
    'extended',
    'launched',
    'introduced',
    'revised',
    'changed',
    'approved',
    'sanctioned',
    'crore allocated',
    'lakh crore',
    'budget outlay',
    'tax relief',
    'tax benefit',
    'deduction limit',
    'exemption limit',
]

# EXCLUDE these speculation/wishlist keywords (STRICT FILTERING)
SPECULATION_KEYWORDS = [
    # Questions - NOT announcements
    'will real estate',
    'will housing',
    'will get',
    'can we expect',
    'what to expect',
    'will it get',
    '?',  # Questions in title
    # Wishlist/demands - NOT announcements
    'key demands',
    'demands of',
    'demands from',
    'wishlist',
    'expectations from',
    'hopes for',
    'seeking',
    'seeks',
    'urges',
    'requests',
    'wants from',
    'push for',
    'appeal',
    'looking for',
    'need from',
    'wants',
    # Market reaction/analysis - NOT announcements
    'shares to benefit',
    'stocks to buy',
    'stocks to watch',
    'benefit from',
    'impact on stocks',
    'market reaction',
    # Speculation words
    'may announce',
    'likely to',
    'expected to',
    'could announce',
    'might propose',
    'anticipate',
    'speculation',
    'may get',
    'could get',
    'might get',
    # Pre-budget content
    'preview',
    'ahead of budget',
    'before budget',
    'pre-budget',
    'budget eve',
    'on the eve',
    # Opinion/should articles
    'should announce',
    'must announce',
    'needs to announce',
    'should focus',
    'must focus',
]

# REAL ESTATE & INFRASTRUCTURE - MUST have at least one
REAL_ESTATE_KEYWORDS = [
    'real estate',
    'housing',
    'property',
    'home loan',
    'affordable housing',
    'pmay',
    'pradhan mantri awas',
    'stamp duty',
    'infrastructure',
    'smart city',
    'metro',
    'rera',
    'construction',
    'builder',
    'developer',
    'residential',
    'commercial property',
    'realty',
    'home buyer',
    'rental',
    'gst housing',
    'capital gains property',
    'section 24',
    'section 80eea',
    'home ownership',
    'urban development',
    'highway',
    'expressway',
    'airport',
    'housing sector',
    'real estate sector',
    'property tax',
    'home buyers',
]

# Boost for specific amounts/allocations (indicates real announcement)
AMOUNT_PATTERNS = [
    '₹',
    'crore',
    'lakh crore',
    'billion',
    'rs ',
    'rs.',
    'inr',
    '%',
    'percent',
]


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
        # Ensure cache directory exists
        cache_dir = os.path.dirname(SENT_FILE)
        os.makedirs(cache_dir, exist_ok=True)

        if os.path.exists(SENT_FILE):
            with open(SENT_FILE, 'r') as f:
                data = json.load(f)
                # Handle both old format (list) and new format (dict with timestamp)
                if isinstance(data, list):
                    return OrderedSet(data)
                return OrderedSet(data.get('ids', []))
    except Exception as e:
        logger.warning(f"Could not load sent articles: {e}")
    return OrderedSet()


def save_sent_articles(sent_ids):
    """Save sent article IDs with timestamp for cleanup"""
    try:
        cache_dir = os.path.dirname(SENT_FILE)
        os.makedirs(cache_dir, exist_ok=True)

        # Keep only last 200 IDs to prevent bloat (preserves insertion order)
        ids_list = sent_ids.to_list()[-200:]

        with open(SENT_FILE, 'w') as f:
            json.dump({
                'ids': ids_list,
                'updated': datetime.now(IST).isoformat(),
                'count': len(ids_list)
            }, f, indent=2)
        logger.info(f"Saved {len(ids_list)} sent article IDs")
    except Exception as e:
        logger.error(f"Could not save sent articles: {e}")


def scrape_budget_news():
    """Scrape budget-related news"""
    logger.info("🏛️ Scraping Budget 2026 news...")

    # RSS feeds for ACTUAL BUDGET ANNOUNCEMENTS
    # Using "when:1d" to get only today's news
    # Focus on past-tense verbs: "announced", "allocated", "hiked", "cut"
    rss_feeds = [
        {
            'name': 'FM Announces Housing',
            'url': 'https://news.google.com/rss/search?q=sitharaman+announces+housing+crore+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Budget Housing Allocated',
            'url': 'https://news.google.com/rss/search?q=budget+2026+housing+allocated+crore+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'PMAY Allocation Announced',
            'url': 'https://news.google.com/rss/search?q=PMAY+allocation+announced+crore+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Infrastructure Allocation',
            'url': 'https://news.google.com/rss/search?q=budget+infrastructure+lakh+crore+allocated+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Home Loan Tax Benefit',
            'url': 'https://news.google.com/rss/search?q=budget+home+loan+tax+deduction+increased+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Real Estate Budget Highlights',
            'url': 'https://news.google.com/rss/search?q=budget+real+estate+announced+highlights+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Stamp Duty Changes',
            'url': 'https://news.google.com/rss/search?q=budget+stamp+duty+reduced+changed+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Metro Highway Sanctioned',
            'url': 'https://news.google.com/rss/search?q=budget+metro+highway+crore+sanctioned+approved+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        }
    ]

    all_articles = []

    for feed_config in rss_feeds:
        try:
            logger.info(f"  Fetching: {feed_config['name']}...")
            feed = feedparser.parse(feed_config['url'])

            for entry in feed.entries[:15]:
                article_id = hashlib.md5(entry.get('link', '').encode()).hexdigest()

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
                    'content': entry.get('summary', ''),
                    'published_at': published_at,
                    'scraped_at': datetime.now(IST).isoformat()
                }
                all_articles.append(article)

            logger.info(f"    Got {min(15, len(feed.entries))} articles")

        except Exception as e:
            logger.error(f"  {feed_config['name']}: Failed - {e}")

    logger.info(f"Total scraped: {len(all_articles)} articles")

    with open(ARTICLES_FILE, 'w') as f:
        json.dump(all_articles, f, default=str)

    return all_articles


def is_within_event_window(published_str):
    """Check if article was published during event window (10:30 AM - 2:30 PM IST today) or within last 3 hours"""
    try:
        # Parse the published time
        published = datetime.fromisoformat(published_str.replace('Z', '+00:00'))

        # Get current IST time
        now_ist = datetime.now(IST)

        # If published time is naive (no timezone), assume IST
        if published.tzinfo is None:
            published = published.replace(tzinfo=IST)

        # Convert to IST for comparison
        published_ist = published.astimezone(IST)

        # Enforce recency: only articles from today or yesterday
        days_diff = (now_ist.date() - published_ist.date()).days
        if days_diff > 1:
            return False

        # Event window: 10:30 AM - 2:30 PM IST on the article's publication date
        event_start = published_ist.replace(hour=10, minute=30, second=0, microsecond=0)
        event_end = published_ist.replace(hour=14, minute=30, second=0, microsecond=0)

        # Accept articles if published within event window on their publication date
        if event_start <= published_ist <= event_end:
            return True

        # Also accept articles from last 3 hours (for post-event coverage)
        three_hours_ago = now_ist - timedelta(hours=3)
        return published_ist >= three_hours_ago
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse date: {published_str} - {e}")
        # If we can't parse, include it (to avoid missing important news)
        return True


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

        # STEP 0: Check if article is from event window (recent articles only)
        published_at = article.get('published_at', '')
        if not is_within_event_window(published_at):
            logger.debug(f"Skipping old article: {article.get('title', '')[:50]}")
            continue

        # Check keywords in title and content
        title = article.get('title', '').lower()
        content = article.get('content', '').lower()
        text = title + ' ' + content

        # STEP 1: MUST have real estate/infrastructure keyword
        real_estate_matches = [kw for kw in REAL_ESTATE_KEYWORDS if kw in text]
        if not real_estate_matches:
            continue  # Skip non-real estate news

        # STEP 2: EXCLUDE speculation articles (STRICT CHECK)
        is_speculation = any(kw in text for kw in SPECULATION_KEYWORDS)
        if is_speculation:
            logger.info(f"Skipping speculation: {title[:60]}")
            continue  # Skip speculation/preview articles

        # STEP 3: MUST have announcement indicator (strict for event alerts)
        announcement_matches = [kw for kw in ANNOUNCEMENT_KEYWORDS if kw in text]
        has_amounts = any(kw in text for kw in AMOUNT_PATTERNS)

        # During event: REQUIRE announcement keywords or amounts
        if not announcement_matches and not has_amounts:
            logger.info(f"Skipping non-announcement: {title[:60]}")
            continue  # Skip if no announcement indicator

        # Calculate relevance score
        relevance_score = 0
        relevance_score += len(real_estate_matches) * 2
        relevance_score += len(announcement_matches) * 3
        relevance_score += 5 if has_amounts else 0

        article['relevance_score'] = relevance_score
        article['is_announcement'] = True
        article['matched_keywords'] = real_estate_matches[:3] + announcement_matches[:2]
        processed.append(article)

    # Sort by relevance
    processed.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

    # Limit to top 10
    processed = processed[:10]

    logger.info(f"Filtered: {len(processed)} budget-relevant articles")

    with open(PROCESSED_FILE, 'w') as f:
        json.dump(processed, f, default=str)

    return processed


async def send_telegram_alert():
    """Send budget alert via Telegram"""
    logger.info("Sending Budget alert via Telegram...")

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
        except asyncio.TimeoutError:
            logger.error("Telegram API request timed out after 30s")
            sys.exit(1)
        except aiohttp.ClientError as e:
            logger.error(f"Telegram API request failed: {e}")
            sys.exit(1)


def format_budget_alert(articles):
    """Format budget alert message"""
    # Convert to IST timezone
    now_ist = datetime.now(IST)
    time_str = now_ist.strftime('%I:%M %p')

    lines = [
        "🏛️ <b>UNION BUDGET 2026 - LIVE UPDATE</b>",
        f"⏰ {time_str} IST",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        ""
    ]

    for i, article in enumerate(articles[:5], 1):
        title = html_module.escape(article.get('title', 'No title')[:80])
        url = html_module.escape(article.get('url', ''), quote=True)
        keywords = [html_module.escape(kw) for kw in article.get('matched_keywords', [])[:3]]

        if url:
            lines.append(f'<b>{i}.</b> <a href="{url}">{title}</a>')
        else:
            lines.append(f"<b>{i}.</b> {title}")
        if keywords:
            keyword_str = ', '.join(keywords)
            lines.append(f"   🏷️ {keyword_str}")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("🔔 <i>Live alerts every 10 min during Budget</i>")
    lines.append("🤖 <i>Powered by Khabri</i>")

    return "\n".join(lines)


def send_email_alert():
    """Send budget alert via Email"""
    logger.info("Sending Budget alert via Email...")

    smtp_host = os.getenv('SMTP_HOST')
    raw_port = os.getenv('SMTP_PORT')
    try:
        smtp_port = int(raw_port) if raw_port else 587
    except ValueError:
        logger.warning(f"Invalid SMTP_PORT value '{raw_port}', defaulting to 587")
        smtp_port = 587
    username = os.getenv('SMTP_USERNAME')
    password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('SMTP_USERNAME')
    to_email = os.getenv('EMAIL_RECIPIENT')

    if not all([smtp_host, username, password, from_email, to_email]):
        logger.error("Email credentials not set!")
        sys.exit(1)

    if not os.path.exists(PROCESSED_FILE):
        logger.warning("No processed articles")
        return

    with open(PROCESSED_FILE, 'r') as f:
        articles = json.load(f)

    if not articles:
        logger.info("No new budget articles to email")
        return

    # Format email - use IST timezone
    now_ist = datetime.now(IST)
    time_str = now_ist.strftime('%I:%M %p')
    date_str = now_ist.strftime('%B %d, %Y')

    subject = f"🏛️ Budget 2026 Live Update - {time_str} IST"

    # HTML email body
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #1a5f7a, #2d8b74); color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0;">🏛️ UNION BUDGET 2026</h1>
            <p style="margin: 5px 0;">LIVE UPDATE - {time_str} IST</p>
            <p style="margin: 5px 0; font-size: 12px;">{date_str}</p>
        </div>

        <div style="padding: 20px;">
            <h2 style="color: #1a5f7a; border-bottom: 2px solid #1a5f7a; padding-bottom: 10px;">
                📰 Latest Budget News
            </h2>
    """

    for i, article in enumerate(articles[:5], 1):
        title = html_module.escape(article.get('title', 'No title'))
        raw_url = article.get('url', '')
        safe_url = html_module.escape(raw_url, quote=True)
        keywords = [html_module.escape(kw) for kw in article.get('matched_keywords', [])[:3]]

        html_body += f"""
            <div style="margin-bottom: 20px; padding: 15px; background: #f5f5f5; border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0; color: #333;">
                    {i}. <a href="{safe_url}" style="color: #1a5f7a; text-decoration: none;">{title}</a>
                </h3>
                <p style="margin: 5px 0; color: #666; font-size: 12px;">
                    🏷️ {', '.join(keywords) if keywords else 'Budget News'}
                </p>
            </div>
        """

    html_body += """
        </div>

        <div style="background: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; color: #666;">
            <p>🔔 Live alerts every 10 minutes during Budget presentation</p>
            <p>🤖 Powered by Khabri News Intelligence</p>
        </div>
    </body>
    </html>
    """

    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    # Attach HTML
    msg.attach(MIMEText(html_body, 'html'))

    # Send email
    try:
        recipients = [addr.strip() for addr in to_email.split(',') if addr.strip()]
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(username, password)
                server.sendmail(from_email, recipients, msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.sendmail(from_email, recipients, msg.as_string())

        # Mark articles as sent to avoid duplicates
        sent_ids = load_sent_articles()
        for article in articles:
            sent_ids.add(article['id'])
        save_sent_articles(sent_ids)

        logger.info(f"Budget email sent! ({len(articles)} articles)")
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        sys.exit(1)


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
        # Support both old and new format
        if len(sys.argv) > 2:
            channel = sys.argv[2]
            if channel == 'telegram':
                asyncio.run(send_telegram_alert())
            elif channel == 'email':
                send_email_alert()
            else:
                print(f"Unknown channel: {channel}")
                sys.exit(1)
        else:
            # Default: send to telegram only (backward compatible)
            asyncio.run(send_telegram_alert())
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
