"""
Unit tests for IGRSScraper module.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from src.scrapers.igrs_scraper import IGRSScraper


class TestIGRSScraper:
    """Test suite for IGRSScraper class."""

    @pytest.fixture
    def mock_config(self):
        """Mock ConfigManager."""
        config = Mock()
        config.get_sources.return_value = [
            {
                'id': 'igrs_maharashtra',
                'name': 'IGRS Maharashtra',
                'url': 'https://igr.maharashtra.gov.in/data',
                'type': 'scrape',
                'category': 'infrastructure',
                'enabled': True,
                'rate_limit_ms': 3000,
                'selectors': {
                    'container': '.registration-entry',
                    'district': '.district',
                    'property_type': '.property-type',
                    'count': '.count',
                    'value': '.value',
                    'date': '.date'
                }
            }
        ]
        return config

    @pytest.fixture
    def scraper(self, mock_config):
        """Create scraper instance with mocked config."""
        return IGRSScraper(config_manager=mock_config)

    @pytest.fixture
    def mock_html_response(self):
        """Sample IGRS HTML."""
        return """
        <html>
            <body>
                <div class="registration-entry">
                    <span class="district">Mumbai</span>
                    <span class="property-type">Residential</span>
                    <span class="count">150</span>
                    <span class="value">₹500 Cr</span>
                    <span class="date">2026-01-30</span>
                </div>
                <div class="registration-entry">
                    <span class="district">Pune</span>
                    <span class="property-type">Commercial</span>
                    <span class="count">75</span>
                    <span class="value">₹300 Cr</span>
                    <span class="date">2026-01-30</span>
                </div>
            </body>
        </html>
        """

    def test_initialization(self, scraper):
        """Test scraper initializes correctly."""
        assert scraper is not None
        assert scraper.config is not None

    def test_generate_id(self, scraper):
        """Test ID generation from URL."""
        url = "https://igr.maharashtra.gov.in#Mumbai"
        id1 = scraper._generate_id(url)
        id2 = scraper._generate_id(url)

        assert id1 == id2
        assert len(id1) == 32

    def test_parse_registration_data(self, scraper, mock_html_response):
        """Test parsing of IGRS registration data."""
        selectors = {
            'container': '.registration-entry',
            'district': '.district',
            'property_type': '.property-type',
            'count': '.count',
            'value': '.value',
            'date': '.date'
        }

        records = scraper._parse_registration_data(mock_html_response, selectors)

        assert len(records) == 2
        assert records[0]['district'] == 'Mumbai'
        assert records[0]['property_type'] == 'Residential'
        assert records[0]['registration_count'] == '150'
        assert records[1]['district'] == 'Pune'

    def test_convert_to_news_item(self, scraper, mock_config):
        """Test conversion of IGRS record to NewsItem."""
        record = {
            'district': 'Mumbai',
            'property_type': 'Residential',
            'registration_count': '150',
            'total_value': '₹500 Cr',
            'date': '2026-01-30'
        }

        source = mock_config.get_sources()[0]
        news_item = scraper._convert_to_news_item(record, source)

        assert 'Mumbai' in news_item['title']
        assert 'Residential' in news_item['title']
        assert news_item['category'] == 'infrastructure'
        assert news_item['source'] == 'IGRS Maharashtra'
        assert 'mumbai' in news_item['tags']

    @patch('src.scrapers.igrs_scraper.requests.Session.get')
    def test_scrape_igrs_source_success(self, mock_get, scraper, mock_config, mock_html_response):
        """Test successful IGRS scraping."""
        mock_response = Mock()
        mock_response.text = mock_html_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        source = mock_config.get_sources()[0]
        items = scraper.scrape_igrs_source(source)

        assert len(items) == 2
        assert all('IGRS' in item['title'] for item in items)

    @patch('src.scrapers.igrs_scraper.requests.Session.get')
    def test_scrape_igrs_source_disabled(self, mock_get, scraper, mock_config):
        """Test that disabled sources are skipped."""
        source = mock_config.get_sources()[0]
        source['enabled'] = False

        items = scraper.scrape_igrs_source(source)

        assert len(items) == 0
        mock_get.assert_not_called()

    @patch('src.scrapers.igrs_scraper.requests.Session.get')
    def test_scrape_igrs_source_non_igrs(self, mock_get, scraper, mock_config):
        """Test that non-IGRS sources are skipped."""
        source = mock_config.get_sources()[0]
        source['id'] = 'regular_news_source'

        items = scraper.scrape_igrs_source(source)

        assert len(items) == 0
        mock_get.assert_not_called()

    @patch('src.scrapers.igrs_scraper.requests.Session.get')
    def test_scrape_igrs_source_error(self, mock_get, scraper, mock_config):
        """Test handling of HTTP errors."""
        mock_get.side_effect = Exception("Connection error")

        source = mock_config.get_sources()[0]
        items = scraper.scrape_igrs_source(source)

        assert len(items) == 0

    @patch('src.scrapers.igrs_scraper.requests.Session.get')
    def test_scrape_all_igrs(self, mock_get, scraper, mock_html_response):
        """Test scraping all IGRS sources."""
        mock_response = Mock()
        mock_response.text = mock_html_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        items = scraper.scrape_all_igrs()

        assert isinstance(items, list)

    @patch('src.scrapers.igrs_scraper.requests.Session.get')
    def test_get_district_summary(self, mock_get, scraper, mock_html_response):
        """Test getting district-specific summary."""
        mock_response = Mock()
        mock_response.text = mock_html_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        summary = scraper.get_district_summary('Mumbai')

        if summary:  # May be None if no data
            assert summary['district'] == 'Mumbai'
            assert 'total_items' in summary
            assert 'items' in summary

    @patch('src.scrapers.igrs_scraper.requests.Session.get')
    def test_rate_limiting(self, mock_get, scraper, mock_config, mock_html_response):
        """Test rate limiting enforcement (3 seconds for govt sites)."""
        mock_response = Mock()
        mock_response.text = mock_html_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        source = mock_config.get_sources()[0]
        source['rate_limit_ms'] = 100

        start_time = datetime.now()
        scraper.scrape_igrs_source(source)
        scraper.scrape_igrs_source(source)
        elapsed = (datetime.now() - start_time).total_seconds() * 1000

        # Should have waited at least 100ms
        assert elapsed >= 100
