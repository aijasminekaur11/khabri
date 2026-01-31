"""
Summarizer
Generates brief summaries and extracts key points from news content
"""

from typing import List, Dict, Any
import re


class Summarizer:
    """
    Generates summaries and extracts key information from news items
    """

    def __init__(self, max_summary_length: int = 200):
        """
        Initialize Summarizer

        Args:
            max_summary_length: Maximum length of generated summaries in characters
        """
        self.max_summary_length = max_summary_length

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Clean and normalize text

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?₹%-]', '', text)
        return text.strip()

    def _extract_first_sentences(self, text: str, max_sentences: int = 2) -> str:
        """
        Extract first N sentences from text

        Args:
            text: Text to extract from
            max_sentences: Maximum number of sentences

        Returns:
            Extracted sentences
        """
        # Split by sentence delimiters
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Take first N sentences
        selected = sentences[:max_sentences]
        summary = '. '.join(selected)

        # Ensure it ends with period
        if summary and not summary.endswith('.'):
            summary += '.'

        return summary

    def generate_summary(self, news_item: Dict[str, Any]) -> str:
        """
        Generate a brief summary of the news item

        Args:
            news_item: News item with 'title' and 'content'

        Returns:
            Generated summary
        """
        content = news_item.get('content', '')
        title = news_item.get('title', '')

        if not content and not title:
            return ""

        # If no content, use title
        if not content:
            return self._clean_text(title)

        # Clean content
        content = self._clean_text(content)

        # Extract first sentences
        summary = self._extract_first_sentences(content, max_sentences=2)

        # Truncate if too long
        if len(summary) > self.max_summary_length:
            summary = summary[:self.max_summary_length].rsplit(' ', 1)[0] + '...'

        return summary

    @staticmethod
    def extract_key_points(news_item: Dict[str, Any]) -> List[str]:
        """
        Extract key points from news item

        Args:
            news_item: News item

        Returns:
            List of key points
        """
        key_points = []

        # Category and priority
        category = news_item.get('category', 'uncategorized')
        priority = news_item.get('priority', 'low')
        if category != 'uncategorized':
            key_points.append(f"Category: {category.replace('_', ' ').title()}")

        # Celebrity info
        if news_item.get('is_celebrity_news'):
            celeb_match = news_item.get('celebrity_match', {})
            celeb_name = celeb_match.get('celebrity_name', '')
            if celeb_name:
                key_points.append(f"Celebrity: {celeb_name}")

            property_value = celeb_match.get('property_value_cr')
            if property_value:
                key_points.append(f"Value: ₹{property_value} Cr")

        # Matched keywords
        matched_keywords = news_item.get('matched_keywords', [])
        if matched_keywords:
            # Show top 3 keywords
            keywords_str = ', '.join(matched_keywords[:3])
            key_points.append(f"Keywords: {keywords_str}")

        return key_points

    def generate_headline(self, news_item: Dict[str, Any]) -> str:
        """
        Generate an optimized headline

        Args:
            news_item: News item

        Returns:
            Generated headline
        """
        title = news_item.get('title', '')

        # If title already exists and is good, use it
        if title:
            # Clean and truncate if needed
            title = self._clean_text(title)
            if len(title) <= 100:
                return title

            # Truncate long titles
            return title[:97] + '...'

        # Generate from content
        content = news_item.get('content', '')
        if content:
            summary = self._extract_first_sentences(content, max_sentences=1)
            return summary[:100]

        return "Untitled News Item"

    def process_items(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple news items and add summaries

        Args:
            news_items: List of news items

        Returns:
            List of news items with summary fields
        """
        processed_items = []

        for item in news_items:
            # Generate summary
            item['summary'] = self.generate_summary(item)

            # Extract key points
            item['key_points'] = self.extract_key_points(item)

            # Generate headline
            item['headline'] = self.generate_headline(item)

            processed_items.append(item)

        return processed_items
