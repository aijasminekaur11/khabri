"""
News Scraper

General web scraping module for extracting news articles from configured sources.
Uses BeautifulSoup for HTML parsing and respects rate limiting.
"""

import hashlib
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

from src.config import ConfigManager

logger = logging.getLogger(__name__)


class NewsScraper:
    """
    General-purpose news scraper that fetches articles from web sources
    based on CSS selectors defined in configuration.
    """

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize the news scraper.

        Args:
            config_manager: ConfigManager instance. If None, creates a new one.
        """
        self.config = config_manager or ConfigManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MagicBricks-NewsBot/1.0 (News Intelligence System)'
        })
        self.last_request_time = {}

    def close(self):
        """Close the requests session to free resources."""
        if self.session:
            self.session.close()
            logger.debug("NewsScraper session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures session is closed."""
        self.close()
        return False

    def _generate_id(self, url: str) -> str:
        """Generate unique ID from URL using hash."""
        return hashlib.md5(url.encode()).hexdigest()

    def _respect_rate_limit(self, source_id: str, rate_limit_ms: int):
        """
        Enforce rate limiting for a specific source.

        Args:
            source_id: The source identifier
            rate_limit_ms: Minimum milliseconds between requests
        """
        if source_id in self.last_request_time:
            elapsed = (time.time() - self.last_request_time[source_id]) * 1000
            if elapsed < rate_limit_ms:
                sleep_time = (rate_limit_ms - elapsed) / 1000
                time.sleep(sleep_time)

        self.last_request_time[source_id] = time.time()

    def _parse_article(self, html: str, selectors: Dict[str, str]) -> Dict[str, Optional[str]]:
        """
        Parse article content using CSS selectors.

        Args:
            html: Raw HTML content
            selectors: Dictionary of CSS selectors for title, content, date, link

        Returns:
            Dictionary with extracted fields
        """
        soup = BeautifulSoup(html, 'html.parser')

        result = {
            'title': None,
            'content': None,
            'date': None,
            'link': None
        }

        for field, selector in selectors.items():
            if selector:
                element = soup.select_one(selector)
                if element:
                    result[field] = element.get_text(strip=True)

        return result

    def scrape_source(self, source: Dict) -> List[Dict]:
        """
        Scrape a single news source.

        Args:
            source: Source configuration dictionary

        Returns:
            List of NewsItem dictionaries
        """
        if not source.get('enabled', False):
            return []

        if source.get('type') != 'scrape':
            return []

        source_id = source['id']
        url = source['url']
        rate_limit = source.get('rate_limit_ms', 1000)
        selectors = source.get('selectors', {})

        # Respect rate limiting
        self._respect_rate_limit(source_id, rate_limit)

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # Parse the article
            parsed = self._parse_article(response.text, selectors)

            if not parsed['title']:
                return []

            # Build NewsItem
            news_item = {
                'id': self._generate_id(url),
                'title': parsed['title'] or 'Untitled',
                'url': url,
                'source': source.get('name', 'Unknown'),
                'source_id': source_id,
                'category': source.get('category', 'general'),
                'content': parsed['content'] or '',
                'published_at': datetime.now(),  # TODO: Parse from parsed['date']
                'scraped_at': datetime.now(),
                'author': None,
                'image_url': None,
                'tags': []
            }

            return [news_item]

        except requests.RequestException as e:
            logger.error(f"Error scraping {source_id} ({url}): {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error scraping {source_id}: {e}")
            return []

    def scrape_all(self) -> List[Dict]:
        """
        Scrape all enabled sources from configuration.

        Returns:
            List of all NewsItem dictionaries from all sources
        """
        sources = self.config.get_sources()
        all_items = []

        for source in sources:
            if source.get('type') == 'scrape':
                items = self.scrape_source(source)
                all_items.extend(items)

        return all_items

    def scrape_by_category(self, category: str) -> List[Dict]:
        """
        Scrape sources filtered by category.

        Args:
            category: Category name to filter

        Returns:
            List of NewsItem dictionaries from the specified category
        """
        sources = self.config.get_sources()
        all_items = []

        for source in sources:
            if source.get('category') == category and source.get('type') == 'scrape':
                items = self.scrape_source(source)
                all_items.extend(items)

        return all_items
