#!/usr/bin/env python3
"""
Test Script: Fetch Latest BTS News with Links

This script demonstrates fetching news related to 'BTS' keyword,
processing results, and displaying them with links.

Usage:
    python tests/test_bts_news_fetch.py
"""

import sys
import os
import logging
from datetime import datetime
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config.config_manager import ConfigManager
from src.scrapers.news_scraper import NewsScraper
from src.notifiers.telegram_notifier import TelegramNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BTSNewsFetcher:
    """
    Specialized fetcher for BTS-related news with link extraction.
    """

    def __init__(self):
        """Initialize the BTS news fetcher."""
        self.config = ConfigManager()
        self.scraper = NewsScraper(self.config)
        self.telegram = TelegramNotifier()
        self.keyword = "BTS"

    def fetch_news(self) -> List[Dict[str, Any]]:
        """
        Fetch latest news articles related to BTS.

        Returns:
            List of news items with BTS keyword matches
        """
        logger.info(f"Fetching news for keyword: {self.keyword}")

        # Scrape all available sources
        all_news = self.scraper.scrape_all()

        # Filter for BTS-related content
        bts_news = []
        for item in all_news:
            title = item.get('title', '').lower()
            content = item.get('content', '').lower()

            # Check if BTS appears in title or content
            if self.keyword.lower() in title or self.keyword.lower() in content:
                bts_news.append(item)

        logger.info(f"Found {len(bts_news)} BTS-related news items")
        return bts_news

    def format_news_output(self, news_items: List[Dict[str, Any]]) -> str:
        """
        Format news items for display with links.

        Args:
            news_items: List of news item dictionaries

        Returns:
            Formatted string output
        """
        if not news_items:
            return "❌ No BTS news found at this time.\n"

        output = f"\n{'='*70}\n"
        output += f"🎵 LATEST BTS NEWS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        output += f"{'='*70}\n\n"
        output += f"Found {len(news_items)} article(s)\n\n"

        for idx, item in enumerate(news_items, 1):
            output += f"[{idx}] {item.get('title', 'No Title')}\n"
            output += f"    📰 Source: {item.get('source', 'Unknown')}\n"
            output += f"    📂 Category: {item.get('category', 'general')}\n"
            output += f"    🔗 Link: {item.get('url', 'No URL')}\n"

            # Add content preview if available
            content = item.get('content', '')
            if content:
                preview = content[:150] + '...' if len(content) > 150 else content
                output += f"    📝 Preview: {preview}\n"

            published = item.get('published_at')
            if published:
                if isinstance(published, str):
                    output += f"    ⏰ Published: {published}\n"
                else:
                    output += f"    ⏰ Published: {published.strftime('%Y-%m-%d %H:%M')}\n"

            output += "\n" + "-"*70 + "\n\n"

        return output

    def send_to_telegram(self, news_items: List[Dict[str, Any]]) -> bool:
        """
        Send BTS news to Telegram.

        Args:
            news_items: List of news items

        Returns:
            True if sent successfully
        """
        if not news_items:
            message = "ℹ️ No BTS news found at this time."
            return self.telegram._send_message(message)

        message = f"🎵 *LATEST BTS NEWS* ({len(news_items)} articles)\n\n"

        for idx, item in enumerate(news_items[:10], 1):  # Limit to 10 items
            title = item.get('title', 'No Title')
            url = item.get('url', '')
            source = item.get('source', 'Unknown')

            # Escape Markdown special characters
            for ch in ('\\', '*', '_', '`', '[', ']'):
                title = title.replace(ch, f'\\{ch}')
                source = source.replace(ch, f'\\{ch}')

            message += f"{idx}\\. *{title}*\n"
            message += f"   📰 Source: {source}\n"

            if url:
                safe_url = url.replace('(', '%28').replace(')', '%29')
                message += f"   🔗 [Read Article]({safe_url})\n"

            message += "\n"

        message += f"\n_Last updated: {datetime.now().strftime('%Y\\-%m\\-%d %H:%M')}_"

        try:
            return self.telegram._send_message(message)
        except Exception as e:
            logger.error(f"Failed to send to Telegram: {e}")
            return False

    def run(self, send_telegram: bool = True) -> None:
        """
        Execute the complete BTS news fetch workflow.

        Args:
            send_telegram: Whether to send results to Telegram
        """
        logger.info("Starting BTS news fetch test...")

        try:
            # Fetch news
            news_items = self.fetch_news()

            # Print to console
            output = self.format_news_output(news_items)
            print(output)

            # Send to Telegram if enabled
            if send_telegram:
                logger.info("Sending results to Telegram...")
                success = self.send_to_telegram(news_items)
                if success:
                    logger.info("✅ Successfully sent to Telegram")
                else:
                    logger.warning("⚠️ Failed to send to Telegram")

            logger.info("BTS news fetch test completed successfully")

        except Exception as e:
            logger.error(f"Error during BTS news fetch: {e}", exc_info=True)
            raise

        finally:
            # Clean up resources
            self.scraper.close()


def main():
    """
    Main entry point for the test script.
    """
    print("\n" + "="*70)
    print("  BTS NEWS FETCHER - TEST SCRIPT")
    print("  Fetches latest news about BTS with links")
    print("="*70 + "\n")

    # Parse command line arguments
    send_telegram = '--telegram' in sys.argv or '-t' in sys.argv
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and run fetcher
    fetcher = BTSNewsFetcher()

    try:
        fetcher.run(send_telegram=send_telegram)
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)

    print("\n✅ Test completed successfully\n")


if __name__ == '__main__':
    main()
