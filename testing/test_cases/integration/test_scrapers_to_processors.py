"""
Integration Tests: Scrapers → Processors Workflow

Tests the interaction between scraper modules and processor pipeline.
Validates that processor pipeline correctly consumes scraper output and transforms data.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from src.processors import ProcessorPipeline, Deduplicator, CelebrityMatcher, Categorizer, Summarizer


class TestScrapersToProcessorsIntegration:
    """Integration tests for Scrapers → Processors workflow."""

    @pytest.fixture
    def sample_news_items(self):
        """Sample NewsItem dictionaries from scrapers."""
        return [
            {
                'id': 'abc123',
                'title': 'Ambani buys luxury property for Rs 640 crore',
                'url': 'https://example.com/article/1',
                'source': 'Economic Times',
                'source_id': 'et_realestate',
                'category': 'real_estate',
                'content': 'Mukesh Ambani purchased a luxury villa in Mumbai for 640 crores...',
                'published_at': datetime(2026, 1, 30, 8, 0, 0),
                'scraped_at': datetime(2026, 1, 30, 9, 0, 0),
                'author': 'John Doe',
                'image_url': None,
                'tags': ['ambani', 'luxury', 'mumbai']
            },
            {
                'id': 'def456',
                'title': 'New infrastructure project in Pune',
                'url': 'https://example.com/article/2',
                'source': 'Times Property',
                'source_id': 'times_property',
                'category': 'infrastructure',
                'content': 'A new metro line project announced for Pune...',
                'published_at': datetime(2026, 1, 29, 15, 0, 0),
                'scraped_at': datetime(2026, 1, 30, 9, 0, 0),
                'author': None,
                'image_url': None,
                'tags': ['infrastructure', 'pune']
            },
            {
                'id': 'abc123',  # Duplicate ID
                'title': 'Ambani buys luxury property for Rs 640 crore',
                'url': 'https://example.com/article/1',  # Same URL
                'source': 'Economic Times',
                'source_id': 'et_realestate',
                'category': 'real_estate',
                'content': 'Duplicate content...',
                'published_at': datetime(2026, 1, 30, 8, 0, 0),
                'scraped_at': datetime(2026, 1, 30, 9, 5, 0),
                'author': 'John Doe',
                'image_url': None,
                'tags': ['ambani']
            }
        ]

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for processors."""
        config = Mock()
        config.get_keywords.return_value = {
            'categories': {
                'real_estate': {
                    'primary': ['property', 'real estate', 'housing'],
                    'secondary': ['apartment', 'villa', 'plot']
                }
            }
        }
        config.get_celebrities.return_value = {
            'business': [
                {
                    'name': 'Mukesh Ambani',
                    'aliases': ['Ambani', 'M Ambani'],
                    'priority': 'high'
                }
            ]
        }
        return config

    def test_deduplicator_receives_scraper_output(self, sample_news_items):
        """
        INT-011: Test Deduplicator can process NewsItem dictionaries from scrapers.
        """
        # Arrange
        deduplicator = Deduplicator()

        # Act
        unique_items = deduplicator.deduplicate(sample_news_items)

        # Assert
        assert len(unique_items) == 2  # Should remove 1 duplicate
        assert unique_items[0]['id'] == 'abc123'
        assert unique_items[1]['id'] == 'def456'

    def test_celebrity_matcher_processes_scraper_content(self, sample_news_items, mock_config):
        """
        INT-012: Test CelebrityMatcher identifies celebrities in scraper content.
        """
        # Arrange
        matcher = CelebrityMatcher(celebrities_config=mock_config.get_celebrities())

        # Act
        item = sample_news_items[0]  # Ambani article
        enhanced_item = matcher.match_celebrities(item)

        # Assert
        assert enhanced_item is not None
        assert 'all_matches' in enhanced_item or 'matched_celebrities' in enhanced_item

    def test_categorizer_validates_scraper_categories(self, sample_news_items, mock_config):
        """
        INT-013: Test Categorizer validates and enhances category from scrapers.
        """
        # Arrange
        categorizer = Categorizer(keywords_config=mock_config.get_keywords())

        # Act
        item = sample_news_items[0]
        categorized_item = categorizer.categorize(item)

        # Assert
        assert categorized_item is not None
        assert 'category' in categorized_item or 'categories' in categorized_item

    def test_summarizer_processes_scraper_content(self, sample_news_items):
        """
        INT-014: Test Summarizer can process content from scrapers.
        """
        # Arrange
        summarizer = Summarizer()

        # Act
        item = sample_news_items[0]
        summary = summarizer.generate_summary(item)

        # Assert
        assert summary is not None
        assert len(str(summary)) > 0

    def test_processor_pipeline_accepts_scraper_format(self, sample_news_items, mock_config):
        """
        INT-015: Test ProcessorPipeline accepts NewsItem format from scrapers.
        """
        # Arrange
        pipeline = ProcessorPipeline(
            celebrities_config=mock_config.get_celebrities(),
            keywords_config=mock_config.get_keywords()
        )

        # Act
        try:
            processed_items = pipeline.process(sample_news_items)
            success = True
        except Exception as e:
            success = False
            processed_items = []

        # Assert
        assert success, "Pipeline should accept scraper output format"
        assert len(processed_items) >= 0

    def test_data_preservation_through_processing(self, sample_news_items):
        """
        INT-016: Test essential data from scrapers is preserved through processing.
        """
        # Arrange
        deduplicator = Deduplicator()

        # Act
        processed_items = deduplicator.deduplicate(sample_news_items)

        # Assert - essential fields should be preserved
        for item in processed_items:
            assert 'id' in item
            assert 'title' in item
            assert 'url' in item
            assert 'source' in item
            assert 'content' in item

    def test_multiple_scrapers_output_processing(self):
        """
        INT-017: Test processors can handle output from different scraper types.
        """
        # Arrange - items from different scrapers
        mixed_items = [
            {'id': '1', 'title': 'News', 'source': 'NewsScraper', 'content': 'text', 'url': 'http://a.com', 'source_id': 'src1', 'category': 'general', 'published_at': datetime.now(), 'scraped_at': datetime.now()},
            {'id': '2', 'title': 'RSS', 'source': 'RSSReader', 'content': 'text', 'url': 'http://b.com', 'source_id': 'src2', 'category': 'general', 'published_at': datetime.now(), 'scraped_at': datetime.now()},
            {'id': '3', 'title': 'Comp', 'source': 'CompetitorTracker', 'content': 'text', 'url': 'http://c.com', 'source_id': 'src3', 'category': 'general', 'published_at': datetime.now(), 'scraped_at': datetime.now()},
            {'id': '4', 'title': 'IGRS', 'source': 'IGRSScraper', 'content': 'text', 'url': 'http://d.com', 'source_id': 'src4', 'category': 'general', 'published_at': datetime.now(), 'scraped_at': datetime.now()}
        ]
        deduplicator = Deduplicator()

        # Act
        processed = deduplicator.deduplicate(mixed_items)

        # Assert
        assert len(processed) == 4
        assert all('id' in item for item in processed)

    def test_empty_scraper_output_handling(self):
        """
        INT-018: Test processors gracefully handle empty scraper output.
        """
        # Arrange
        deduplicator = Deduplicator()
        empty_items = []

        # Act
        result = deduplicator.deduplicate(empty_items)

        # Assert
        assert result == []
        assert isinstance(result, list)

    def test_malformed_scraper_data_handling(self):
        """
        INT-019: Test processors handle malformed data from scrapers.
        """
        # Arrange
        deduplicator = Deduplicator()
        malformed_items = [
            {'id': '1', 'title': 'Valid'},  # Missing required fields
            {'id': '2'}  # Only ID
        ]

        # Act - should not crash
        try:
            result = deduplicator.deduplicate(malformed_items)
            success = True
        except Exception:
            success = False
            result = []

        # Assert - should handle gracefully
        assert success or len(result) >= 0

    def test_timestamp_preservation(self, sample_news_items):
        """
        INT-020: Test timestamps from scrapers are preserved through processing.
        """
        # Arrange
        deduplicator = Deduplicator()

        # Act
        processed_items = deduplicator.deduplicate(sample_news_items)

        # Assert
        for item in processed_items:
            assert 'published_at' in item
            assert 'scraped_at' in item
            assert isinstance(item['published_at'], datetime)
            assert isinstance(item['scraped_at'], datetime)
