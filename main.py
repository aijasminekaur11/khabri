#!/usr/bin/env python3
"""
Khabri - News Intelligence System
Main Runner Script

This script runs the news intelligence system continuously,
checking for scheduled digests and events.
"""

import os
import sys
import time
import signal
import logging
import asyncio
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Import pytz for timezone support
try:
    import pytz
    IST = pytz.timezone('Asia/Kolkata')
except ImportError:
    IST = None  # Will use system local time

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.orchestrator import Orchestrator
from src.scrapers import NewsScraper, RSSReader, CompetitorTracker, IGRSScraper
from src.notifiers import TelegramNotifier, EmailNotifier
from src.processors import ProcessorPipeline

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/khabri.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Khabri')


class KhabriRunner:
    """
    Main runner for the Khabri News Intelligence System
    """

    def __init__(self):
        self.running = False
        self.orchestrator: Optional[Orchestrator] = None
        self.telegram: Optional[TelegramNotifier] = None
        self.email: Optional[EmailNotifier] = None
        self.scrapers = {}

        # Track last digest times to avoid duplicates
        self.last_morning_digest = None
        self.last_evening_digest = None

    def initialize(self):
        """Initialize all components"""
        logger.info("=" * 60)
        logger.info("Initializing Khabri News Intelligence System...")
        logger.info("=" * 60)

        # Initialize orchestrator
        config_dir = os.path.join(os.path.dirname(__file__), 'config')
        self.orchestrator = Orchestrator(config_dir)
        self.orchestrator.initialize()

        # Initialize notifiers
        self._init_notifiers()

        # Initialize scrapers
        self._init_scrapers()

        logger.info("Khabri initialized successfully!")
        self._print_config_summary()

    def _init_notifiers(self):
        """Initialize notification channels"""
        # Telegram
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if telegram_token and telegram_chat_id:
            self.telegram = TelegramNotifier(
                bot_token=telegram_token,
                default_chat_id=telegram_chat_id
            )
            logger.info("Telegram notifier initialized")
        else:
            logger.warning("Telegram not configured - missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")

        # Email
        smtp_host = os.getenv('SMTP_HOST')
        smtp_user = os.getenv('SMTP_USERNAME')
        smtp_pass = os.getenv('SMTP_PASSWORD')
        email_recipient = os.getenv('EMAIL_RECIPIENT')

        if all([smtp_host, smtp_user, smtp_pass, email_recipient]):
            self.email = EmailNotifier(
                smtp_host=smtp_host,
                smtp_port=int(os.getenv('SMTP_PORT', 587)),
                username=smtp_user,
                password=smtp_pass,
                sender_email=smtp_user,
                default_recipients=[email_recipient]
            )
            logger.info("Email notifier initialized")
        else:
            logger.warning("Email not configured - missing SMTP credentials")

    def _init_scrapers(self):
        """Initialize news scrapers"""
        self.scrapers = {
            'news': NewsScraper(),
            'rss': RSSReader(),
            'competitor': CompetitorTracker(),
            'igrs': IGRSScraper()
        }
        logger.info(f"Initialized {len(self.scrapers)} scrapers")

    def _print_config_summary(self):
        """Print configuration summary"""
        summary = self.orchestrator.get_config_summary()
        logger.info("-" * 40)
        logger.info("Configuration Summary:")
        logger.info(f"  Morning Digest: {'Enabled' if summary.get('digests', {}).get('morning_enabled') else 'Disabled'}")
        logger.info(f"  Evening Digest: {'Enabled' if summary.get('digests', {}).get('evening_enabled') else 'Disabled'}")
        logger.info(f"  Active Events: {summary.get('events', {}).get('active', 0)}")
        logger.info(f"  News Sources: {sum(summary.get('sources', {}).values())}")
        logger.info("-" * 40)

    async def run_digest_cycle(self):
        """Check and run scheduled digests"""
        # Use IST timezone if available, otherwise system local time
        if IST:
            now = datetime.now(IST)
        else:
            now = datetime.now()
        today = now.date()

        # Check morning digest (7:00 AM - 7:30 AM IST window)
        if now.hour == 7 and now.minute < 30:
            if self.last_morning_digest != today:
                logger.info(f"Triggering morning digest at {now.strftime('%H:%M')} IST")
                await self._run_morning_digest()
                self.last_morning_digest = today

        # Check evening digest (4:00 PM - 4:30 PM IST window)
        if now.hour == 16 and now.minute < 30:
            if self.last_evening_digest != today:
                logger.info(f"Triggering evening digest at {now.strftime('%H:%M')} IST")
                await self._run_evening_digest()
                self.last_evening_digest = today

    async def _run_morning_digest(self):
        """Execute morning digest workflow"""
        logger.info("Starting Morning Digest...")

        try:
            # 1. Scrape news from all sources
            all_articles = await self._scrape_all_sources()
            logger.info(f"Scraped {len(all_articles)} articles")

            # 2. Process through pipeline
            processed = self.orchestrator.process_news_items(all_articles)
            logger.info(f"Processed {len(processed)} articles")

            # 3. Send notifications
            if processed:
                await self._send_digest(processed, 'morning')
            else:
                logger.info("No articles to send in morning digest")

        except Exception as e:
            logger.error(f"Morning digest failed: {e}")

    async def _run_evening_digest(self):
        """Execute evening digest workflow"""
        logger.info("Starting Evening Digest...")

        try:
            # 1. Scrape news from all sources
            all_articles = await self._scrape_all_sources()
            logger.info(f"Scraped {len(all_articles)} articles")

            # 2. Process through pipeline
            processed = self.orchestrator.process_news_items(all_articles)
            logger.info(f"Processed {len(processed)} articles")

            # 3. Send notifications
            if processed:
                await self._send_digest(processed, 'evening')
            else:
                logger.info("No articles to send in evening digest")

        except Exception as e:
            logger.error(f"Evening digest failed: {e}")

    async def _scrape_all_sources(self):
        """Scrape news from all configured sources"""
        all_articles = []

        for name, scraper in self.scrapers.items():
            try:
                articles = await scraper.fetch()
                all_articles.extend(articles)
                logger.info(f"  {name}: {len(articles)} articles")
            except Exception as e:
                logger.error(f"  {name}: Failed - {e}")

        return all_articles

    async def _send_digest(self, articles, digest_type):
        """Send digest via configured channels"""
        # Format message
        message = self._format_digest_message(articles, digest_type)

        # Send via Telegram
        if self.telegram:
            try:
                await self.telegram.send_message(message)
                logger.info(f"Sent {digest_type} digest via Telegram")
            except Exception as e:
                logger.error(f"Telegram send failed: {e}")

        # Send via Email
        if self.email:
            try:
                subject = f"Khabri {digest_type.title()} Digest - {datetime.now().strftime('%Y-%m-%d')}"
                await self.email.send_email(subject=subject, body=message)
                logger.info(f"Sent {digest_type} digest via Email")
            except Exception as e:
                logger.error(f"Email send failed: {e}")

    def _format_digest_message(self, articles, digest_type):
        """Format articles into a digest message"""
        header = f"{'Morning' if digest_type == 'morning' else 'Evening'} News Digest"
        date_str = datetime.now().strftime('%B %d, %Y')

        lines = [
            f"📰 {header}",
            f"📅 {date_str}",
            f"📊 {len(articles)} articles",
            "",
            "─" * 30,
            ""
        ]

        # Group by category
        categories = {}
        for article in articles[:20]:  # Limit to top 20
            cat = article.get('category', 'general')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(article)

        for category, cat_articles in categories.items():
            lines.append(f"📁 {category.upper()}")
            lines.append("")
            for article in cat_articles[:5]:  # Max 5 per category
                title = article.get('title', 'No title')
                source = article.get('source', 'Unknown')
                url = article.get('url', '')
                lines.append(f"• {title}")
                lines.append(f"  Source: {source}")
                if url:
                    lines.append(f"  🔗 {url}")
                lines.append("")
            lines.append("")

        lines.append("─" * 30)
        lines.append("Powered by Khabri News Intelligence")

        return "\n".join(lines)

    async def check_events(self):
        """Check for active events and send alerts"""
        result = self.orchestrator.run_event_check()

        if result.get('active_events', 0) > 0:
            event_names = result.get('event_names', [])
            logger.info(f"Active events detected: {event_names}")

            # Trigger event-based scraping
            for event_name in event_names:
                await self._run_event_scrape(event_name)

    async def _run_event_scrape(self, event_name):
        """Run scraping for a specific event"""
        logger.info(f"Running event scrape for: {event_name}")
        # Event-specific scraping logic would go here

    async def run_loop(self):
        """Main execution loop"""
        self.running = True
        check_interval = 60  # Check every 60 seconds

        logger.info(f"Starting main loop (checking every {check_interval}s)...")

        while self.running:
            try:
                # Check for scheduled digests
                await self.run_digest_cycle()

                # Check for active events
                await self.check_events()

                # Wait before next check
                await asyncio.sleep(check_interval)

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(check_interval)

    def stop(self):
        """Stop the runner"""
        logger.info("Stopping Khabri...")
        self.running = False


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    runner.stop()
    sys.exit(0)


# Global runner instance
runner = KhabriRunner()


async def main():
    """Main entry point"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize
        runner.initialize()

        # Run main loop
        await runner.run_loop()

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        runner.stop()


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🗞️  KHABRI - News Intelligence System  🗞️               ║
    ║                                                           ║
    ║   Real Estate News Aggregation & Notification Platform    ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    asyncio.run(main())
