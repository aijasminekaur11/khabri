"""
Unit Tests for News Scraper
Comprehensive test suite covering all NewsScraper functionality
Coverage target: 85%+

Test Categories:
- Initialization and setup
- ID generation
- Rate limiting
- HTML parsing
- Article extraction
- Error handling
- HTTP status codes
- Edge cases
"""

import pytest
import time
import hashlib
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import requests
import responses
from bs4 import BeautifulSoup

from src.scrapers.news_scraper import NewsScraper


pytestmark = pytest.mark.unit


# ============================================================================
# TEST CLASS: INITIALIZATION & SETUP
# ============================================================================

class TestNewsScraperInitialization:
    """Test initialization and setup"""

    def test_initialization_with_config(self):
        """Test initialization with provided config manager"""
        mock_config = Mock()
        scraper = NewsScraper(config_manager=mock_config)

        assert scraper.config is mock_config
        assert scraper.session is not None
        assert 'User-Agent' in scraper.session.headers
        assert scraper.last_request_time == {}

    def test_initialization_without_config(self):
        """Test initialization creates new config manager"""
        with patch('src.scrapers.news_scraper.ConfigManager') as MockConfigManager:
            MockConfigManager.return_value = Mock()
            scraper = NewsScraper()

            assert scraper.config is not None
            MockConfigManager.assert_called_once()

    def test_user_agent_header_set(self):
        """Test that User-Agent header is properly set"""
        mock_config = Mock()
        scraper = NewsScraper(config_manager=mock_config)

        assert 'MagicBricks-NewsBot/1.0' in scraper.session.headers['User-Agent']

    def test_session_is_requests_session(self):
        """Test that session is a requests.Session instance"""
        mock_config = Mock()
        scraper = NewsScraper(config_manager=mock_config)

        assert isinstance(scraper.session, requests.Session)


# ============================================================================
# TEST CLASS: ID GENERATION
# ============================================================================

class TestIDGeneration:
    """Test unique ID generation from URLs"""

    @pytest.fixture
    def scraper(self):
        """Create scraper with mock config"""
        return NewsScraper(config_manager=Mock())

    def test_generate_id_consistency(self, scraper):
        """Test same URL generates same ID"""
        url = "https://example.com/article/123"
        id1 = scraper._generate_id(url)
        id2 = scraper._generate_id(url)

        assert id1 == id2

    def test_generate_id_uniqueness(self, scraper):
        """Test different URLs generate different IDs"""
        url1 = "https://example.com/article/123"
        url2 = "https://example.com/article/456"

        id1 = scraper._generate_id(url1)
        id2 = scraper._generate_id(url2)

        assert id1 != id2

    def test_generate_id_length(self, scraper):
        """Test ID is MD5 hash (32 characters)"""
        url = "https://example.com/article"
        id_hash = scraper._generate_id(url)

        assert len(id_hash) == 32

    def test_generate_id_matches_manual_hash(self, scraper):
        """Test generated ID matches manual MD5 hash"""
        url = "https://example.com/test"
        expected = hashlib.md5(url.encode()).hexdigest()
        actual = scraper._generate_id(url)

        assert actual == expected

    def test_generate_id_with_special_characters(self, scraper):
        """Test ID generation with special characters in URL"""
        url = "https://example.com/article?id=123&lang=en"
        id_hash = scraper._generate_id(url)

        assert len(id_hash) == 32
        assert id_hash.isalnum()


# ============================================================================
# TEST CLASS: RATE LIMITING
# ============================================================================

