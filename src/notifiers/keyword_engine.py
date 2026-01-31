"""
Keyword Engine
SEO keyword research and Google Discover potential calculation
"""

import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re


logger = logging.getLogger(__name__)


class KeywordEngine:
    """
    SEO keyword research engine using Google Trends data.

    NOT a notifier - provides data TO notifiers.

    Requirements:
    - Use pytrends for Google Trends (gracefully degrade if unavailable)
    - Cache results (15 min TTL)
    - Handle rate limiting
    """

    CACHE_TTL = 900  # 15 minutes in seconds
    RATE_LIMIT_DELAY = 2.0  # seconds between API calls

    def __init__(self):
        """Initialize KeywordEngine with caching"""
        self.cache = {}
        self.last_request_time = 0

        # Try to import pytrends
        self.pytrends_available = False
        try:
            from pytrends.request import TrendReq
            self.pytrends = TrendReq(hl='en-IN', tz=330)  # India timezone
            self.pytrends_available = True
            logger.info("KeywordEngine initialized with pytrends support")
        except ImportError:
            logger.warning("pytrends not available. Using fallback keyword extraction.")
            self.pytrends = None

    def _rate_limit(self):
        """Enforce rate limiting for API calls"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    def _get_cache(self, key: str) -> Optional[Any]:
        """
        Get cached value if not expired

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if key in self.cache:
            cached_data, timestamp = self.cache[key]
            if time.time() - timestamp < self.CACHE_TTL:
                return cached_data
            else:
                # Expired, remove from cache
                del self.cache[key]
        return None

    def _set_cache(self, key: str, value: Any):
        """
        Store value in cache

        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = (value, time.time())

    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """
        Extract potential keywords from text using heuristics

        Args:
            text: Text to extract keywords from

        Returns:
            List of keywords
        """
        # Remove special characters and normalize
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)

        # Split into words
        words = text.split()

        # Filter for meaningful words (length > 3, not common words)
        common_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him',
            'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two',
            'who', 'boy', 'did', 'she', 'let', 'put', 'say', 'too', 'use',
            'this', 'that', 'with', 'have', 'from', 'they', 'will', 'what',
            'been', 'more', 'when', 'your', 'said', 'each', 'than', 'them'
        }

        keywords = [
            word for word in words
            if len(word) > 3 and word not in common_words
        ]

        # Extract bigrams (two-word phrases)
        bigrams = [
            f"{words[i]} {words[i+1]}"
            for i in range(len(words) - 1)
            if len(words[i]) > 3 and len(words[i+1]) > 3
            and words[i] not in common_words
            and words[i+1] not in common_words
        ]

        # Combine and deduplicate
        all_keywords = list(set(keywords + bigrams))

        return all_keywords[:20]  # Return top 20

    def get_trending_keywords(self, topic: str) -> List[Dict[str, Any]]:
        """
        Get trending keywords related to a topic

        Args:
            topic: Topic to search for

        Returns:
            List of KeywordData dictionaries
        """
        cache_key = f"trending_{topic}"
        cached = self._get_cache(cache_key)
        if cached:
            logger.info(f"Returning cached trending keywords for: {topic}")
            return cached

        keywords = []

        if self.pytrends_available and self.pytrends:
            try:
                self._rate_limit()

                # Get related queries
                self.pytrends.build_payload([topic], timeframe='now 7-d', geo='IN')
                related = self.pytrends.related_queries()

                if topic in related and related[topic]['rising'] is not None:
                    rising_df = related[topic]['rising']

                    for _, row in rising_df.head(5).iterrows():
                        keywords.append({
                            'keyword': row['query'],
                            'search_volume': int(row.get('value', 0)),
                            'difficulty': self._estimate_difficulty(row.get('value', 0)),
                            'type': 'trending'
                        })

                logger.info(f"Found {len(keywords)} trending keywords for: {topic}")

            except Exception as e:
                logger.error(f"Error fetching trending keywords: {e}")

        # Fallback: use topic variations
        if not keywords:
            keywords = [
                {
                    'keyword': f"{topic} news",
                    'search_volume': 0,
                    'difficulty': 'MEDIUM',
                    'type': 'primary'
                },
                {
                    'keyword': f"{topic} latest",
                    'search_volume': 0,
                    'difficulty': 'MEDIUM',
                    'type': 'primary'
                },
                {
                    'keyword': f"{topic} updates",
                    'search_volume': 0,
                    'difficulty': 'MEDIUM',
                    'type': 'secondary'
                }
            ]

        self._set_cache(cache_key, keywords)
        return keywords

    def get_seo_suggestions(self, news: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get SEO keyword suggestions for a news item

        Args:
            news: ProcessedNews dictionary

        Returns:
            List of KeywordData dictionaries
        """
        title = news.get('title', '')
        content = news.get('content', '')
        category = news.get('category', '')

        # Extract keywords from text
        text_keywords = self._extract_keywords_from_text(title + ' ' + content)

        suggestions = []

        # Primary keywords (from title)
        title_keywords = self._extract_keywords_from_text(title)[:3]
        for kw in title_keywords:
            suggestions.append({
                'keyword': kw,
                'search_volume': 0,  # Would need API to get real data
                'difficulty': 'MEDIUM',
                'type': 'primary'
            })

        # Secondary keywords (from content)
        content_keywords = [
            kw for kw in text_keywords
            if kw not in title_keywords
        ][:3]
        for kw in content_keywords:
            suggestions.append({
                'keyword': kw,
                'search_volume': 0,
                'difficulty': 'MEDIUM',
                'type': 'secondary'
            })

        # Long-tail keywords (category + keyword combinations)
        if category and title_keywords:
            suggestions.append({
                'keyword': f"{category} {title_keywords[0]}",
                'search_volume': 0,
                'difficulty': 'LOW',
                'type': 'long_tail'
            })

        # Celebrity-specific keywords
        if news.get('celebrity_match'):
            celebrity = news.get('celebrity_match')
            suggestions.append({
                'keyword': f"{celebrity} news",
                'search_volume': 0,
                'difficulty': 'HIGH',
                'type': 'primary'
            })
            suggestions.append({
                'keyword': f"{celebrity} {category}",
                'search_volume': 0,
                'difficulty': 'MEDIUM',
                'type': 'secondary'
            })

        logger.info(f"Generated {len(suggestions)} SEO suggestions")
        return suggestions[:10]  # Return top 10

    def calculate_discover_potential(self, news: Dict[str, Any]) -> int:
        """
        Calculate Google Discover potential score (0-100)

        Scoring based on:
        - Celebrity name in title (30 points)
        - Trending topic (25 points)
        - Visual content (20 points)
        - Fresh news (15 points)
        - High engagement keywords (10 points)

        Args:
            news: ProcessedNews dictionary

        Returns:
            Score from 0-100
        """
        score = 0

        # Celebrity presence (30 points)
        if news.get('celebrity_match'):
            score += 30
            logger.debug("Celebrity match: +30 points")

        # Freshness (15 points max)
        published_at = news.get('published_at')
        if published_at:
            try:
                if isinstance(published_at, str):
                    published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))

                age_hours = (datetime.now() - published_at.replace(tzinfo=None)).total_seconds() / 3600

                if age_hours < 2:
                    score += 15
                    logger.debug("Very fresh (< 2h): +15 points")
                elif age_hours < 6:
                    score += 10
                    logger.debug("Fresh (< 6h): +10 points")
                elif age_hours < 24:
                    score += 5
                    logger.debug("Recent (< 24h): +5 points")
            except Exception as e:
                logger.warning(f"Error calculating freshness: {e}")

        # Visual content (20 points)
        if news.get('image_url'):
            score += 20
            logger.debug("Has image: +20 points")

        # Trending topic (25 points)
        # Check if keywords match trending topics
        keywords = news.get('keywords', [])
        title = news.get('title', '').lower()

        trending_terms = [
            'breaking', 'exclusive', 'viral', 'trending', 'major',
            'shock', 'controversy', 'announced', 'launches', 'reveals'
        ]

        if any(term in title for term in trending_terms):
            score += 15
            logger.debug("Trending term in title: +15 points")

        # Check category priority
        high_priority_categories = ['celebrity', 'real_estate', 'infrastructure']
        if news.get('category') in high_priority_categories:
            score += 10
            logger.debug("High priority category: +10 points")

        # High engagement potential (10 points)
        if news.get('impact_level') == 'HIGH':
            score += 10
            logger.debug("High impact: +10 points")

        # Cap at 100
        score = min(score, 100)

        logger.info(f"Discover potential calculated: {score}/100")
        return score

    def _estimate_difficulty(self, search_volume: int) -> str:
        """
        Estimate keyword difficulty based on search volume

        Args:
            search_volume: Search volume number

        Returns:
            Difficulty level (HIGH | MEDIUM | LOW)
        """
        if search_volume > 10000:
            return 'HIGH'
        elif search_volume > 1000:
            return 'MEDIUM'
        else:
            return 'LOW'

    def get_keyword_stats(self) -> Dict[str, Any]:
        """
        Get statistics about keyword engine usage

        Returns:
            Statistics dictionary
        """
        return {
            'cache_size': len(self.cache),
            'pytrends_available': self.pytrends_available,
            'last_request': datetime.fromtimestamp(self.last_request_time).isoformat()
            if self.last_request_time > 0
            else None
        }

    def clear_cache(self):
        """Clear the keyword cache"""
        self.cache = {}
        logger.info("Keyword cache cleared")
