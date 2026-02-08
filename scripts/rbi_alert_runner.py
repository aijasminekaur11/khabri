#!/usr/bin/env python3
"""
RBI Policy Review 2026 - Event Alert Runner
Khabri - News Intelligence System

High-frequency alerts during RBI Policy announcement
Scrapes RBI-specific news every 15 minutes during the event

Usage:
    python rbi_alert_runner.py scrape
    python rbi_alert_runner.py process
    python rbi_alert_runner.py notify
"""

import os
import sys
import json
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
logger = logging.getLogger('RBIAlert')

# Temp files - use tempfile module for cross-platform compatibility
_temp_dir = tempfile.gettempdir()
ARTICLES_FILE = os.path.join(_temp_dir, 'rbi_articles.json')
PROCESSED_FILE = os.path.join(_temp_dir, 'rbi_processed.json')

# Persistent sent tracking
CACHE_DIR = os.getenv('GITHUB_WORKSPACE', _temp_dir)
SENT_FILE = os.path.join(CACHE_DIR, '.khabri_cache', 'rbi_sent.json')

# =============================================================================
# RBI POLICY ACTUAL DECISION KEYWORDS
# Focus on what WAS decided, not speculation
# =============================================================================

# Keywords indicating ACTUAL RBI decisions
DECISION_KEYWORDS = [
    'cuts repo',
    'hikes repo',
    'keeps repo',
    'unchanged',
    'raised to',
    'reduced to',
    'cut by',
    'hiked by',
    'basis points',
    'bps',
    'announces',
    'announced',
    'decides',
    'decided',
    'maintains',
    'slashes',
    'increases',
    'decreases',
    'policy rate',
    'rate decision',
    'mpc decision',
    'mpc announces',
    'governor announces',
]

# EXCLUDE speculation/prediction articles (STRICT)
RBI_SPECULATION = [
    # Speculation verbs
    'may cut',
    'may hike',
    'may keep',
    'likely to',
    'expected to',
    'could cut',
    'could hike',
    'might raise',
    'might reduce',
    # Questions
    'will rbi',
    'will mpc',
    '?',
    # Prediction/forecast
    'speculation',
    'anticipate',
    'forecast',
    'prediction',
    'expects',
    'expecting',
    'polls suggest',
    # Pre-event
    'ahead of mpc',
    'ahead of rbi',
    'before rbi',
    'before mpc',
    'what to expect',
    'preview',
    # Wishlist/demands
    'demands',
    'seeks',
    'wants',
    'urges',
    'appeals',
    'hopes',
    # Market speculation
    'stocks to buy',
    'shares to benefit',
    'benefit from',
]

# RBI policy keywords
RBI_KEYWORDS = [
    'rbi',
    'reserve bank',
    'repo rate',
    'reverse repo',
    'interest rate',
    'monetary policy',
    'mpc',
    'shaktikanta das',
    'lending rate',
    'credit policy',
    'bank rate',
]

# MUST HAVE: Real estate / housing impact
REAL_ESTATE_MUST_HAVE = [
    'home loan',
    'housing',
    'real estate',
    'property',
    'emi',
    'mortgage',
    'home buyer',
    'affordability',
    'housing finance',
    'property loan',
    'residential',
    'home ownership',
    'housing market',
    'real estate sector',
    'realty',
    'housing demand',
    'home prices',
    'property prices',
    'emi change',
    'emi impact',
    'loan rate',
]