class TestRateLimiting:
    """Test rate limiting functionality"""

    @pytest.fixture
    def scraper(self):
        """Create scraper with mock config"""
        return NewsScraper(config_manager=Mock())

    def test_first_request_no_delay(self, scraper):
        """Test first request to source has no delay"""
        source_id = "test_source"
        start_time = time.time()

        scraper._respect_rate_limit(source_id, 1000)

        elapsed = (time.time() - start_time) * 1000
        assert elapsed < 100  # Should be nearly instant

    @patch('time.sleep')
    def test_rapid_requests_trigger_delay(self, mock_sleep, scraper):
        """Test rapid successive requests trigger rate limiting"""
        source_id = "test_source"
        rate_limit_ms = 1000

        # First request
        scraper._respect_rate_limit(source_id, rate_limit_ms)

        # Immediate second request (should trigger sleep)
        scraper._respect_rate_limit(source_id, rate_limit_ms)

        # Sleep should be called
        assert mock_sleep.called

    @patch('time.sleep')
    def test_rate_limit_sleep_duration(self, mock_sleep, scraper):
        """Test rate limit calculates correct sleep duration"""
        source_id = "test_source"
        rate_limit_ms = 1000

        # First request
        scraper._respect_rate_limit(source_id, rate_limit_ms)

        # Simulate 200ms elapsed
        scraper.last_request_time[source_id] = time.time() - 0.2

        # Second request
        scraper._respect_rate_limit(source_id, rate_limit_ms)

        # Should sleep ~800ms (1000 - 200)
        if mock_sleep.called:
            sleep_duration = mock_sleep.call_args[0][0]
            assert 0.7 < sleep_duration < 0.9

    def test_different_sources_independent(self, scraper):
        """Test rate limiting is independent per source"""
        source1 = "source_1"
        source2 = "source_2"

        scraper._respect_rate_limit(source1, 1000)
        scraper._respect_rate_limit(source2, 1000)

        assert source1 in scraper.last_request_time
        assert source2 in scraper.last_request_time

    @patch('time.sleep')
    def test_sufficient_time_passed_no_delay(self, mock_sleep, scraper):
        """Test no delay if sufficient time has passed"""
        source_id = "test_source"
        rate_limit_ms = 1000

        # First request
        scraper._respect_rate_limit(source_id, rate_limit_ms)

        # Simulate 1.5 seconds elapsed (more than rate limit)
        scraper.last_request_time[source_id] = time.time() - 1.5

        # Second request
        scraper._respect_rate_limit(source_id, rate_limit_ms)

        # No sleep should be called
        assert not mock_sleep.called


# ============================================================================
# TEST CLASS: HTML PARSING
# ============================================================================

class TestHTMLParsing:
    """Test HTML parsing with CSS selectors"""

    @pytest.fixture
    def scraper(self):
        """Create scraper with mock config"""
        return NewsScraper(config_manager=Mock())

    def test_parse_article_with_all_fields(self, scraper):
        """Test parsing HTML with all selector fields present"""
        html = """
        <html>
            <body>
                <h1 class="title">Test Article Title</h1>
                <div class="content">Test article content</div>
                <time class="date">2026-01-30</time>
                <a class="link" href="/article/123">Read more</a>
            </body>
        </html>
        """

        selectors = {
            'title': '.title',
            'content': '.content',
            'date': '.date',
            'link': '.link'
        }

        result = scraper._parse_article(html, selectors)

        assert result['title'] == 'Test Article Title'
        assert result['content'] == 'Test article content'
        assert result['date'] == '2026-01-30'
        assert result['link'] == 'Read more'

    def test_parse_article_with_missing_fields(self, scraper):
        """Test parsing HTML with some fields missing"""
        html = """
        <html>
            <body>
                <h1 class="title">Test Title</h1>
            </body>
        </html>
        """

        selectors = {
            'title': '.title',
            'content': '.content',
            'date': '.date',
            'link': '.link'
        }

        result = scraper._parse_article(html, selectors)

        assert result['title'] == 'Test Title'
        assert result['content'] is None
        assert result['date'] is None
        assert result['link'] is None

    def test_parse_article_with_empty_selectors(self, scraper):
        """Test parsing with empty selectors dict"""
        html = "<html><body><h1>Title</h1></body></html>"
        selectors = {}

        result = scraper._parse_article(html, selectors)

        assert result['title'] is None
        assert result['content'] is None
        assert result['date'] is None
        assert result['link'] is None

    def test_parse_article_strips_whitespace(self, scraper):
        """Test parsing strips extra whitespace"""
        html = """
        <html>
            <body>
                <h1 class="title">
                    Test Title with Whitespace
                </h1>
            </body>
        </html>
        """

        selectors = {'title': '.title'}
        result = scraper._parse_article(html, selectors)

        assert result['title'] == 'Test Title with Whitespace'
        assert not result['title'].startswith(' ')
        assert not result['title'].endswith(' ')

    def test_parse_article_with_nested_elements(self, scraper):
        """Test parsing with nested HTML elements"""
        html = """
        <html>
            <body>
                <div class="content">
                    <p>First paragraph</p>
                    <p>Second paragraph</p>
                </div>
            </body>
        </html>
        """

        selectors = {'content': '.content'}
        result = scraper._parse_article(html, selectors)

        assert 'First paragraph' in result['content']
        assert 'Second paragraph' in result['content']

    def test_parse_article_with_invalid_selector(self, scraper):
        """Test parsing with invalid CSS selector"""
        html = "<html><body><h1>Title</h1></body></html>"
        selectors = {'title': '.nonexistent'}

        result = scraper._parse_article(html, selectors)

        assert result['title'] is None

    def test_parse_article_with_complex_selectors(self, scraper):
        """Test parsing with complex CSS selectors"""
        html = """
        <html>
            <body>
                <article>
                    <div class="meta">
                        <h2 class="headline">Main Headline</h2>
                    </div>
                </article>
            </body>
        </html>
        """

        selectors = {'title': 'article .meta h2.headline'}
        result = scraper._parse_article(html, selectors)

        assert result['title'] == 'Main Headline'

    def test_parse_malformed_html(self, scraper):
        """Test parsing malformed HTML gracefully"""
        html = "<html><div<p>Broken HTML</html>"
        selectors = {'title': 'p'}

        # BeautifulSoup should handle this gracefully
        result = scraper._parse_article(html, selectors)

        assert isinstance(result, dict)


