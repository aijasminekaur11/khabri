#!/usr/bin/env python3
"""
GitHub Actions Digest Runner
Khabri - News Intelligence System

This script is called by GitHub Actions to:
1. Scrape news from sources
2. Process articles through pipeline
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
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers import NewsScraper, RSSReader, CompetitorTracker
from src.processors import ProcessorPipeline
from src.notifiers import TelegramNotifier, EmailNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('GitHubDigest')

# Temp file to store scraped articles between steps
ARTICLES_FILE = '/tmp/khabri_articles.json'
PROCESSED_FILE = '/tmp/khabri_processed.json'


async def scrape_news():
    """Scrape news from all sources"""
    logger.info("Starting news scraping...")

    all_articles = []

    # RSS feeds (most reliable for GitHub Actions)
    rss_feeds = [
        {
            'name': 'Google News - Real Estate',
            'url': 'https://news.google.com/rss/search?q=indian+real+estate&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Google News - Property',
            'url': 'https://news.google.com/rss/search?q=india+property+prices&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Google News - Housing',
            'url': 'https://news.google.com/rss/search?q=india+housing+market&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Google News - RERA',
            'url': 'https://news.google.com/rss/search?q=RERA+india&hl=en-IN&gl=IN&ceid=IN:en'
        },
        {
            'name': 'Google News - Mumbai Property',
            'url': 'https://news.google.com/rss/search?q=mumbai+property&hl=en-IN&gl=IN&ceid=IN:en'
        }
    ]

    rss_reader = RSSReader()

    for feed in rss_feeds:
        try:
            articles = await rss_reader.fetch_feed(feed['url'])
            for article in articles:
                article['source'] = feed['name']
            all_articles.extend(articles)
            logger.info(f"  {feed['name']}: {len(articles)} articles")
        except Exception as e:
            logger.error(f"  {feed['name']}: Failed - {e}")

    logger.info(f"Total scraped: {len(all_articles)} articles")

    # Save to temp file
    with open(ARTICLES_FILE, 'w') as f:
        json.dump(all_articles, f, default=str)

    return all_articles


async def process_articles():
    """Process scraped articles through pipeline"""
    logger.info("Processing articles...")

    # Load scraped articles
    if not os.path.exists(ARTICLES_FILE):
        logger.error("No articles file found. Run scrape first.")
        return []

    with open(ARTICLES_FILE, 'r') as f:
        articles = json.load(f)

    if not articles:
        logger.warning("No articles to process")
        return []

    # Initialize pipeline
    pipeline = ProcessorPipeline(
        enable_deduplication=True,
        enable_categorization=True,
        enable_summarization=True,
        enable_celebrity_matching=True
    )

    # Process articles
    processed = pipeline.process(articles)

    logger.info(f"Processed: {len(processed)} articles (from {len(articles)})")

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
        logger.error("No processed articles. Run process first.")
        sys.exit(1)

    with open(PROCESSED_FILE, 'r') as f:
        articles = json.load(f)

    if not articles:
        logger.warning("No articles to send")
        # Send empty digest notification
        articles = []

    # Format message
    message = format_digest_message(articles, digest_type)

    # Send via Telegram
    notifier = TelegramNotifier(
        bot_token=bot_token,
        default_chat_id=chat_id
    )

    await notifier.send_message(message)
    logger.info(f"Telegram digest sent! ({len(articles)} articles)")


async def send_email():
    """Send digest via Email"""
    logger.info("Sending Email notification...")

    # Get credentials from environment (matching your .env variable names)
    smtp_host = os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('EMAIL_SMTP_PORT', 587))
    username = os.getenv('EMAIL_USERNAME')
    password = os.getenv('EMAIL_PASSWORD')
    sender = os.getenv('EMAIL_FROM')
    recipient = os.getenv('EMAIL_TO')
    digest_type = os.getenv('DIGEST_TYPE', 'morning')

    if not all([username, password, recipient]):
        logger.error("Email credentials not fully configured!")
        sys.exit(1)

    # Load processed articles
    if not os.path.exists(PROCESSED_FILE):
        logger.error("No processed articles. Run process first.")
        sys.exit(1)

    with open(PROCESSED_FILE, 'r') as f:
        articles = json.load(f)

    # Format message
    message = format_digest_message(articles, digest_type, html=True)
    subject = f"Khabri {digest_type.title()} Digest - {datetime.now().strftime('%B %d, %Y')}"

    # Send via Email
    notifier = EmailNotifier(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        username=username,
        password=password,
        sender_email=sender or username,
        default_recipients=[recipient]
    )

    await notifier.send_email(subject=subject, body=message, html=True)
    logger.info(f"Email digest sent to {recipient}!")


def format_digest_message(articles, digest_type, html=False):
    """Format articles into a digest message"""
    now = datetime.now()
    date_str = now.strftime('%B %d, %Y')
    time_str = now.strftime('%I:%M %p')

    if html:
        return format_html_digest(articles, digest_type, date_str)
    else:
        return format_text_digest(articles, digest_type, date_str, time_str)


def format_text_digest(articles, digest_type, date_str, time_str):
    """Format as plain text (for Telegram)"""
    header = "🌅 Morning" if digest_type == "morning" else "🌆 Evening"

    lines = [
        f"{header} News Digest",
        f"📅 {date_str} | ⏰ {time_str}",
        f"📊 {len(articles)} articles",
        "",
        "━" * 30,
    ]

    if not articles:
        lines.append("")
        lines.append("No new articles found today.")
        lines.append("")
    else:
        # Group by category
        categories = {}
        for article in articles[:15]:  # Limit to 15
            cat = article.get('category', 'general')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(article)

        for category, cat_articles in categories.items():
            lines.append("")
            lines.append(f"📁 {category.upper().replace('_', ' ')}")

            for article in cat_articles[:5]:
                title = article.get('title', 'No title')[:80]
                source = article.get('source', 'Unknown')
                url = article.get('url', article.get('link', ''))

                lines.append(f"")
                lines.append(f"• {title}")
                lines.append(f"  📰 {source}")
                if url:
                    lines.append(f"  🔗 {url}")

    lines.append("")
    lines.append("━" * 30)
    lines.append("🤖 Powered by Khabri News Intelligence")
    lines.append("⚡ Auto-delivered via GitHub Actions")

    return "\n".join(lines)


def format_html_digest(articles, digest_type, date_str):
    """Format as HTML (for Email)"""
    header = "🌅 Morning" if digest_type == "morning" else "🌆 Evening"

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            .meta {{ color: #7f8c8d; font-size: 14px; margin-bottom: 20px; }}
            .category {{ background: #3498db; color: white; padding: 5px 15px; margin: 20px 0 10px 0; border-radius: 3px; }}
            .article {{ background: #f9f9f9; padding: 15px; margin: 10px 0; border-left: 3px solid #3498db; }}
            .article h3 {{ margin: 0 0 10px 0; color: #2c3e50; }}
            .article .source {{ color: #7f8c8d; font-size: 12px; }}
            .article a {{ color: #3498db; text-decoration: none; }}
            .footer {{ text-align: center; color: #95a5a6; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px; }}
        </style>
    </head>
    <body>
        <h1>{header} News Digest</h1>
        <div class="meta">📅 {date_str} | 📊 {len(articles)} articles</div>
    """

    if not articles:
        html += "<p>No new articles found today.</p>"
    else:
        categories = {}
        for article in articles[:15]:
            cat = article.get('category', 'general')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(article)

        for category, cat_articles in categories.items():
            html += f'<div class="category">{category.upper().replace("_", " ")}</div>'

            for article in cat_articles[:5]:
                title = article.get('title', 'No title')
                source = article.get('source', 'Unknown')
                url = article.get('url', article.get('link', ''))
                summary = article.get('summary', '')[:200] if article.get('summary') else ''

                html += f'''
                <div class="article">
                    <h3>{title}</h3>
                    <div class="source">📰 {source}</div>
                    {f'<p>{summary}...</p>' if summary else ''}
                    {f'<a href="{url}">Read more →</a>' if url else ''}
                </div>
                '''

    html += """
        <div class="footer">
            🤖 Powered by Khabri News Intelligence<br>
            ⚡ Auto-delivered via GitHub Actions
        </div>
    </body>
    </html>
    """

    return html


async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python github_digest_runner.py [scrape|process|notify] [telegram|email]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'scrape':
        await scrape_news()

    elif command == 'process':
        await process_articles()

    elif command == 'notify':
        if len(sys.argv) < 3:
            print("Usage: python github_digest_runner.py notify [telegram|email]")
            sys.exit(1)

        channel = sys.argv[2]

        if channel == 'telegram':
            await send_telegram()
        elif channel == 'email':
            await send_email()
        else:
            print(f"Unknown channel: {channel}")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
