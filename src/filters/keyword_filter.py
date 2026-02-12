"""
Keyword Filter
Filters and scores news articles based on configured keywords
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class KeywordFilter:
    """
    Filters news articles based on keyword matching and scoring.
    Implements both inclusion and exclusion logic based on user preferences.
    """

    def __init__(self, keywords_config: Dict[str, Any]):
        """
        Initialize KeywordFilter with configuration

        Args:
            keywords_config: Keywords configuration dictionary from keywords.yaml
        """
        self.config = keywords_config
        self.priority_keywords = keywords_config.get('priority', {})
        self.housing_schemes = keywords_config.get('housing_schemes', {})
        self.celebrity = keywords_config.get('celebrity', {})
        self.policy = keywords_config.get('policy', {})
        self.excluded = keywords_config.get('excluded', {})
        self.scoring = keywords_config.get('scoring', {})

    def _normalize_text(self, text: str) -> str:
        """Normalize text for keyword matching"""
        return text.lower().strip() if text else ""

    def _check_keywords(self, text: str, keywords: List[str]) -> Tuple[bool, List[str]]:
        """
        Check if any keywords are present in text

        Args:
            text: Text to search in
            keywords: List of keywords to search for

        Returns:
            Tuple of (found: bool, matched_keywords: List[str])
        """
        text_normalized = self._normalize_text(text)
        matched = []

        for keyword in keywords:
            keyword_normalized = self._normalize_text(keyword)
            # Use word boundary matching for better accuracy
            pattern = r'\b' + re.escape(keyword_normalized) + r'\b'
            if re.search(pattern, text_normalized):
                matched.append(keyword)

        return len(matched) > 0, matched

    def _should_exclude(self, article: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if article should be excluded based on exclusion keywords

        Args:
            article: News article dictionary

        Returns:
            Tuple of (should_exclude: bool, reason: str)
        """
        text = f"{article.get('title', '')} {article.get('content', '')}"

        # Check competitor keywords
        competitor_keywords = self.excluded.get('competitor', [])
        found, matched = self._check_keywords(text, competitor_keywords)
        if found:
            return True, f"Excluded: competitor mention ({', '.join(matched)})"

        # Check market research keywords
        research_keywords = self.excluded.get('market_research', [])
        found, matched = self._check_keywords(text, research_keywords)
        if found:
            return True, f"Excluded: market research report ({', '.join(matched)})"

        return False, ""

    def _calculate_score(self, article: Dict[str, Any], matched_categories: Dict[str, List[str]]) -> int:
        """
        Calculate relevance score based on matched keywords

        Args:
            article: News article dictionary
            matched_categories: Dictionary of category -> matched keywords

        Returns:
            Score (0-10)
        """
        score = 0
        text = f"{article.get('title', '')} {article.get('content', '')}"

        # Apply category weights
        for category, keywords in matched_categories.items():
            if category in self.scoring:
                category_score = self.scoring[category]
                if isinstance(category_score, dict):
                    # Nested scoring (e.g., priority.metro)
                    for subcategory, subkeywords in keywords.items() if isinstance(keywords, dict) else [(category, keywords)]:
                        weight = category_score.get(subcategory, 5)
                        score += weight * len(subkeywords) if isinstance(subkeywords, list) else weight
                else:
                    # Simple scoring
                    score += category_score * len(keywords)

        # Check for low priority terms and reduce score
        low_priority = self.excluded.get('low_priority', [])
        found, matched = self._check_keywords(text, low_priority)
        if found:
            penalty = self.scoring.get('excluded', {}).get('low_priority', -3)
            score += penalty

        # Normalize score to 0-10 range
        return max(0, min(10, score))

    def filter_article(self, article: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Filter a single article and calculate its relevance

        Args:
            article: News article dictionary

        Returns:
            Tuple of (should_include: bool, metadata: dict)
            metadata includes: score, matched_keywords, category, reason
        """
        text = f"{article.get('title', '')} {article.get('content', '')}"

        # First check exclusions
        should_exclude, reason = self._should_exclude(article)
        if should_exclude:
            return False, {
                'score': 0,
                'matched_keywords': [],
                'category': 'excluded',
                'reason': reason
            }

        # Check all inclusion categories
        matched_categories = {}
        all_matched_keywords = []

        # Priority keywords (metro, expressway, airport)
        for subcategory, keywords in self.priority_keywords.items():
            found, matched = self._check_keywords(text, keywords)
            if found:
                if 'priority' not in matched_categories:
                    matched_categories['priority'] = {}
                matched_categories['priority'][subcategory] = matched
                all_matched_keywords.extend(matched)

        # Housing schemes
        for subcategory, keywords in self.housing_schemes.items():
            found, matched = self._check_keywords(text, keywords)
            if found:
                if 'housing_schemes' not in matched_categories:
                    matched_categories['housing_schemes'] = {}
                matched_categories['housing_schemes'][subcategory] = matched
                all_matched_keywords.extend(matched)

        # Celebrity real estate
        celebrity_keywords = self.celebrity.get('transactions', [])
        found, matched = self._check_keywords(text, celebrity_keywords)
        if found:
            matched_categories['celebrity'] = matched
            all_matched_keywords.extend(matched)

        # Policy changes
        for subcategory, keywords in self.policy.items():
            found, matched = self._check_keywords(text, keywords)
            if found:
                if 'policy' not in matched_categories:
                    matched_categories['policy'] = {}
                matched_categories['policy'][subcategory] = matched
                all_matched_keywords.extend(matched)

        # If no keywords matched, exclude
        if not matched_categories:
            return False, {
                'score': 0,
                'matched_keywords': [],
                'category': 'no_match',
                'reason': 'No relevant keywords found'
            }

        # Calculate score
        score = self._calculate_score(article, matched_categories)

        # Determine primary category (highest scoring)
        primary_category = 'general'
        if 'priority' in matched_categories:
            if 'metro' in matched_categories['priority']:
                primary_category = 'metro'
            elif 'expressway' in matched_categories['priority']:
                primary_category = 'expressway'
            elif 'airport' in matched_categories['priority']:
                primary_category = 'airport'
        elif 'housing_schemes' in matched_categories:
            if 'pmay' in matched_categories['housing_schemes']:
                primary_category = 'pmay'
            elif 'dda' in matched_categories['housing_schemes']:
                primary_category = 'dda'
            else:
                primary_category = 'housing_scheme'
        elif 'celebrity' in matched_categories:
            primary_category = 'celebrity_realestate'
        elif 'policy' in matched_categories:
            primary_category = 'policy_change'

        return True, {
            'score': score,
            'matched_keywords': all_matched_keywords,
            'matched_categories': matched_categories,
            'category': primary_category,
            'reason': f"Matched {len(all_matched_keywords)} relevant keywords"
        }

    def filter_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter multiple articles

        Args:
            articles: List of news article dictionaries

        Returns:
            List of filtered articles with metadata
        """
        filtered = []

        for article in articles:
            should_include, metadata = self.filter_article(article)

            if should_include:
                # Add metadata to article
                article['filter_metadata'] = metadata
                article['relevance_score'] = metadata['score']
                article['matched_keywords'] = metadata['matched_keywords']
                article['primary_category'] = metadata['category']
                filtered.append(article)
            else:
                logger.debug(f"Filtered out: {article.get('title', 'Unknown')} - {metadata.get('reason', 'Unknown')}")

        # Sort by score (descending)
        filtered.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        logger.info(f"Filtered {len(filtered)} articles from {len(articles)} total")
        return filtered
