"""
Unit tests for RSSReader module.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from src.scrapers.rss_reader import RSSReader


class TestRSSReader:
    """Test suite for RSSReader class."""

    @pytest.fixture
    def mock_config(self):
        """Mock ConfigManager."""
        config = Mock()
        config.get_sources.return_value = [
            {
                'id': 'test_rss_1',
                'name': 'Test RSS Feed',
                'url': 'https://example.com/feed.xml',
                'type': 'rss',
                'category': 'real_estate',
                'enabled': True,
                'rate_limit_ms': 1000
            }
        ]
        return config

    @pytest.fixture
    def reader(self, mock_config):
        """Create reader instance with mocked config."""
        return RSSReader(config_manager=mock_config)

    @pytest.fixture
    def mock_feed_data(self):
        """Mock feedparser response."""
        # Create a Mock object that supports both dict and attribute access
        feed = Mock()
        feed.bozo = False
        feed.entries = [
            {
                'title': 'Test RSS Article',
                'link': 'https://example.com/article/1',
                'summary': 'Test summary content',
                'published_parsed': (2026, 1, 30, 12, 0, 0, 0, 0, 0),
                'author': 'Test Author',
                'tags': [{'term': 'real-estate'}, {'term': 'news'}]
            },
            {
                'title': 'Another Article',
                'link': 'https://example.com/article/2',
                'description': 'Test description',
                'updated_parsed': (2026, 1, 29, 10, 0, 0, 0, 0, 0)
            }
        ]
        return feed

    def test_initialization(self, reader):
        """Test reader initializes correctly."""
        assert reader is not None
        assert reader.config is not None

    def test_generate_id(self, reader):
        """Test ID generation from URL."""
        url = "https://example.com/article/123"
        id1 = reader._generate_id(url)
        id2 = reader._generate_id(url)

        assert id1 == id2  # Same URL should generate same ID
        assert len(id1) == 32  # MD5 hash length

    def test_parse_date_published(self, reader, mock_feed_data):
        """Test date parsing from published_parsed field."""
        entry = type('Entry', (), mock_feed_data.entries[0])()

        date = reader._parse_date(entry)

        assert date.year == 2026
        assert date.month == 1
        assert date.day == 30

    def test_parse_date_fallback(self, reader):
        """Test date parsing falls back to current time."""
        entry = type('Entry', (), {})()

        date = reader._parse_date(entry)

        assert isinstance(date, datetime)

    def test_extract_content_from_summary(self, reader, mock_feed_data):
        """Test content extraction from summary field."""
        entry = type('Entry', (), mock_feed_data.entries[0])()

        content = reader._extract_content(entry)

        assert content == 'Test summary content'

    def test_extract_content_from_description(self, reader, mock_feed_data):
        """Test content extraction from description field."""
        entry = type('Entry', (), mock_feed_data.entries[1])()

        content = reader._extract_content(entry)

        assert content == 'Test description'

    @patch('src.scrapers.rss_reader.feedparser.parse')
    def test_read_feed_success(self, mock_parse, reader, mock_config, mock_feed_data):
        """Test successful RSS feed reading."""
        mock_parse.return_value = mock_feed_data

        source = mock_config.get_sources()[0]
        items = reader.read_feed(source)

        assert len(items) == 2
        assert items[0]['title'] == 'Test RSS Article'
        assert items[0]['source'] == 'Test RSS Feed'
        assert items[0]['category'] == 'real_estate'
        assert items[0]['author'] == 'Test Author'
        assert 'real-estate' in items[0]['tags']

    @patch('src.scrapers.rss_reader.feedparser.parse')
    def test_read_feed_disabled(self, mock_parse, reader, mock_config):
        """Test that disabled sources are skipped."""
        source = mock_config.get_sources()[0]
        source['enabled'] = False

        items = reader.read_feed(source)

        assert len(items) == 0
        mock_parse.assert_not_called()

    @patch('src.scrapers.rss_reader.feedparser.parse')
    def test_read_feed_wrong_type(self, mock_parse, reader, mock_config):
        """Test that non-RSS sources are skipped."""
        source = mock_config.get_sources()[0]
        source['type'] = 'scrape'

        items = reader.read_feed(source)

        assert len(items) == 0
        mock_parse.assert_not_called()

    @patch('src.scrapers.rss_reader.feedparser.parse')
    def test_read_feed_with_bozo(self, mock_parse, reader, mock_config, mock_feed_data):
        """Test handling of malformed feeds (bozo=True)."""
        mock_feed_data.bozo = True
        mock_parse.return_value = mock_feed_data

        source = mock_config.get_sources()[0]
        items = reader.read_feed(source)

        # Should still process entries despite bozo flag
        assert len(items) == 2

    @patch('src.scrapers.rss_reader.feedparser.parse')
    def test_read_feed_error(self, mock_parse, reader, mock_config):
        """Test handling of feed parsing errors."""
        mock_parse.side_effect = Exception("Parse error")

        source = mock_config.get_sources()[0]
        items = reader.read_feed(source)

        assert len(items) == 0

    @patch('src.scrapers.rss_reader.feedparser.parse')
    def test_read_all(self, mock_parse, reader, mock_feed_data):
        """Test reading all RSS feeds."""
        mock_parse.return_value = mock_feed_data

        items = reader.read_all()

        assert len(items) >= 2
        assert all('title' in item for item in items)

    @patch('src.scrapers.rss_reader.feedparser.parse')
    def test_read_by_category(self, mock_parse, reader, mock_feed_data):
        """Test filtering feeds by category."""
        mock_parse.return_value = mock_feed_data

        items = reader.read_by_category('real_estate')

        assert len(items) >= 2
        assert all(item['category'] == 'real_estate' for item in items)

    @patch('src.scrapers.rss_reader.feedparser.parse')
    def test_rate_limiting(self, mock_parse, reader, mock_config, mock_feed_data):
        """Test rate limiting enforcement."""
        mock_parse.return_value = mock_feed_data

        source = mock_config.get_sources()[0]
        source['rate_limit_ms'] = 100

        start_time = datetime.now()
        reader.read_feed(source)
        reader.read_feed(source)
        elapsed = (datetime.now() - start_time).total_seconds() * 1000

        # Should have waited at least 100ms
        assert elapsed >= 100
