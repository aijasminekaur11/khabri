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

# Temp files
ARTICLES_FILE = '/tmp/rbi_articles.json'
PROCESSED_FILE = '/tmp/rbi_processed.json'
SENT_FILE = '/tmp/rbi_sent.json'  # Track already sent articles

# RBI-specific keywords
RBI_KEYWORDS = [
    'rbi',
    'reserve bank',
    'repo rate',
    'reverse repo',
    'interest rate',
    'monetary policy',
    'mpc',
    'shaktikanta das',
    'home loan rate',
    'emi',
    'lending rate',
    'inflation',
    'cpi',
    'liquidity',
    'credit policy',
    'bank rate',
    'cash reserve ratio',
    'crr',
    'slr',
    'housing finance',
    'mortgage rate',
    'real estate finance',
    'property loan',
    'home buyer',
    'affordability',
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


def scrape_rbi_news():
    """Scrape RBI-related news"""
    logger.info("🏦 Scraping RBI Policy news...")

    # RBI-specific RSS feeds
    rss_feeds = [
        {
            'name': 'RBI Policy',
            'url': 'https://news.google.com/rss/search?q=RBI+policy+repo+rate&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'RBI Interest Rate',
            'url': 'https://news.google.com/rss/search?q=RBI+interest+rate+home+loan&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'RBI MPC',
            'url': 'https://news.google.com/rss/search?q=RBI+MPC+monetary+policy&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Home Loan EMI',
            'url': 'https://news.google.com/rss/search?q=home+loan+EMI+rate+change&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'RBI Governor',
            'url': 'https://news.google.com/rss/search?q=RBI+governor+announcement&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Housing Finance',
            'url': 'https://news.google.com/rss/search?q=housing+finance+interest+rate&hl=en-IN&gl=IN&ceid=IN:en'
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

        # Check for RBI keywords
        text = (article.get('title', '') + ' ' + article.get('content', '')).lower()

        relevance_score = sum(1 for kw in RBI_KEYWORDS if kw in text)

        if relevance_score >= 1:  # At least 1 keyword match
            article['relevance_score'] = relevance_score
            article['matched_keywords'] = [kw for kw in RBI_KEYWORDS if kw in text]
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

    smtp_host = os.getenv('EMAIL_SMTP_HOST')
    smtp_port = int(os.getenv('EMAIL_SMTP_PORT', 587))
    username = os.getenv('EMAIL_USERNAME')
    password = os.getenv('EMAIL_PASSWORD')
    from_email = os.getenv('EMAIL_FROM')
    to_email = os.getenv('EMAIL_TO')

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