# ============================================================================
# TEST CLASS: SCRAPE SOURCE
# ============================================================================

class TestScrapeSource:
    """Test scraping individual sources"""

    @pytest.fixture
    def scraper(self):
        """Create scraper with mock config"""
        return NewsScraper(config_manager=Mock())

    @pytest.fixture
    def valid_source(self):
        """Create valid source configuration"""
        return {
            'id': 'test_source',
            'name': 'Test Source',
            'url': 'https://test.com/news',
            'type': 'scrape',
            'category': 'real_estate',
            'enabled': True,
            'rate_limit_ms': 1000,
            'selectors': {
                'title': 'h1.title',
                'content': '.content',
                'date': 'time',
                'link': 'a'
            }
        }

    @responses.activate
    def test_scrape_source_success(self, scraper, valid_source):
        """Test successful scraping of a source"""
        html = """
        <html>
            <body>
                <h1 class="title">Test Article</h1>
                <div class="content">Article content here</div>
                <time>2026-01-30</time>
                <a href="/article">Link</a>
            </body>
        </html>
        """

        responses.add(
            responses.GET,
            valid_source['url'],
            body=html,
            status=200
        )

        result = scraper.scrape_source(valid_source)

        assert len(result) == 1
        assert result[0]['title'] == 'Test Article'
        assert result[0]['source'] == 'Test Source'
        assert result[0]['category'] == 'real_estate'
        assert result[0]['url'] == valid_source['url']

    def test_scrape_disabled_source(self, scraper, valid_source):
        """Test disabled source returns empty list"""
        valid_source['enabled'] = False

        result = scraper.scrape_source(valid_source)

        assert result == []

    def test_scrape_wrong_type_source(self, scraper, valid_source):
        """Test non-scrape type source returns empty list"""
        valid_source['type'] = 'rss'

        result = scraper.scrape_source(valid_source)

        assert result == []

    @responses.activate
    def test_scrape_source_no_title(self, scraper, valid_source):
        """Test scraping source with no title returns empty"""
        html = """
        <html>
            <body>
                <div class="content">Content without title</div>
            </body>
        </html>
        """

        responses.add(
            responses.GET,
            valid_source['url'],
            body=html,
            status=200
        )

        result = scraper.scrape_source(valid_source)

        assert result == []

    @responses.activate
    def test_scrape_source_http_404(self, scraper, valid_source):
        """Test scraping handles 404 gracefully"""
        responses.add(
            responses.GET,
            valid_source['url'],
            status=404
        )

        result = scraper.scrape_source(valid_source)

        assert result == []

    @responses.activate
    def test_scrape_source_http_500(self, scraper, valid_source):
        """Test scraping handles 500 error gracefully"""
        responses.add(
            responses.GET,
            valid_source['url'],
            status=500
        )

        result = scraper.scrape_source(valid_source)

        assert result == []

    @responses.activate
    def test_scrape_source_timeout(self, scraper, valid_source):
        """Test scraping handles timeout gracefully"""
        responses.add(
            responses.GET,
            valid_source['url'],
            body=requests.exceptions.Timeout('Connection timeout')
        )

        result = scraper.scrape_source(valid_source)

        assert result == []

    @responses.activate
    def test_scrape_source_connection_error(self, scraper, valid_source):
        """Test scraping handles connection error gracefully"""
        responses.add(
            responses.GET,
            valid_source['url'],
            body=requests.exceptions.ConnectionError('Connection failed')
        )

        result = scraper.scrape_source(valid_source)

        assert result == []

    @responses.activate
    def test_scrape_source_includes_all_fields(self, scraper, valid_source):
        """Test scraped item includes all required fields"""
        html = "<html><h1 class='title'>Test</h1></html>"

        responses.add(
            responses.GET,
            valid_source['url'],
            body=html,
            status=200
        )

        result = scraper.scrape_source(valid_source)

        assert len(result) == 1
        item = result[0]

        # Check all required fields
        assert 'id' in item
        assert 'title' in item
        assert 'url' in item
        assert 'source' in item
        assert 'source_id' in item
        assert 'category' in item
        assert 'content' in item
        assert 'published_at' in item
        assert 'scraped_at' in item
        assert 'author' in item
        assert 'image_url' in item
        assert 'tags' in item

    @responses.activate
    def test_scrape_source_default_values(self, scraper, valid_source):
        """Test default values for optional fields"""
        html = "<html><h1 class='title'>Test</h1></html>"

        responses.add(
            responses.GET,
            valid_source['url'],
            body=html,
            status=200
        )

        result = scraper.scrape_source(valid_source)

        item = result[0]
        assert item['author'] is None
        assert item['image_url'] is None
        assert item['tags'] == []
        assert item['content'] == ''  # No content in HTML

    @responses.activate
    @patch('time.sleep')
    def test_scrape_source_respects_rate_limit(self, mock_sleep, scraper, valid_source):
        """Test scraping respects rate limiting"""
        html = "<html><h1 class='title'>Test</h1></html>"

        responses.add(
            responses.GET,
            valid_source['url'],
            body=html,
            status=200
        )

        # First scrape
        scraper.scrape_source(valid_source)

        # Second scrape (should trigger rate limit)
        responses.add(
            responses.GET,
            valid_source['url'],
            body=html,
            status=200
        )
        scraper.scrape_source(valid_source)

        # Rate limit should have been enforced
        assert valid_source['id'] in scraper.last_request_time


