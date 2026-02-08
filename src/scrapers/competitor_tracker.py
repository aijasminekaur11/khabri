"""
Competitor Tracker

Monitors competitor websites to identify content gaps and opportunities.
Generates CompetitorAlert objects when competitors publish content.
"""

import hashlib
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

from src.config import ConfigManager

logger = logging.getLogger(__name__)


class CompetitorTracker:
    """
    Tracks competitor content to identify publishing gaps and opportunities.
    """

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize the competitor tracker.

        Args:
            config_manager: ConfigManager instance. If None, creates a new one.
        """
        self.config = config_manager or ConfigManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MagicBricks-CompetitorBot/1.0 (Content Gap Analysis)'
        })
        self.last_request_time = {}
        self.tracked_articles = {}  # Store previously seen articles

    def close(self):
        """Close the requests session to free resources."""
        if self.session:
            self.session.close()
            logger.debug("CompetitorTracker session closed")

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

    def _extract_articles(self, html: str, selectors: Dict[str, str]) -> List[Dict]:
        """
        Extract multiple articles from competitor homepage.

        Args:
            html: Raw HTML content
            selectors: CSS selectors for articles

        Returns:
            List of extracted article data
        """
        soup = BeautifulSoup(html, 'html.parser')
        articles = []

        # Find all article containers
        article_elements = soup.select(selectors.get('container', 'article'))

        for element in article_elements[:10]:  # Limit to 10 most recent
            title_el = element.select_one(selectors.get('title', 'h2'))
            link_el = element.select_one(selectors.get('link', 'a'))
            date_el = element.select_one(selectors.get('date', 'time'))

            if title_el and link_el:
                article = {
                    'title': title_el.get_text(strip=True),
                    'link': link_el.get('href', ''),
                    'date': date_el.get_text(strip=True) if date_el else None
                }
                articles.append(article)

        return articles

    def _analyze_content_gap(self, competitor_article: Dict, our_content: List[Dict]) -> List[str]:
        """
        Analyze what content gaps exist between competitor and our coverage.

        Args:
            competitor_article: Competitor's article data
            our_content: List of our recent articles

        Returns:
            List of identified gaps
        """
        gaps = []

        competitor_title = competitor_article['title'].lower()

        # Check if we covered similar topic
        covered = False
        for our_article in our_content:
            our_title = our_article.get('title', '').lower()
            # Simple keyword matching
            common_words = set(competitor_title.split()) & set(our_title.split())
            if len(common_words) >= 3:
                covered = True
                break

        if not covered:
            gaps.append(f"Not covered: {competitor_article['title']}")

        return gaps

    def _calculate_opportunity_window(self, published_at: datetime) -> int:
        """
        Calculate how many minutes we have to respond.

        Args:
            published_at: When competitor published

        Returns:
            Minutes remaining to beat competitor
        """
        now = datetime.now()
        elapsed = (now - published_at).total_seconds() / 60
        window = max(0, 180 - int(elapsed))  # 3-hour window
        return window

    def track_competitor(self, source: Dict, our_recent_content: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Track a single competitor source.

        Args:
            source: Source configuration for competitor
            our_recent_content: Our recent articles for gap analysis

        Returns:
            List of CompetitorAlert dictionaries
        """
        if not source.get('enabled', False):
            return []

        if source.get('category') != 'competitor':
            return []

        source_id = source['id']
        url = source['url']
        rate_limit = source.get('rate_limit_ms', 2000)  # Be more polite to competitors
        selectors = source.get('selectors', {})

        # Respect rate limiting
        self._respect_rate_limit(source_id, rate_limit)

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # Extract articles
            articles = self._extract_articles(response.text, selectors)

            alerts = []

            for article in articles:
                article_id = self._generate_id(article['link'])

                # Check if this is new
                if article_id not in self.tracked_articles:
                    self.tracked_articles[article_id] = datetime.now()

                    # Analyze content gap
                    gaps = self._analyze_content_gap(
                        article,
                        our_recent_content or []
                    )

                    if gaps:
                        # Create CompetitorAlert
                        alert = {
                            'competitor': source.get('name', 'Unknown'),
                            'article_url': article['link'],
                            'article_title': article['title'],
                            'published_at': datetime.now(),  # TODO: Parse from article['date']
                            'gaps': gaps,
                            'opportunity_window': self._calculate_opportunity_window(datetime.now())
                        }
                        alerts.append(alert)

            return alerts

        except requests.RequestException as e:
            logger.error(f"Error tracking competitor {source_id} ({url}): {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error tracking competitor {source_id}: {e}")
            return []

    def track_all_competitors(self, our_recent_content: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Track all configured competitors.

        Args:
            our_recent_content: Our recent articles for gap analysis

        Returns:
            List of all CompetitorAlert dictionaries
        """
        sources = self.config.get_sources()
        all_alerts = []

        for source in sources:
            if source.get('category') == 'competitor':
                alerts = self.track_competitor(source, our_recent_content)
                all_alerts.extend(alerts)

        return all_alerts

    def get_high_priority_alerts(self, our_recent_content: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Get only high-priority competitor alerts (narrow opportunity window).

        Args:
            our_recent_content: Our recent articles for gap analysis

        Returns:
            List of high-priority CompetitorAlert dictionaries
        """
        all_alerts = self.track_all_competitors(our_recent_content)

        # Filter for alerts with opportunity window > 120 minutes
        high_priority = [
            alert for alert in all_alerts
            if alert['opportunity_window'] >= 120
        ]

        return high_priority
