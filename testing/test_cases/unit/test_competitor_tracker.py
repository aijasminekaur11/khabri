"""
Unit tests for CompetitorTracker module.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from src.scrapers.competitor_tracker import CompetitorTracker


class TestCompetitorTracker:
    """Test suite for CompetitorTracker class."""

    @pytest.fixture
    def mock_config(self):
        """Mock ConfigManager."""
        config = Mock()
        config.get_sources.return_value = [
            {
                'id': 'competitor_1',
                'name': 'Competitor News',
                'url': 'https://competitor.com',
                'type': 'scrape',
                'category': 'competitor',
                'enabled': True,
                'rate_limit_ms': 2000,
                'selectors': {
                    'container': 'article',
                    'title': 'h2',
                    'link': 'a',
                    'date': 'time'
                }
            }
        ]
        return config

    @pytest.fixture
    def tracker(self, mock_config):
        """Create tracker instance with mocked config."""
        return CompetitorTracker(config_manager=mock_config)

    @pytest.fixture
    def mock_html_response(self):
        """Sample competitor HTML."""
        return """
        <html>
            <body>
                <article>
                    <h2>Competitor Article 1</h2>
                    <a href="/article/1">Read</a>
                    <time>2026-01-30</time>
                </article>
                <article>
                    <h2>Competitor Article 2</h2>
                    <a href="/article/2">Read</a>
                    <time>2026-01-29</time>
                </article>
            </body>
        </html>
        """

    def test_initialization(self, tracker):
        """Test tracker initializes correctly."""
        assert tracker is not None
        assert tracker.config is not None
        assert tracker.tracked_articles == {}

    def test_generate_id(self, tracker):
        """Test ID generation from URL."""
        url = "https://competitor.com/article/123"
        id1 = tracker._generate_id(url)
        id2 = tracker._generate_id(url)

        assert id1 == id2
        assert len(id1) == 32

    def test_extract_articles(self, tracker, mock_html_response):
        """Test article extraction from HTML."""
        selectors = {
            'container': 'article',
            'title': 'h2',
            'link': 'a',
            'date': 'time'
        }

        articles = tracker._extract_articles(mock_html_response, selectors)

        assert len(articles) == 2
        assert articles[0]['title'] == 'Competitor Article 1'
        assert articles[0]['link'] == '/article/1'

    def test_analyze_content_gap_not_covered(self, tracker):
        """Test gap detection when we haven't covered the topic."""
        competitor_article = {'title': 'New Real Estate Policy Announced'}
        our_content = [
            {'title': 'Local Market Update'},
            {'title': 'Property Prices Rising'}
        ]

        gaps = tracker._analyze_content_gap(competitor_article, our_content)

        assert len(gaps) > 0
        assert 'Not covered' in gaps[0]

    def test_analyze_content_gap_covered(self, tracker):
        """Test when we've already covered similar topic."""
        competitor_article = {'title': 'Real Estate Policy Announced'}
        our_content = [
            {'title': 'Real Estate Policy Update Announced'}
        ]

        gaps = tracker._analyze_content_gap(competitor_article, our_content)

        assert len(gaps) == 0

    def test_calculate_opportunity_window(self, tracker):
        """Test opportunity window calculation."""
        now = datetime.now()

        window = tracker._calculate_opportunity_window(now)

        assert window == 180  # Full 3-hour window for just-published

    @patch('src.scrapers.competitor_tracker.requests.Session.get')
    def test_track_competitor_success(self, mock_get, tracker, mock_config, mock_html_response):
        """Test successful competitor tracking."""
        mock_response = Mock()
        mock_response.text = mock_html_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        source = mock_config.get_sources()[0]
        our_content = []

        alerts = tracker.track_competitor(source, our_content)

        assert len(alerts) >= 1
        assert all('competitor' in alert for alert in alerts)
        assert all('gaps' in alert for alert in alerts)

    @patch('src.scrapers.competitor_tracker.requests.Session.get')
    def test_track_competitor_disabled(self, mock_get, tracker, mock_config):
        """Test that disabled sources are skipped."""
        source = mock_config.get_sources()[0]
        source['enabled'] = False

        alerts = tracker.track_competitor(source, [])

        assert len(alerts) == 0
        mock_get.assert_not_called()

    @patch('src.scrapers.competitor_tracker.requests.Session.get')
    def test_track_competitor_wrong_category(self, mock_get, tracker, mock_config):
        """Test that non-competitor sources are skipped."""
        source = mock_config.get_sources()[0]
        source['category'] = 'real_estate'

        alerts = tracker.track_competitor(source, [])

        assert len(alerts) == 0
        mock_get.assert_not_called()

    @patch('src.scrapers.competitor_tracker.requests.Session.get')
    def test_track_all_competitors(self, mock_get, tracker, mock_html_response):
        """Test tracking all competitors."""
        mock_response = Mock()
        mock_response.text = mock_html_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        alerts = tracker.track_all_competitors([])

        assert isinstance(alerts, list)

    @patch('src.scrapers.competitor_tracker.requests.Session.get')
    def test_get_high_priority_alerts(self, mock_get, tracker, mock_html_response):
        """Test filtering for high-priority alerts."""
        mock_response = Mock()
        mock_response.text = mock_html_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        alerts = tracker.get_high_priority_alerts([])

        # All should have opportunity_window >= 120
        assert all(alert['opportunity_window'] >= 120 for alert in alerts)

    @patch('src.scrapers.competitor_tracker.requests.Session.get')
    def test_duplicate_article_tracking(self, mock_get, tracker, mock_config, mock_html_response):
        """Test that already-tracked articles don't generate duplicate alerts."""
        mock_response = Mock()
        mock_response.text = mock_html_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        source = mock_config.get_sources()[0]

        # First call should generate alerts
        alerts1 = tracker.track_competitor(source, [])
        initial_count = len(alerts1)

        # Second call should not generate alerts for same articles
        alerts2 = tracker.track_competitor(source, [])

        assert len(alerts2) == 0  # Already tracked