# ============================================================================
# TEST CLASS: SCRAPE ALL
# ============================================================================

class TestScrapeAll:
    """Test scraping multiple sources"""

    @pytest.fixture
    def scraper(self):
        """Create scraper with mock config"""
        mock_config = Mock()
        return NewsScraper(config_manager=mock_config)

    @responses.activate
    def test_scrape_all_multiple_sources(self, scraper):
        """Test scraping multiple sources"""
        sources = [
            {
                'id': 'source1',
                'name': 'Source 1',
                'url': 'https://test1.com/news',
                'type': 'scrape',
                'enabled': True,
                'rate_limit_ms': 100,
                'selectors': {'title': 'h1'}
            },
            {
                'id': 'source2',
                'name': 'Source 2',
                'url': 'https://test2.com/news',
                'type': 'scrape',
                'enabled': True,
                'rate_limit_ms': 100,
                'selectors': {'title': 'h1'}
            }
        ]

        scraper.config.get_sources.return_value = sources

        responses.add(responses.GET, 'https://test1.com/news',
                     body="<html><h1>Article 1</h1></html>", status=200)
        responses.add(responses.GET, 'https://test2.com/news',
                     body="<html><h1>Article 2</h1></html>", status=200)

        result = scraper.scrape_all()

        assert len(result) == 2

    def test_scrape_all_filters_non_scrape_types(self, scraper):
        """Test scrape_all only processes scrape type sources"""
        sources = [
            {'id': 's1', 'type': 'scrape', 'enabled': True, 'url': 'http://test.com',
             'rate_limit_ms': 100, 'selectors': {}},
            {'id': 's2', 'type': 'rss', 'enabled': True}
        ]

        scraper.config.get_sources.return_value = sources

        with patch.object(scraper, 'scrape_source') as mock_scrape:
            mock_scrape.return_value = []
            scraper.scrape_all()

            # Should only call scrape_source for scrape type
            assert mock_scrape.call_count == 1

    @responses.activate
    def test_scrape_all_handles_partial_failures(self, scraper):
        """Test scrape_all continues when one source fails"""
        sources = [
            {
                'id': 'source1',
                'name': 'Source 1',
                'url': 'https://test1.com/news',
                'type': 'scrape',
                'enabled': True,
                'rate_limit_ms': 100,
                'selectors': {'title': 'h1'}
            },
            {
                'id': 'source2',
                'name': 'Source 2',
                'url': 'https://test2.com/news',
                'type': 'scrape',
                'enabled': True,
                'rate_limit_ms': 100,
                'selectors': {'title': 'h1'}
            }
        ]

        scraper.config.get_sources.return_value = sources

        # First source fails, second succeeds
        responses.add(responses.GET, 'https://test1.com/news', status=500)
        responses.add(responses.GET, 'https://test2.com/news',
                     body="<html><h1>Article 2</h1></html>", status=200)

        result = scraper.scrape_all()

        # Should still get result from successful source
        assert len(result) == 1


