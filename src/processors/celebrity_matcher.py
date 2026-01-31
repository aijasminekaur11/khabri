"""
Celebrity Matcher
Matches news items with celebrity names and extracts property deal information
"""

import re
from typing import List, Dict, Any, Optional, Set


class CelebrityMatcher:
    """
    Matches celebrity names (including aliases) in news content
    Detects high-value property deals (₹5Cr+)
    """

    def __init__(self, celebrities_config: Dict[str, List[Dict[str, Any]]]):
        """
        Initialize CelebrityMatcher

        Args:
            celebrities_config: Celebrity configuration from celebrities.json
        """
        self.celebrities_config = celebrities_config
        self._build_lookup_index()

    def _build_lookup_index(self):
        """Build efficient lookup index for celebrity name matching"""
        self.name_to_celebrity = {}
        self.all_search_terms: Set[str] = set()

        for category, celebrities in self.celebrities_config.items():
            for celeb in celebrities:
                primary_name = celeb.get('name', '')
                aliases = celeb.get('aliases', [])
                family = celeb.get('family', [])
                priority = celeb.get('priority', 'medium')

                # Store celebrity data with all possible name variants
                celeb_data = {
                    'name': primary_name,
                    'category': category,
                    'priority': priority,
                    'aliases': aliases,
                    'family': family
                }

                # Index primary name
                if primary_name:
                    self.name_to_celebrity[primary_name.lower()] = celeb_data
                    self.all_search_terms.add(primary_name.lower())

                # Index aliases
                for alias in aliases:
                    self.name_to_celebrity[alias.lower()] = celeb_data
                    self.all_search_terms.add(alias.lower())

                # Index family members (link to main celebrity)
                for family_member in family:
                    self.name_to_celebrity[family_member.lower()] = celeb_data
                    self.all_search_terms.add(family_member.lower())

    @staticmethod
    def _extract_property_value(text: str) -> Optional[float]:
        """
        Extract property value from text

        Args:
            text: Text containing property value

        Returns:
            Value in crores, or None if not found
        """
        # Patterns for Indian currency (₹X Cr, ₹X Crore, Rs X Cr, etc.)
        patterns = [
            r'₹\s*(\d+(?:\.\d+)?)\s*(?:cr|crore|crores)',
            r'rs\.?\s*(\d+(?:\.\d+)?)\s*(?:cr|crore|crores)',
            r'inr\s*(\d+(?:\.\d+)?)\s*(?:cr|crore|crores)',
            r'(\d+(?:\.\d+)?)\s*(?:cr|crore|crores)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None

    def match_celebrities(self, news_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Match celebrities in a news item

        Args:
            news_item: News item with 'title' and 'content' keys

        Returns:
            Celebrity match data if found, None otherwise
        """
        title = news_item.get('title', '').lower()
        content = news_item.get('content', '').lower()
        combined_text = f"{title} {content}"

        matches = []

        # Search for each celebrity name/alias
        for search_term in self.all_search_terms:
            if search_term in combined_text:
                celeb_data = self.name_to_celebrity[search_term]
                matches.append({
                    'matched_term': search_term,
                    'celebrity': celeb_data
                })

        if not matches:
            return None

        # Return highest priority match
        matches.sort(key=lambda x: (
            0 if x['celebrity']['priority'] == 'high' else
            1 if x['celebrity']['priority'] == 'medium' else 2
        ))

        primary_match = matches[0]['celebrity']

        # Extract property value
        property_value = self._extract_property_value(combined_text)

        return {
            'celebrity_name': primary_match['name'],
            'celebrity_category': primary_match['category'],
            'priority': primary_match['priority'],
            'matched_term': matches[0]['matched_term'],
            'property_value_cr': property_value,
            'is_high_value': property_value >= 5.0 if property_value else False,
            'all_matches': [m['celebrity']['name'] for m in matches]
        }

    def is_celebrity_news(self, news_item: Dict[str, Any], high_value_only: bool = False) -> bool:
        """
        Check if news item is celebrity-related

        Args:
            news_item: News item to check
            high_value_only: If True, only return True for high-value deals (₹5Cr+)

        Returns:
            True if celebrity news, False otherwise
        """
        match = self.match_celebrities(news_item)

        if not match:
            return False

        if high_value_only:
            return match.get('is_high_value', False)

        return True

    def process_items(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple news items and add celebrity match data

        Args:
            news_items: List of news items

        Returns:
            List of news items with celebrity_match field added
        """
        processed_items = []

        for item in news_items:
            match = self.match_celebrities(item)
            if match:
                item['celebrity_match'] = match
                item['is_celebrity_news'] = True
            else:
                item['is_celebrity_news'] = False

            processed_items.append(item)

        return processed_items

    def get_celebrity_news_only(
        self,
        news_items: List[Dict[str, Any]],
        high_value_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Filter news items to only celebrity-related ones

        Args:
            news_items: List of news items
            high_value_only: If True, only return high-value deals

        Returns:
            Filtered list of celebrity news
        """
        filtered = []

        for item in news_items:
            if self.is_celebrity_news(item, high_value_only):
                match = self.match_celebrities(item)
                item['celebrity_match'] = match
                filtered.append(item)

        return filtered
