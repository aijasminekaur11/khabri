"""
Categorizer
Categorizes news items based on keywords and assigns priority scores
"""

from typing import List, Dict, Any, Set
import re


class Categorizer:
    """
    Categorizes news items into predefined categories
    Assigns priority scores based on keyword matches
    """

    def __init__(self, keywords_config: Dict[str, Any]):
        """
        Initialize Categorizer

        Args:
            keywords_config: Keywords configuration from keywords.json
        """
        self.keywords_config = keywords_config
        self._build_category_index()

    def _build_category_index(self):
        """Build efficient category keyword index"""
        self.category_keywords = {}

        for category, keywords_data in self.keywords_config.items():
            all_keywords = []

            # Handle different keyword structures
            if isinstance(keywords_data, dict):
                # Nested structure like real_estate, infrastructure
                for subcategory, keywords in keywords_data.items():
                    if isinstance(keywords, list):
                        all_keywords.extend([kw.lower() for kw in keywords])
                    elif isinstance(keywords, dict):
                        # Handle nested dicts (like projects in infrastructure)
                        for subcat_keywords in keywords.values():
                            if isinstance(subcat_keywords, list):
                                all_keywords.extend([kw.lower() for kw in subcat_keywords])
            elif isinstance(keywords_data, list):
                # Flat list structure
                all_keywords.extend([kw.lower() for kw in keywords_data])

            self.category_keywords[category] = set(all_keywords)

    def _calculate_match_score(self, text: str, keywords: Set[str]) -> float:
        """
        Calculate match score for text against keywords

        Args:
            text: Text to analyze
            keywords: Set of keywords to match

        Returns:
            Match score (0-1)
        """
        text_lower = text.lower()
        matches = 0
        total_keywords = len(keywords)

        if total_keywords == 0:
            return 0.0

        for keyword in keywords:
            # Use word boundaries for better matching
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                matches += 1

        return matches / total_keywords

    def categorize(self, news_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Categorize a single news item

        Args:
            news_item: News item with 'title' and 'content' keys

        Returns:
            Dictionary with category, score, and matched keywords
        """
        title = news_item.get('title', '')
        content = news_item.get('content', '')
        combined_text = f"{title} {content}"

        category_scores = {}
        category_matches = {}

        # Calculate scores for each category
        for category, keywords in self.category_keywords.items():
            score = self._calculate_match_score(combined_text, keywords)
            category_scores[category] = score

            # Track which keywords matched
            matched = []
            text_lower = combined_text.lower()
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower):
                    matched.append(keyword)

            category_matches[category] = matched

        # Find best matching category
        if not category_scores:
            return {
                'category': 'uncategorized',
                'score': 0.0,
                'matched_keywords': [],
                'all_scores': {}
            }

        best_category = max(category_scores.items(), key=lambda x: x[1])
        category_name, score = best_category

        # Require minimum score to assign category
        if score < 0.01:  # At least 1% match
            category_name = 'uncategorized'

        return {
            'category': category_name,
            'score': score,
            'matched_keywords': category_matches.get(category_name, []),
            'all_scores': category_scores
        }

    def assign_priority(self, news_item: Dict[str, Any]) -> str:
        """
        Assign priority level to news item

        Args:
            news_item: News item with category data

        Returns:
            Priority level: 'high', 'medium', or 'low'
        """
        category = news_item.get('category', 'uncategorized')
        score = news_item.get('score', 0.0)
        is_celebrity = news_item.get('is_celebrity_news', False)
        is_high_value = news_item.get('celebrity_match', {}).get('is_high_value', False)

        # High priority conditions
        if is_high_value:  # Celebrity deal ₹5Cr+
            return 'high'

        if category in ['policy', 'real_estate'] and score > 0.1:
            return 'high'

        if is_celebrity:
            return 'high'

        # Medium priority
        if category in ['infrastructure', 'cities'] and score > 0.05:
            return 'medium'

        if score > 0.05:
            return 'medium'

        # Low priority
        return 'low'

    def process_items(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple news items and add categorization

        Args:
            news_items: List of news items

        Returns:
            List of news items with category and priority fields
        """
        processed_items = []

        for item in news_items:
            # Categorize
            cat_data = self.categorize(item)
            item.update(cat_data)

            # Assign priority
            item['priority'] = self.assign_priority(item)

            processed_items.append(item)

        return processed_items

    def filter_by_category(
        self,
        news_items: List[Dict[str, Any]],
        categories: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Filter news items by categories

        Args:
            news_items: List of news items
            categories: List of category names to include

        Returns:
            Filtered list of news items
        """
        return [
            item for item in news_items
            if item.get('category') in categories
        ]

    def filter_by_priority(
        self,
        news_items: List[Dict[str, Any]],
        min_priority: str = 'low'
    ) -> List[Dict[str, Any]]:
        """
        Filter news items by minimum priority

        Args:
            news_items: List of news items
            min_priority: Minimum priority ('high', 'medium', 'low')

        Returns:
            Filtered list of news items
        """
        priority_order = {'high': 2, 'medium': 1, 'low': 0}
        min_level = priority_order.get(min_priority, 0)

        return [
            item for item in news_items
            if priority_order.get(item.get('priority', 'low'), 0) >= min_level
        ]
