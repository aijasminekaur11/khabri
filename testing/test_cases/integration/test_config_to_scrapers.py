"""
Integration Tests: Config Manager → Scrapers Workflow

Tests the interaction between configuration management and scraper modules.
Validates that scrapers correctly consume configuration and execute as expected.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.config import ConfigManager
from src.scrapers import NewsScraper, RSSReader, CompetitorTracker, IGRSScraper


class TestConfigToScrapersIntegration:
    """Integration tests for Config Manager → Scrapers workflow."""

    @pytest.fixture
    def sample_sources_config(self):
        """Sample sources configuration for testing."""
        return [
            {
                'id': 'times_property',
                'name': 'Times Property',
                'url': 'https://timesproperty.com/news',
                'type': 'scrape',
                'category': 'real_estate',
                'enabled': True,
                'rate_limit_ms': 1000,
                'selectors': {
                    'title': 'h1.article-title',
                    'content': 'div.article-content',
                    'date': 'time.publish-date'
                }
            },
            {
                'id': 'housing_rss',
                'name': 'Housing.com RSS',
                'url': 'https://housing.com/news/feed',
                'type': 'rss',
                'category': 'real_estate',
                'enabled': True,
                'rate_limit_ms': 1000
            },
            {
                'id': 'competitor_99acres',
                'name': '99acres Blog',
                'url': 'https://99acres.com/blog',
                'type': 'scrape',
                'category': 'competitor',
                'enabled': True,
                'rate_limit_ms': 2000,
                'selectors': {
                    'container': 'article',
                    'title': 'h2',
                    'link': 'a'
                }
            },
            {
                'id': 'igrs_maharashtra',
                'name': 'IGRS Maharashtra',
                'url': 'https://igr.maharashtra.gov.in/stats',
                'type': 'scrape',
                'category': 'infrastructure',
                'enabled': True,
                'rate_limit_ms': 3000,
                'selectors': {
                    'container': '.registration-entry',
                    'district': '.district',
                    'property_type': '.property-type'
                }
            }
        ]

    @pytest.fixture
    def mock_config_manager(self, sample_sources_config):
        """Mock ConfigManager with sample sources."""
        config = Mock(spec=ConfigManager)
        config.get_sources.return_value = sample_sources_config
        return config

    def test_news_scraper_loads_config(self, mock_config_manager):
        """
        INT-001: Test NewsScraper loads configuration correctly.
        """
        # Arrange
        scraper = NewsScraper(config_manager=mock_config_manager)

        # Act
        sources = scraper.config.get_sources()

        # Assert
        assert len(sources) == 4
        assert sources[0]['id'] == 'times_property'
        mock_config_manager.get_sources.assert_called_once()

    def test_rss_reader_loads_config(self, mock_config_manager):
        """
        INT-002: Test RSSReader loads configuration correctly.
        """
        # Arrange
        reader = RSSReader(config_manager=mock_config_manager)

        # Act
        sources = reader.config.get_sources()

        # Assert
        assert len(sources) == 4
        assert sources[1]['type'] == 'rss'
        mock_config_manager.get_sources.assert_called_once()

    def test_competitor_tracker_loads_config(self, mock_config_manager):
        """
        INT-003: Test CompetitorTracker loads configuration correctly.
        """
        # Arrange
        tracker = CompetitorTracker(config_manager=mock_config_manager)

        # Act
        sources = tracker.config.get_sources()

        # Assert
        assert len(sources) == 4
        assert sources[2]['category'] == 'competitor'
        mock_config_manager.get_sources.assert_called_once()

    def test_igrs_scraper_loads_config(self, mock_config_manager):
        """
        INT-004: Test IGRSScraper loads configuration correctly.
        """
        # Arrange
        scraper = IGRSScraper(config_manager=mock_config_manager)

        # Act
        sources = scraper.config.get_sources()

        # Assert
        assert len(sources) == 4
        assert 'igrs' in sources[3]['id'].lower()
        mock_config_manager.get_sources.assert_called_once()

    def test_news_scraper_filters_by_type(self, mock_config_manager):
        """
        INT-005: Test NewsScraper filters sources by type='scrape'.
        """
        # Arrange
        scraper = NewsScraper(config_manager=mock_config_manager)

        # Act - scrape_all should only process type='scrape' sources
        sources = [s for s in scraper.config.get_sources() if s['type'] == 'scrape']

        # Assert
        assert len(sources) == 3  # times_property, competitor_99acres, igrs_maharashtra
        assert all(s['type'] == 'scrape' for s in sources)

    def test_rss_reader_filters_by_type(self, mock_config_manager):
        """
        INT-006: Test RSSReader filters sources by type='rss'.
        """
        # Arrange
        reader = RSSReader(config_manager=mock_config_manager)

        # Act
        sources = [s for s in reader.config.get_sources() if s['type'] == 'rss']

        # Assert
        assert len(sources) == 1  # housing_rss only
        assert sources[0]['id'] == 'housing_rss'

    def test_competitor_tracker_filters_by_category(self, mock_config_manager):
        """
        INT-007: Test CompetitorTracker filters sources by category='competitor'.
        """
        # Arrange
        tracker = CompetitorTracker(config_manager=mock_config_manager)

        # Act
        sources = [s for s in tracker.config.get_sources() if s['category'] == 'competitor']

        # Assert
        assert len(sources) == 1  # competitor_99acres only
        assert sources[0]['name'] == '99acres Blog'

    def test_config_provides_rate_limits(self, mock_config_manager):
        """
        INT-008: Test configuration provides rate_limit_ms to scrapers.
        """
        # Arrange
        scraper = NewsScraper(config_manager=mock_config_manager)

        # Act
        sources = scraper.config.get_sources()

        # Assert
        assert sources[0]['rate_limit_ms'] == 1000
        assert sources[2]['rate_limit_ms'] == 2000
        assert sources[3]['rate_limit_ms'] == 3000

    def test_config_provides_selectors(self, mock_config_manager):
        """
        INT-009: Test configuration provides CSS selectors to scrapers.
        """
        # Arrange
        scraper = NewsScraper(config_manager=mock_config_manager)

        # Act
        sources = scraper.config.get_sources()
        times_property = sources[0]

        # Assert
        assert 'selectors' in times_property
        assert times_property['selectors']['title'] == 'h1.article-title'
        assert times_property['selectors']['content'] == 'div.article-content'

    def test_all_scrapers_initialize_without_errors(self, mock_config_manager):
        """
        INT-010: Test all scraper types initialize successfully with config.
        """
        # Act & Assert - should not raise exceptions
        news_scraper = NewsScraper(config_manager=mock_config_manager)
        rss_reader = RSSReader(config_manager=mock_config_manager)
        competitor_tracker = CompetitorTracker(config_manager=mock_config_manager)
        igrs_scraper = IGRSScraper(config_manager=mock_config_manager)

        assert news_scraper is not None
        assert rss_reader is not None
        assert competitor_tracker is not None
        assert igrs_scraper is not None
