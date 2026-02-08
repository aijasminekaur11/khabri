"""
RSS Reader

Fetches and parses RSS/Atom feeds from configured sources.
"""

import hashlib
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional
import feedparser
import requests

from src.config import ConfigManager

logger = logging.getLogger(__name__)


class RSSReader:
    """
    RSS feed parser that extracts news items from RSS/Atom feeds.
    """

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize the RSS reader.

        Args:
            config_manager: ConfigManager instance. If None, creates a new one.
        """
        self.config = config_manager or ConfigManager()
        self.last_request_time = {}

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

    def _parse_date(self, entry) -> datetime:
        """
        Parse publication date from RSS entry.

        Args:
            entry: RSS feed entry

        Returns:
            Parsed datetime or current time if parsing fails
        """
        # Try different date fields
        for date_field in ['published_parsed', 'updated_parsed', 'created_parsed']:
            if hasattr(entry, date_field):
                parsed_time = getattr(entry, date_field)
                if parsed_time:
                    try:
                        return datetime(*parsed_time[:6])
                    except (TypeError, ValueError):
                        pass

        return datetime.now()

    def _extract_content(self, entry) -> str:
        """
        Extract content from RSS entry.

        Args:
            entry: RSS feed entry

        Returns:
            Content string
        """
        # Try different content fields
        if hasattr(entry, 'content') and entry.content:
            return entry.content[0].value if isinstance(entry.content, list) else entry.content

        if hasattr(entry, 'summary') and entry.summary:
            return entry.summary

        if hasattr(entry, 'description') and entry.description:
            return entry.description

        return ''

    def read_feed(self, source: Dict) -> List[Dict]:
        """
        Read and parse a single RSS feed.

        Args:
            source: Source configuration dictionary

        Returns:
            List of NewsItem dictionaries
        """
        if not source.get('enabled', False):
            return []

        if source.get('type') != 'rss':
            return []

        source_id = source['id']
        url = source['url']
        rate_limit = source.get('rate_limit_ms', 1000)

        # Respect rate limiting
        self._respect_rate_limit(source_id, rate_limit)

        try:
            # Parse the feed
            feed = feedparser.parse(url)

            if feed.bozo:  # Feed has errors
                logger.warning(f"Feed {source_id} has parsing errors")

            news_items = []

            for entry in feed.entries:
                # Extract entry data
                title = entry.get('title', 'Untitled')
                link = entry.get('link', url)
                content = self._extract_content(entry)
                published_at = self._parse_date(entry)
                author = entry.get('author', None)

                # Build NewsItem
                news_item = {
                    'id': self._generate_id(link),
                    'title': title,
                    'url': link,
                    'source': source.get('name', 'Unknown'),
                    'source_id': source_id,
                    'category': source.get('category', 'general'),
                    'content': content,
                    'published_at': published_at,
                    'scraped_at': datetime.now(),
                    'author': author,
                    'image_url': None,
                    'tags': [tag.get('term', '') for tag in entry.get('tags', [])]
                }

                news_items.append(news_item)

            return news_items

        except Exception as e:
            logger.error(f"Error reading RSS feed {source_id} ({url}): {e}")
            return []

    def read_all(self) -> List[Dict]:
        """
        Read all enabled RSS feeds from configuration.

        Returns:
            List of all NewsItem dictionaries from all feeds
        """
        sources = self.config.get_sources()
        all_items = []

        for source in sources:
            if source.get('type') == 'rss':
                items = self.read_feed(source)
                all_items.extend(items)

        return all_items

    def read_by_category(self, category: str) -> List[Dict]:
        """
        Read RSS feeds filtered by category.

        Args:
            category: Category name to filter

        Returns:
            List of NewsItem dictionaries from the specified category
        """
        sources = self.config.get_sources()
        all_items = []

        for source in sources:
            if source.get('category') == category and source.get('type') == 'rss':
                items = self.read_feed(source)
                all_items.extend(items)

        return all_items
