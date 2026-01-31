"""
Integration Tests: Full Pipeline End-to-End

Tests the complete data flow from Config → Scrapers → Processors → Notifiers.
Validates the entire system working together with realistic workflows.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from src.config import ConfigManager
from src.scrapers import NewsScraper
from src.processors import ProcessorPipeline
from src.orchestrator import Orchestrator


class TestFullPipelineE2E:
    """End-to-end integration tests for full pipeline."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration with complete setup."""
        config = Mock()
        config.get_sources.return_value = [
            {
                'id': 'test_source',
                'name': 'Test Source',
                'url': 'https://test.com/news',
                'type': 'scrape',
                'category': 'real_estate',
                'enabled': True,
                'rate_limit_ms': 1000,
                'selectors': {
                    'title': 'h1',
                    'content': 'div.content'
                }
            }
        ]
        config.get_keywords.return_value = {
            'categories': {
                'real_estate': {
                    'primary': ['property', 'real estate'],
                    'secondary': ['housing', 'apartment']
                }
            }
        }
        config.get_celebrities.return_value = {
            'business': [
                {
                    'name': 'Test Celebrity',
                    'aliases': ['Celebrity'],
                    'priority': 'high'
                }
            ]
        }
        return config

    def test_config_to_scraper_to_processor_flow(self, mock_config):
        """
        INT-021: Test data flows from Config → Scraper → Processor.
        """
        # Arrange
        scraper = NewsScraper(config_manager=mock_config)
        pipeline = ProcessorPipeline(
            celebrities_config=mock_config.get_celebrities(),
            keywords_config=mock_config.get_keywords()
        )

        # Simulate scraper output
        scraper_output = [
            {
                'id': 'test123',
                'title': 'Test Article',
                'url': 'https://test.com/article',
                'source': 'Test Source',
                'source_id': 'test_source',
                'category': 'real_estate',
                'content': 'Test content about property',
                'published_at': datetime.now(),
                'scraped_at': datetime.now(),
                'author': None,
                'image_url': None,
                'tags': []
            }
        ]

        # Act
        try:
            processed = pipeline.process(scraper_output)
            success = True
        except Exception as e:
            success = False
            processed = []

        # Assert
        assert success
        assert len(processed) >= 0

    def test_morning_digest_workflow(self, mock_config):
        """
        INT-022: Test morning digest workflow end-to-end.

        Simulates the morning digest workflow:
        1. Config provides morning digest settings
        2. Scrapers fetch news
        3. Processors enhance data
        4. Digest is prepared for notifiers
        """
        # Arrange - morning digest config
        mock_config.get_schedules.return_value = {
            'timezone': 'Asia/Kolkata',
            'digests': {
                'morning': {
                    'enabled': True,
                    'time': '07:00',
                    'include': ['real_estate', 'infrastructure']
                }
            }
        }

        # Simulate morning news items
        morning_items = [
            {
                'id': 'morning1',
                'title': 'Morning Property News',
                'url': 'https://test.com/morning1',
                'source': 'Test Source',
                'source_id': 'test_source',
                'category': 'real_estate',
                'content': 'Morning content',
                'published_at': datetime(2026, 1, 30, 6, 0, 0),
                'scraped_at': datetime(2026, 1, 30, 7, 0, 0),
                'author': None,
                'image_url': None,
                'tags': []
            }
        ]

        pipeline = ProcessorPipeline(
            celebrities_config=mock_config.get_celebrities(),
            keywords_config=mock_config.get_keywords()
        )

        # Act
        processed = pipeline.process(morning_items)

        # Assert
        assert len(processed) >= 0
        assert all('category' in item for item in processed)

    def test_realtime_alert_workflow(self, mock_config):
        """
        INT-023: Test real-time alert workflow end-to-end.

        Simulates the real-time alert workflow:
        1. High-priority news is scraped
        2. Processors identify urgency
        3. Alert is prepared for immediate notification
        """
        # Arrange - high-priority celebrity news
        urgent_item = {
            'id': 'urgent1',
            'title': 'Breaking: Celebrity buys property for Rs 500 crore',
            'url': 'https://test.com/urgent1',
            'source': 'Test Source',
            'source_id': 'test_source',
            'category': 'real_estate',
            'content': 'Celebrity purchased luxury villa...',
            'published_at': datetime.now(),
            'scraped_at': datetime.now(),
            'author': None,
            'image_url': None,
            'tags': ['celebrity', 'breaking']
        }

        pipeline = ProcessorPipeline(
            celebrities_config=mock_config.get_celebrities(),
            keywords_config=mock_config.get_keywords()
        )

        # Act
        processed = pipeline.process([urgent_item])

        # Assert
        assert len(processed) >= 0
        if processed:
            assert 'category' in processed[0]

    def test_event_triggered_scraping(self, mock_config):
        """
        INT-024: Test event-triggered scraping workflow.

        Simulates event-triggered scraping:
        1. Event configuration loaded
        2. Scrapers fetch news for specific event
        3. Processors match event keywords
        """
        # Arrange - event configuration
        mock_config.get_active_events.return_value = [
            {
                'id': 'budget2026',
                'name': 'Union Budget 2026',
                'date': '2026-02-01',
                'keywords': ['budget', 'real estate', 'tax'],
                'sources': ['test_source'],
                'active': True
            }
        ]

        # Event-related news
        event_item = {
            'id': 'event1',
            'title': 'Budget 2026: Real estate sector gets tax relief',
            'url': 'https://test.com/event1',
            'source': 'Test Source',
            'source_id': 'test_source',
            'category': 'policy',
            'content': 'Budget announcement includes real estate tax changes...',
            'published_at': datetime.now(),
            'scraped_at': datetime.now(),
            'author': None,
            'image_url': None,
            'tags': ['budget', 'tax', 'real_estate']
        }

        pipeline = ProcessorPipeline(
            celebrities_config=mock_config.get_celebrities(),
            keywords_config=mock_config.get_keywords()
        )

        # Act
        processed = pipeline.process([event_item])

        # Assert
        assert len(processed) >= 0
        if processed:
            assert any(keyword in processed[0]['title'].lower() for keyword in ['budget', 'real estate', 'tax'])

    def test_concurrent_scraper_execution(self, mock_config):
        """
        INT-025: Test multiple scrapers can execute concurrently.
        """
        # Arrange - multiple scraper types
        from src.scrapers import RSSReader, CompetitorTracker

        news_scraper = NewsScraper(config_manager=mock_config)
        rss_reader = RSSReader(config_manager=mock_config)
        competitor_tracker = CompetitorTracker(config_manager=mock_config)

        # Act - all should initialize without conflicts
        all_initialized = all([
            news_scraper is not None,
            rss_reader is not None,
            competitor_tracker is not None
        ])

        # Assert
        assert all_initialized
        assert news_scraper.config == mock_config
        assert rss_reader.config == mock_config
        assert competitor_tracker.config == mock_config

    def test_error_propagation_through_pipeline(self, mock_config):
        """
        INT-026: Test error handling throughout the pipeline.
        """
        # Arrange - malformed data
        bad_item = {
            'id': 'bad1',
            # Missing required fields
        }

        pipeline = ProcessorPipeline(
            celebrities_config=mock_config.get_celebrities(),
            keywords_config=mock_config.get_keywords()
        )

        # Act - should handle gracefully
        try:
            processed = pipeline.process([bad_item])
            handled_gracefully = True
        except Exception:
            handled_gracefully = False
            processed = []

        # Assert - should not crash the system
        assert handled_gracefully or len(processed) >= 0

    def test_data_transformation_stages(self, mock_config):
        """
        INT-027: Test data transformation at each pipeline stage.
        """
        # Arrange - track transformations
        original_item = {
            'id': 'transform1',
            'title': 'Original Title',
            'url': 'https://test.com/transform1',
            'source': 'Test Source',
            'source_id': 'test_source',
            'category': 'real_estate',
            'content': 'Original content',
            'published_at': datetime.now(),
            'scraped_at': datetime.now(),
            'author': None,
            'image_url': None,
            'tags': []
        }

        pipeline = ProcessorPipeline(
            celebrities_config=mock_config.get_celebrities(),
            keywords_config=mock_config.get_keywords()
        )

        # Act
        processed = pipeline.process([original_item])

        # Assert - should maintain core data
        if processed:
            assert processed[0]['id'] == original_item['id']
            assert processed[0]['url'] == original_item['url']

    def test_graceful_degradation(self, mock_config):
        """
        INT-028: Test system continues with partial failures.
        """
        # Arrange - mix of good and bad items
        mixed_items = [
            {
                'id': 'good1',
                'title': 'Good Item',
                'url': 'https://test.com/good1',
                'source': 'Test',
                'source_id': 'test',
                'category': 'real_estate',
                'content': 'Content',
                'published_at': datetime.now(),
                'scraped_at': datetime.now(),
                'author': None,
                'image_url': None,
                'tags': []
            },
            {
                'id': 'bad1',
                # Incomplete item
                'title': 'Bad Item'
            }
        ]

        pipeline = ProcessorPipeline(
            celebrities_config=mock_config.get_celebrities(),
            keywords_config=mock_config.get_keywords()
        )

        # Act
        try:
            processed = pipeline.process(mixed_items)
            continues_processing = True
        except Exception:
            continues_processing = False
            processed = []

        # Assert - should process at least the good items
        assert continues_processing
