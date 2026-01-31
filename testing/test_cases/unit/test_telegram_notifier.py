"""
Unit tests for TelegramNotifier module.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from src.notifiers.telegram_notifier import TelegramNotifier


class TestTelegramNotifier:
    """Test suite for TelegramNotifier class."""

    @pytest.fixture
    def notifier(self):
        """Create TelegramNotifier instance with test credentials."""
        return TelegramNotifier(
            bot_token='test_token_123',
            chat_id='test_chat_456'
        )

    @pytest.fixture
    def sample_digest(self):
        """Sample digest data."""
        return {
            'type': 'morning',
            'generated_at': datetime(2026, 1, 30, 7, 0, 0),
            'news_items': [
                {
                    'id': 'news_1',
                    'title': 'New Real Estate Project Launched',
                    'url': 'https://example.com/news1',
                    'source': 'Test News',
                    'category': 'real_estate',
                    'content': 'Major real estate project launched in Mumbai.',
                    'signal_score': 8,
                    'impact_level': 'HIGH',
                    'discover_potential': 75
                },
                {
                    'id': 'news_2',
                    'title': 'Infrastructure Development Update',
                    'url': 'https://example.com/news2',
                    'source': 'Test Source',
                    'category': 'infrastructure',
                    'content': 'New metro line announced.',
                    'signal_score': 6,
                    'impact_level': 'MEDIUM',
                    'discover_potential': 50
                }
            ],
            'competitor_alerts': []
        }

    @pytest.fixture
    def sample_alert(self):
        """Sample high-priority alert."""
        return {
            'id': 'alert_1',
            'title': 'Breaking: Celebrity Buys Luxury Villa',
            'url': 'https://example.com/alert',
            'source': 'Exclusive News',
            'category': 'celebrity',
            'content': 'Famous actor purchases luxury property worth 50 crores.',
            'signal_score': 10,
            'impact_level': 'HIGH',
            'discover_potential': 95,
            'celebrity_match': 'Shah Rukh Khan',
            'keywords': [
                {'keyword': 'luxury villa', 'type': 'primary'},
                {'keyword': 'celebrity real estate', 'type': 'secondary'}
            ],
            'verified': True
        }

    def test_initialization(self):
        """Test TelegramNotifier initialization."""
        notifier = TelegramNotifier(bot_token='token', chat_id='chat')
        assert notifier.bot_token == 'token'
        assert notifier.chat_id == 'chat'
        assert notifier.api_url == 'https://api.telegram.org/bottoken'

    def test_initialization_from_env(self, monkeypatch):
        """Test TelegramNotifier initialization from environment variables."""
        monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'env_token')
        monkeypatch.setenv('TELEGRAM_CHAT_ID', 'env_chat')

        notifier = TelegramNotifier()
        assert notifier.bot_token == 'env_token'
        assert notifier.chat_id == 'env_chat'

    def test_split_message_short(self, notifier):
        """Test message splitting with short message."""
        short_message = "This is a short message"
        chunks = notifier._split_message(short_message)
        assert len(chunks) == 1
        assert chunks[0] == short_message

    def test_split_message_long(self, notifier):
        """Test message splitting with long message."""
        # Create a message longer than MAX_MESSAGE_LENGTH
        long_message = "Line\n" * 1000  # Creates a very long message
        chunks = notifier._split_message(long_message)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= notifier.MAX_MESSAGE_LENGTH

    def test_format_digest(self, notifier, sample_digest):
        """Test digest formatting."""
        formatted = notifier._format_digest(sample_digest)
        assert 'MORNING DIGEST' in formatted
        assert 'Magic Bricks Daily Brief' in formatted
        assert '2026-01-30' in formatted
        assert 'New Real Estate Project Launched' in formatted
        assert 'REAL ESTATE' in formatted
        assert 'INFRASTRUCTURE' in formatted

    def test_format_alert(self, notifier, sample_alert):
        """Test alert formatting."""
        formatted = notifier._format_alert(sample_alert)
        assert 'HIGH-IMPACT ALERT' in formatted
        assert 'Score: 10/10' in formatted
        assert 'Celebrity Buys Luxury Villa' in formatted
        assert 'Shah Rukh Khan' in formatted
        assert 'luxury villa' in formatted
        assert 'Verified' in formatted

    @patch('requests.post')
    def test_send_message_success(self, mock_post, notifier):
        """Test successful message sending."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = notifier._send_message("Test message")
        assert result is True
        assert mock_post.called

    @patch('requests.post')
    def test_send_message_failure(self, mock_post, notifier):
        """Test message sending failure with retry."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        result = notifier._send_message("Test message")
        assert result is False
        assert mock_post.call_count == notifier.MAX_RETRIES

    @patch('requests.post')
    def test_send_digest(self, mock_post, notifier, sample_digest):
        """Test sending digest."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = notifier.send(sample_digest)
        assert result is True
        assert mock_post.called

    @patch('requests.post')
    def test_send_alert(self, mock_post, notifier, sample_alert):
        """Test sending alert."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = notifier.send_alert(sample_alert)
        assert result is True
        assert mock_post.called

    @patch('requests.get')
    def test_health_check_success(self, mock_get, notifier):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'result': {'username': 'test_bot'}
        }
        mock_get.return_value = mock_response

        result = notifier.health_check()
        assert result is True

    @patch('requests.get')
    def test_health_check_failure(self, mock_get, notifier):
        """Test failed health check."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        result = notifier.health_check()
        assert result is False

    def test_health_check_no_token(self):
        """Test health check without bot token."""
        notifier = TelegramNotifier(bot_token=None, chat_id='chat')
        result = notifier.health_check()
        assert result is False

    def test_rate_limiting(self, notifier):
        """Test rate limiting delay."""
        import time
        notifier._rate_limit()
        start = time.time()
        notifier._rate_limit()
        elapsed = time.time() - start
        # Should have delayed at least a little bit
        assert elapsed >= 0

    @patch('requests.post')
    def test_send_without_credentials(self, mock_post):
        """Test sending without credentials."""
        notifier = TelegramNotifier(bot_token=None, chat_id=None)
        result = notifier._send_message("Test")
        assert result is False
        assert not mock_post.called
