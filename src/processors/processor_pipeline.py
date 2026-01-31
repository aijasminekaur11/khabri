"""
Processor Pipeline
Coordinates all processing steps: deduplication, celebrity matching, categorization, summarization
"""

from typing import List, Dict, Any, Optional
from .deduplicator import Deduplicator
from .celebrity_matcher import CelebrityMatcher
from .categorizer import Categorizer
from .summarizer import Summarizer


class ProcessorPipeline:
    """
    Main processing pipeline that coordinates all processors
    """

    def __init__(
        self,
        celebrities_config: Optional[Dict[str, Any]] = None,
        keywords_config: Optional[Dict[str, Any]] = None,
        enable_deduplication: bool = True,
        enable_celebrity_matching: bool = True,
        enable_categorization: bool = True,
        enable_summarization: bool = True
    ):
        """
        Initialize ProcessorPipeline

        Args:
            celebrities_config: Celebrity configuration
            keywords_config: Keywords configuration
            enable_deduplication: Enable deduplication
            enable_celebrity_matching: Enable celebrity matching
            enable_categorization: Enable categorization
            enable_summarization: Enable summarization
        """
        # Initialize processors
        self.enable_deduplication = enable_deduplication
        self.enable_celebrity_matching = enable_celebrity_matching
        self.enable_categorization = enable_categorization
        self.enable_summarization = enable_summarization

        # Create processor instances
        if enable_deduplication:
            self.deduplicator = Deduplicator()
        else:
            self.deduplicator = None

        if enable_celebrity_matching and celebrities_config:
            self.celebrity_matcher = CelebrityMatcher(celebrities_config)
        else:
            self.celebrity_matcher = None

        if enable_categorization and keywords_config:
            self.categorizer = Categorizer(keywords_config)
        else:
            self.categorizer = None

        if enable_summarization:
            self.summarizer = Summarizer()
        else:
            self.summarizer = None

        self.stats = {
            'total_input': 0,
            'duplicates_removed': 0,
            'celebrity_news': 0,
            'categorized': 0,
            'summarized': 0,
            'total_output': 0
        }

    def process(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process news items through the complete pipeline

        Args:
            news_items: List of raw news items

        Returns:
            List of processed news items
        """
        self.stats['total_input'] = len(news_items)
        processed = news_items.copy()

        # Step 1: Deduplication
        if self.enable_deduplication and self.deduplicator:
            initial_count = len(processed)
            processed = self.deduplicator.deduplicate(processed)
            self.stats['duplicates_removed'] = initial_count - len(processed)

        # Step 2: Celebrity Matching
        if self.enable_celebrity_matching and self.celebrity_matcher:
            processed = self.celebrity_matcher.process_items(processed)
            self.stats['celebrity_news'] = sum(
                1 for item in processed if item.get('is_celebrity_news', False)
            )

        # Step 3: Categorization
        if self.enable_categorization and self.categorizer:
            processed = self.categorizer.process_items(processed)
            self.stats['categorized'] = sum(
                1 for item in processed if item.get('category') != 'uncategorized'
            )

        # Step 4: Summarization
        if self.enable_summarization and self.summarizer:
            processed = self.summarizer.process_items(processed)
            self.stats['summarized'] = sum(
                1 for item in processed if item.get('summary')
            )

        self.stats['total_output'] = len(processed)

        return processed

    def process_with_filters(
        self,
        news_items: List[Dict[str, Any]],
        categories: Optional[List[str]] = None,
        min_priority: Optional[str] = None,
        celebrity_only: bool = False,
        high_value_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Process news items and apply filters

        Args:
            news_items: List of raw news items
            categories: Filter by categories (optional)
            min_priority: Minimum priority level (optional)
            celebrity_only: Only include celebrity news
            high_value_only: Only include high-value celebrity deals

        Returns:
            Filtered and processed news items
        """
        # Process through pipeline
        processed = self.process(news_items)

        # Apply filters
        if celebrity_only and self.celebrity_matcher:
            processed = [
                item for item in processed
                if item.get('is_celebrity_news', False)
            ]

        if high_value_only and self.celebrity_matcher:
            processed = [
                item for item in processed
                if item.get('celebrity_match', {}).get('is_high_value', False)
            ]

        if categories and self.categorizer:
            processed = self.categorizer.filter_by_category(processed, categories)

        if min_priority and self.categorizer:
            processed = self.categorizer.filter_by_priority(processed, min_priority)

        return processed

    def get_stats(self) -> Dict[str, int]:
        """
        Get processing statistics

        Returns:
            Dictionary with processing stats
        """
        return self.stats.copy()

    def reset_stats(self):
        """Reset processing statistics"""
        for key in self.stats:
            self.stats[key] = 0

    def clear_caches(self):
        """Clear all processor caches"""
        if self.deduplicator:
            self.deduplicator.clear()

    def get_summary_report(self) -> str:
        """
        Generate a summary report of processing

        Returns:
            Formatted summary string
        """
        report_lines = [
            "Processing Pipeline Summary",
            "=" * 40,
            f"Total Input Items:     {self.stats['total_input']}",
            f"Duplicates Removed:    {self.stats['duplicates_removed']}",
            f"Celebrity News Found:  {self.stats['celebrity_news']}",
            f"Items Categorized:     {self.stats['categorized']}",
            f"Items Summarized:      {self.stats['summarized']}",
            f"Total Output Items:    {self.stats['total_output']}",
            "=" * 40
        ]

        return "\n".join(report_lines)
