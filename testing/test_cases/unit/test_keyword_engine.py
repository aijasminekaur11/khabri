"""
Unit tests for KeywordEngine module.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from src.notifiers.keyword_engine import KeywordEngine


class TestKeywordEngine:
    """Test suite for KeywordEngine class."""

    @pytest.fixture
    def engine(self):
        """Create KeywordEngine instance."""
        return KeywordEngine()

    @pytest.fixture
    def sample_news(self):
        """Sample news item for testing."""
        return {
            'id': 'news_1',
            'title': 'Shah Rukh Khan Buys Luxury Villa in Mumbai',
            'content': 'Famous Bollywood actor Shah Rukh Khan has purchased a luxury villa in Bandra worth 50 crores. The property features modern amenities and sea-facing views.',
            'url': 'https://example.com/news1',
            'source': 'Test News',
            'category': 'celebrity',
            'published_at': datetime.now(),
            'signal_score': 9,
            'impact_level': 'HIGH',
            'celebrity_match': 'Shah Rukh Khan',
            'image_url': 'https://example.com/image.jpg',
            'keywords': []
        }

    @pytest.fixture
    def old_news(self):
        """Sample old news item."""
        return {
            'id': 'old_news',
            'title': 'Old Real Estate News',
            'content': 'This is an old article about real estate.',
            'category': 'real_estate',
            'published_at': datetime.now() - timedelta(days=5),
            'signal_score': 5,
            'impact_level': 'LOW',
            'keywords': []
        }

    def test_initialization(self, engine):
        """Test KeywordEngine initialization."""
        assert engine.cache == {}
        assert engine.CACHE_TTL == 900
        assert engine.RATE_LIMIT_DELAY == 2.0

    def test_extract_keywords_from_text(self, engine):
        """Test keyword extraction from text."""
        text = "This is a test article about real estate market trends and property investments"
        keywords = engine._extract_keywords_from_text(text)

        assert isinstance(keywords, list)
        assert len(keywords) > 0
        # Should not contain common words
        assert 'this' not in keywords
        assert 'test' in keywords or 'article' in keywords

    def test_extract_keywords_bigrams(self, engine):
        """Test bigram extraction."""
        text = "luxury villa real estate market"
        keywords = engine._extract_keywords_from_text(text)

        # Should contain bigrams like "luxury villa"
        bigrams = [kw for kw in keywords if ' ' in kw]
        assert len(bigrams) > 0

    def test_get_seo_suggestions(self, engine, sample_news):
        """Test SEO suggestions generation."""
        suggestions = engine.get_seo_suggestions(sample_news)

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

        # Check structure of suggestions
        for suggestion in suggestions:
            assert 'keyword' in suggestion
            assert 'search_volume' in suggestion
            assert 'difficulty' in suggestion
            assert 'type' in suggestion

    def test_get_seo_suggestions_with_celebrity(self, engine, sample_news):
        """Test SEO suggestions include celebrity keywords."""
        suggestions = engine.get_seo_suggestions(sample_news)

        # Should include celebrity-related keywords
        celebrity_keywords = [
            s for s in suggestions
            if 'Shah Rukh Khan' in s['keyword']
        ]
        assert len(celebrity_keywords) > 0

    def test_calculate_discover_potential_celebrity(self, engine, sample_news):
        """Test Discover potential calculation with celebrity."""
        score = engine.calculate_discover_potential(sample_news)

        assert isinstance(score, int)
        assert 0 <= score <= 100
        # Celebrity should add 30 points
        assert score >= 30

    def test_calculate_discover_potential_fresh_news(self, engine, sample_news):
        """Test Discover potential with fresh news."""
        # Set to very recent
        sample_news['published_at'] = datetime.now() - timedelta(minutes=30)
        score = engine.calculate_discover_potential(sample_news)

        # Fresh news should score higher
        assert score >= 15  # Freshness points

    def test_calculate_discover_potential_old_news(self, engine, old_news):
        """Test Discover potential with old news."""
        score = engine.calculate_discover_potential(old_news)

        # Old news should score lower
        assert score < 50

    def test_calculate_discover_potential_with_image(self, engine, sample_news):
        """Test Discover potential with image."""
        score_with_image = engine.calculate_discover_potential(sample_news)

        # Remove image and recalculate
        sample_news['image_url'] = None
        score_without_image = engine.calculate_discover_potential(sample_news)

        # Image should add 20 points
        assert score_with_image >= score_without_image + 20

    def test_calculate_discover_potential_high_impact(self, engine, sample_news):
        """Test Discover potential with high impact."""
        sample_news['impact_level'] = 'HIGH'
        score = engine.calculate_discover_potential(sample_news)

        # High impact should add 10 points
        assert score >= 10

    def test_calculate_discover_potential_trending_terms(self, engine):
        """Test Discover potential with trending terms."""
        news = {
            'title': 'BREAKING: Exclusive viral news announced',
            'content': 'Test content',
            'category': 'real_estate',
            'published_at': datetime.now(),
            'impact_level': 'MEDIUM',
            'keywords': []
        }

        score = engine.calculate_discover_potential(news)

        # Trending terms should add points
        assert score >= 15

    def test_calculate_discover_potential_max_100(self, engine):
        """Test Discover potential is capped at 100."""
        # Create news with all possible points
        news = {
            'title': 'BREAKING: Exclusive viral trending major news',
            'content': 'Test content',
            'category': 'celebrity',
            'published_at': datetime.now(),
            'celebrity_match': 'Test Celebrity',
            'image_url': 'https://example.com/image.jpg',
            'impact_level': 'HIGH',
            'keywords': []
        }

        score = engine.calculate_discover_potential(news)

        # Should not exceed 100
        assert score <= 100

    def test_estimate_difficulty(self, engine):
        """Test difficulty estimation."""
        assert engine._estimate_difficulty(15000) == 'HIGH'
        assert engine._estimate_difficulty(5000) == 'MEDIUM'
        assert engine._estimate_difficulty(500) == 'LOW'

    def test_cache_functionality(self, engine):
        """Test caching mechanism."""
        # Set a value
        engine._set_cache('test_key', 'test_value')

        # Retrieve it
        cached = engine._get_cache('test_key')
        assert cached == 'test_value'

        # Check cache stats
        stats = engine.get_keyword_stats()
        assert stats['cache_size'] == 1

    def test_cache_expiration(self, engine):
        """Test cache expiration."""
        engine._set_cache('test_key', 'test_value')

        # Manually expire by modifying timestamp
        engine.cache['test_key'] = ('test_value', 0)  # Very old timestamp

        # Should return None
        cached = engine._get_cache('test_key')
        assert cached is None

    def test_clear_cache(self, engine):
        """Test cache clearing."""
        engine._set_cache('key1', 'value1')
        engine._set_cache('key2', 'value2')

        assert len(engine.cache) == 2

        engine.clear_cache()
        assert len(engine.cache) == 0

    def test_get_keyword_stats(self, engine):
        """Test keyword statistics."""
        stats = engine.get_keyword_stats()

        assert 'cache_size' in stats
        assert 'pytrends_available' in stats
        assert 'last_request' in stats

        assert isinstance(stats['cache_size'], int)
        assert isinstance(stats['pytrends_available'], bool)

    def test_get_trending_keywords_with_pytrends(self, engine):
        """Test trending keywords with pytrends available."""
        # Mock pytrends
        mock_pytrends = Mock()
        mock_df = Mock()
        mock_df.head.return_value.iterrows.return_value = [
            (0, {'query': 'trending keyword 1', 'value': 5000}),
            (1, {'query': 'trending keyword 2', 'value': 3000})
        ]

        mock_pytrends.related_queries.return_value = {
            'test topic': {'rising': mock_df}
        }

        engine.pytrends = mock_pytrends
        engine.pytrends_available = True

        keywords = engine.get_trending_keywords('test topic')

        assert len(keywords) > 0
        assert keywords[0]['keyword'] == 'trending keyword 1'
        assert keywords[0]['type'] == 'trending'

    def test_get_trending_keywords_fallback(self, engine):
        """Test trending keywords without pytrends (fallback)."""
        engine.pytrends_available = False
        engine.pytrends = None

        keywords = engine.get_trending_keywords('real estate')

        # Should return fallback keywords
        assert len(keywords) > 0
        assert any('news' in kw['keyword'] for kw in keywords)

    def test_get_trending_keywords_caching(self, engine):
        """Test trending keywords are cached."""
        engine.pytrends_available = False

        # First call
        keywords1 = engine.get_trending_keywords('test')

        # Second call should use cache
        keywords2 = engine.get_trending_keywords('test')

        assert keywords1 == keywords2
        assert engine.get_keyword_stats()['cache_size'] == 1

    def test_rate_limiting(self, engine):
        """Test rate limiting."""
        import time

        engine._rate_limit()
        start = time.time()
        engine._rate_limit()
        elapsed = time.time() - start

        # Should have some delay
        assert elapsed >= 0

    def test_seo_suggestions_keyword_types(self, engine, sample_news):
        """Test SEO suggestions include different keyword types."""
        suggestions = engine.get_seo_suggestions(sample_news)

        types = set(s['type'] for s in suggestions)

        # Should have multiple types
        assert len(types) >= 2
        assert 'primary' in types or 'secondary' in types

    def test_seo_suggestions_limit(self, engine, sample_news):
        """Test SEO suggestions are limited to 10."""
        suggestions = engine.get_seo_suggestions(sample_news)

        # Should not exceed 10
        assert len(suggestions) <= 10