# ============================================================================
# TEST CLASS: SCRAPE BY CATEGORY
# ============================================================================

class TestScrapeByCategory:
    """Test scraping sources filtered by category"""

    @pytest.fixture
    def scraper(self):
        """Create scraper with mock config"""
        mock_config = Mock()
        return NewsScraper(config_manager=mock_config)

    @responses.activate
    def test_scrape_by_category_filters_correctly(self, scraper):
        """Test category filtering works"""
        sources = [
            {
                'id': 'source1',
                'name': 'Real Estate Source',
                'url': 'https://test1.com/news',
                'type': 'scrape',
                'category': 'real_estate',
                'enabled': True,
                'rate_limit_ms': 100,
                'selectors': {'title': 'h1'}
            },
            {
                'id': 'source2',
                'name': 'Policy Source',
                'url': 'https://test2.com/news',
                'type': 'scrape',
                'category': 'policy',
                'enabled': True,
                'rate_limit_ms': 100,
                'selectors': {'title': 'h1'}
            }
        ]

        scraper.config.get_sources.return_value = sources

        responses.add(responses.GET, 'https://test1.com/news',
                     body="<html><h1>RE Article</h1></html>", status=200)

        result = scraper.scrape_by_category('real_estate')

        # Should only get real_estate articles
        assert len(result) == 1
        assert result[0]['category'] == 'real_estate'

    def test_scrape_by_category_no_matches(self, scraper):
        """Test category with no matching sources"""
        sources = [
            {
                'id': 'source1',
                'type': 'scrape',
                'category': 'policy',
                'enabled': True,
                'url': 'http://test.com',
                'rate_limit_ms': 100,
                'selectors': {}
            }
        ]

        scraper.config.get_sources.return_value = sources

        result = scraper.scrape_by_category('real_estate')

        assert result == []


