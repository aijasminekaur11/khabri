"""
Deduplicator
Removes duplicate news items based on URL, title similarity, and time window
"""

import hashlib
from typing import List, Dict, Any, Set
from datetime import datetime, timedelta
from difflib import SequenceMatcher


class Deduplicator:
    """
    Removes duplicate news items using multiple strategies:
    - URL hash checking
    - Title similarity
    - 24-hour time window
    """

    def __init__(self, similarity_threshold: float = 0.85, time_window_hours: int = 24):
        """
        Initialize Deduplicator

        Args:
            similarity_threshold: Minimum similarity ratio (0-1) to consider duplicates
            time_window_hours: Time window in hours to check for duplicates
        """
        self.similarity_threshold = similarity_threshold
        self.time_window_hours = time_window_hours
        self.seen_urls: Set[str] = set()
        self.seen_hashes: Set[str] = set()
        self.recent_titles: List[tuple] = []  # (title, timestamp)

    @staticmethod
    def _compute_hash(text: str) -> str:
        """
        Compute SHA256 hash of text

        Args:
            text: Text to hash

        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    @staticmethod
    def _title_similarity(title1: str, title2: str) -> float:
        """
        Calculate similarity between two titles

        Args:
            title1: First title
            title2: Second title

        Returns:
            Similarity ratio between 0 and 1
        """
        # Normalize titles
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()

        return SequenceMatcher(None, t1, t2).ratio()

    def _is_duplicate_by_title(self, title: str, timestamp: datetime) -> bool:
        """
        Check if title is duplicate based on similarity and time window

        Args:
            title: News item title
            timestamp: News item timestamp

        Returns:
            True if duplicate, False otherwise
        """
        # Remove old titles outside time window
        cutoff_time = timestamp - timedelta(hours=self.time_window_hours)
        self.recent_titles = [
            (t, ts) for t, ts in self.recent_titles
            if ts >= cutoff_time
        ]

        # Check similarity with recent titles
        for recent_title, _ in self.recent_titles:
            similarity = self._title_similarity(title, recent_title)
            if similarity >= self.similarity_threshold:
                return True

        return False

    def is_duplicate(self, news_item: Dict[str, Any]) -> bool:
        """
        Check if a news item is a duplicate

        Args:
            news_item: News item dictionary with keys: url, title, timestamp

        Returns:
            True if duplicate, False otherwise
        """
        url = news_item.get('url', '')
        title = news_item.get('title', '')
        timestamp = news_item.get('timestamp')

        if not timestamp:
            timestamp = datetime.now()
        elif isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()

        # Check URL hash
        if url:
            url_hash = self._compute_hash(url)
            if url_hash in self.seen_hashes:
                return True

        # Check title similarity
        if title and self._is_duplicate_by_title(title, timestamp):
            return True

        return False

    def mark_as_seen(self, news_item: Dict[str, Any]):
        """
        Mark a news item as seen

        Args:
            news_item: News item to mark as seen
        """
        url = news_item.get('url', '')
        title = news_item.get('title', '')
        timestamp = news_item.get('timestamp')

        if not timestamp:
            timestamp = datetime.now()
        elif isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()

        # Mark URL as seen
        if url:
            url_hash = self._compute_hash(url)
            self.seen_hashes.add(url_hash)
            self.seen_urls.add(url)

        # Add title to recent titles
        if title:
            self.recent_titles.append((title, timestamp))

    def deduplicate(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicates from a list of news items

        Args:
            news_items: List of news item dictionaries

        Returns:
            List of unique news items
        """
        unique_items = []

        for item in news_items:
            if not self.is_duplicate(item):
                self.mark_as_seen(item)
                unique_items.append(item)

        return unique_items

    def clear(self):
        """Clear all deduplication caches"""
        self.seen_urls.clear()
        self.seen_hashes.clear()
        self.recent_titles.clear()

    def get_stats(self) -> Dict[str, int]:
        """
        Get deduplication statistics

        Returns:
            Dictionary with stats
        """
        return {
            'seen_urls': len(self.seen_urls),
            'seen_hashes': len(self.seen_hashes),
            'recent_titles': len(self.recent_titles)
        }