def load_sent_articles():
    """Load previously sent article IDs from persistent cache"""
    try:
        cache_dir = os.path.dirname(SENT_FILE)
        os.makedirs(cache_dir, exist_ok=True)

        if os.path.exists(SENT_FILE):
            with open(SENT_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return set(data)
                return set(data.get('ids', []))
    except Exception as e:
        logger.warning(f"Could not load sent articles: {e}")
    return set()


def save_sent_articles(sent_ids):
    """Save sent article IDs with timestamp"""
    try:
        cache_dir = os.path.dirname(SENT_FILE)
        os.makedirs(cache_dir, exist_ok=True)

        ids_list = list(sent_ids)[-200:]

        with open(SENT_FILE, 'w') as f:
            json.dump({
                'ids': ids_list,
                'updated': datetime.now(IST).isoformat(),
                'count': len(ids_list)
            }, f, indent=2)
        logger.info(f"Saved {len(ids_list)} sent article IDs")
    except Exception as e:
        logger.error(f"Could not save sent articles: {e}")


def scrape_rbi_news():
    """Scrape RBI-related news"""
    logger.info("🏦 Scraping RBI Policy news...")

    # RSS feeds for ACTUAL RBI DECISIONS (today only with when:1d)
    rss_feeds = [
        {
            'name': 'RBI Cuts/Hikes Repo',
            'url': 'https://news.google.com/rss/search?q=RBI+cuts+hikes+repo+rate+bps+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'MPC Announces Decision',
            'url': 'https://news.google.com/rss/search?q=MPC+announces+decision+repo+rate+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Home Loan EMI Impact',
            'url': 'https://news.google.com/rss/search?q=home+loan+EMI+RBI+rate+cut+impact+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'RBI Governor Announces',
            'url': 'https://news.google.com/rss/search?q=RBI+governor+announces+policy+decision+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Housing Finance Impact',
            'url': 'https://news.google.com/rss/search?q=housing+finance+RBI+rate+decision+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Real Estate RBI Decision',
            'url': 'https://news.google.com/rss/search?q=real+estate+RBI+decision+announces+when:1d&hl=en-IN&gl=IN&ceid=IN:en'
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


def is_within_event_window(published_str):
    """Check if article was published during/after event (recent only)"""
    try:
        published = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
        now_ist = datetime.now(IST)

        # If published time is naive, assume IST
        if published.tzinfo is None:
            published = published.replace(tzinfo=IST)

        # Only include articles from last 3 hours (during event)
        three_hours_ago = now_ist - timedelta(hours=3)
        return published >= three_hours_ago
    except Exception as e:
        logger.warning(f"Could not parse date: {published_str} - {e}")
        return True  # Include if can't parse


def process_rbi_articles():
    """Filter for RBI-relevant articles only"""
    logger.info("Processing RBI articles...")

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

        # STEP 0: Only recent articles (during event window)
        published_at = article.get('published_at', '')
        if not is_within_event_window(published_at):
            continue

        # Check for RBI keywords
        title = article.get('title', '').lower()
        content = article.get('content', '').lower()
        text = title + ' ' + content

        # STEP 1: MUST have real estate/housing related keyword
        has_real_estate = any(kw in text for kw in REAL_ESTATE_MUST_HAVE)
        if not has_real_estate:
            continue  # Skip non-real estate RBI news

        # STEP 2: EXCLUDE speculation articles (STRICT)
        is_speculation = any(kw in text for kw in RBI_SPECULATION)
        if is_speculation:
            logger.info(f"Skipping speculation: {title[:60]}")
            continue  # Skip speculation articles

        # STEP 3: MUST have decision indicator (strict for event)
        decision_matches = [kw for kw in DECISION_KEYWORDS if kw in text]
        has_percentage = '%' in text or 'basis points' in text or 'bps' in text

        # During event: REQUIRE decision keywords or percentages
        if not decision_matches and not has_percentage:
            logger.info(f"Skipping non-decision: {title[:60]}")
            continue

        # Calculate relevance score
        rbi_score = sum(1 for kw in RBI_KEYWORDS if kw in text)
        real_estate_score = sum(1 for kw in REAL_ESTATE_MUST_HAVE if kw in text)
        decision_score = len(decision_matches) * 3

        relevance_score = rbi_score + real_estate_score * 2 + decision_score
        relevance_score += 5 if has_percentage else 0

        article['relevance_score'] = relevance_score
        article['is_decision'] = True
        matched = decision_matches[:2] if decision_matches else []
        matched.extend([kw for kw in REAL_ESTATE_MUST_HAVE if kw in text][:2])
        article['matched_keywords'] = matched
        processed.append(article)

    # Sort by relevance
    processed.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

    # Limit to top 10
    processed = processed[:10]

    logger.info(f"Filtered: {len(processed)} RBI-relevant articles")

    with open(PROCESSED_FILE, 'w') as f:
        json.dump(processed, f, default=str)

    return processed


async def send_telegram_alert():
    """Send RBI alert via Telegram"""
    logger.info("Sending RBI alert via Telegram...")

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
        logger.info("No new RBI articles to send")
        return

    # Format message
    message = format_rbi_alert(articles)

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
                logger.info(f"RBI alert sent! ({len(articles)} articles)")

                # Mark articles as sent
                sent_ids = load_sent_articles()
                for article in articles:
                    sent_ids.add(article['id'])
                save_sent_articles(sent_ids)
            else:
                error = await response.text()
                logger.error(f"Telegram send failed: {error}")
                sys.exit(1)


def format_rbi_alert(articles):
    """Format RBI alert message"""
    # Convert to IST timezone
    now_ist = datetime.now(IST)
    time_str = now_ist.strftime('%I:%M %p')

    lines = [
        "🏦 <b>RBI POLICY REVIEW - LIVE UPDATE</b>",
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
            lines.append(f'<b>{i}.</b> <a href="{url}">{title}</a>')
        else:
            lines.append(f"<b>{i}.</b> {title}")
        if keywords:
            keyword_str = ', '.join(keywords[:3])
            lines.append(f"   🏷️ {keyword_str}")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("🔔 <i>Live alerts every 15 min during RBI Policy</i>")
    lines.append("🤖 <i>Powered by Khabri</i>")

    return "\n".join(lines)


def send_email_alert():
    """Send RBI alert via Email"""
    logger.info("Sending RBI alert via Email...")

    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
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
        logger.info("No new RBI articles to email")
        return

    # Format email - use IST timezone
    now_ist = datetime.now(IST)
    time_str = now_ist.strftime('%I:%M %p')
    date_str = now_ist.strftime('%B %d, %Y')

    subject = f"🏦 RBI Policy Live Update - {time_str} IST"

    # HTML email body
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #0d47a1, #1976d2); color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0;">🏦 RBI POLICY REVIEW</h1>
            <p style="margin: 5px 0;">LIVE UPDATE - {time_str} IST</p>
            <p style="margin: 5px 0; font-size: 12px;">{date_str}</p>
        </div>

        <div style="padding: 20px;">
            <h2 style="color: #0d47a1; border-bottom: 2px solid #0d47a1; padding-bottom: 10px;">
                📰 Latest RBI News
            </h2>
    """

    for i, article in enumerate(articles[:5], 1):
        title = article.get('title', 'No title')
        url = article.get('url', '')
        keywords = article.get('matched_keywords', [])[:3]

        html_body += f"""
            <div style="margin-bottom: 20px; padding: 15px; background: #f5f5f5; border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0; color: #333;">
                    {i}. <a href="{url}" style="color: #0d47a1; text-decoration: none;">{title}</a>
                </h3>
                <p style="margin: 5px 0; color: #666; font-size: 12px;">
                    🏷️ {', '.join(keywords[:3]) if keywords else 'RBI News'}
                </p>
            </div>
        """

    html_body += """
        </div>

        <div style="background: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; color: #666;">
            <p>🔔 Live alerts every 15 minutes during RBI Policy</p>
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
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(from_email, to_email.split(','), msg.as_string())
        logger.info(f"RBI email sent! ({len(articles)} articles)")
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python rbi_alert_runner.py [scrape|process|notify]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'scrape':
        scrape_rbi_news()
    elif command == 'process':
        process_rbi_articles()
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