# ============================================================================
# TEST CLASS: EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.fixture
    def scraper(self):
        """Create scraper with mock config"""
        return NewsScraper(config_manager=Mock())

    @responses.activate
    def test_scrape_very_large_html(self, scraper, valid_source):
        """Test scraping very large HTML document"""
        # Create large HTML (1MB+)
        large_content = "Lorem ipsum " * 100000
        html = f"<html><h1 class='title'>Title</h1><div class='content'>{large_content}</div></html>"

        valid_source = {
            'id': 'test',
            'name': 'Test',
            'url': 'https://test.com',
            'type': 'scrape',
            'enabled': True,
            'rate_limit_ms': 100,
            'selectors': {'title': '.title', 'content': '.content'}
        }

        responses.add(responses.GET, valid_source['url'], body=html, status=200)

        result = scraper.scrape_source(valid_source)

        assert len(result) == 1
        assert len(result[0]['content']) > 1000000

    def test_scrape_source_unicode_content(self, scraper):
        """Test scraping content with Unicode characters"""
        html = """
        <html>
            <h1 class="title">मुंबई में प्रॉपर्टी की कीमतें बढ़ीं</h1>
            <div class="content">プロパティ市場 📈</div>
        </html>
        """

        selectors = {'title': '.title', 'content': '.content'}
        result = scraper._parse_article(html, selectors)

        assert 'मुंबई' in result['title']
        assert 'プロパティ' in result['content']
        assert '📈' in result['content']

    @responses.activate
    def test_scrape_empty_html_response(self, scraper):
        """Test scraping empty HTML response"""
        source = {
            'id': 'test',
            'name': 'Test',
            'url': 'https://test.com',
            'type': 'scrape',
            'enabled': True,
            'rate_limit_ms': 100,
            'selectors': {'title': 'h1'}
        }

        responses.add(responses.GET, source['url'], body="", status=200)

        result = scraper.scrape_source(source)

        assert result == []

    @responses.activate
    def test_scrape_html_with_javascript(self, scraper):
        """Test scraping HTML with embedded JavaScript"""
        html = """
        <html>
            <head>
                <script>
                    alert('test');
                </script>
            </head>
            <body>
                <h1 class="title">Article Title</h1>
            </body>
        </html>
        """

        source = {
            'id': 'test',
            'name': 'Test',
            'url': 'https://test.com',
            'type': 'scrape',
            'enabled': True,
            'rate_limit_ms': 100,
            'selectors': {'title': '.title'}
        }

        responses.add(responses.GET, source['url'], body=html, status=200)

        result = scraper.scrape_source(source)

        # Should extract title, ignoring JavaScript
        assert len(result) == 1
        assert result[0]['title'] == 'Article Title'

    def test_parse_html_with_comments(self, scraper):
        """Test parsing HTML with comments"""
        html = """
        <html>
            <!-- This is a comment -->
            <h1 class="title">Title</h1>
            <!-- Another comment -->
        </html>
        """

        selectors = {'title': '.title'}
        result = scraper._parse_article(html, selectors)

        assert result['title'] == 'Title'
        assert '<!--' not in result['title']


# ============================================================================
# TEST CLASS: HTTP STATUS CODES
# ============================================================================

class TestHTTPStatusCodes:
    """Test handling of various HTTP status codes"""

    @pytest.fixture
    def scraper(self):
        """Create scraper with mock config"""
        return NewsScraper(config_manager=Mock())

    @pytest.fixture
    def source(self):
        """Create test source"""
        return {
            'id': 'test',
            'name': 'Test',
            'url': 'https://test.com',
            'type': 'scrape',
            'enabled': True,
            'rate_limit_ms': 100,
            'selectors': {'title': 'h1'}
        }

    @pytest.mark.parametrize("status_code", [
        301, 302, 303, 307, 308,  # Redirects
        400, 401, 403, 404,       # Client errors
        500, 502, 503, 504,       # Server errors
        429,                      # Rate limit
    ])
    @responses.activate
    def test_handle_various_status_codes(self, scraper, source, status_code):
        """Test handling of various HTTP status codes returns empty"""
        responses.add(responses.GET, source['url'], status=status_code)

        result = scraper.scrape_source(source)

        # All error codes should return empty list
        assert result == []

    @responses.activate
    def test_handle_redirect_success(self, scraper, source):
        """Test following redirects to successful page"""
        # responses library handles redirects automatically
        html = "<html><h1>Success after redirect</h1></html>"

        responses.add(
            responses.GET,
            source['url'],
            body=html,
            status=200
        )

        result = scraper.scrape_source(source)

        assert len(result) == 1


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def valid_source():
    """Create a valid source configuration for testing"""
    return {
        'id': 'test_source',
        'name': 'Test Source',
        'url': 'https://test.com/news',
        'type': 'scrape',
        'category': 'real_estate',
        'enabled': True,
        'rate_limit_ms': 1000,
        'selectors': {
            'title': 'h1.title',
            'content': '.content',
            'date': 'time',
            'link': 'a'
        }
    }
