"""
Unit tests for EmailNotifier module.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from src.notifiers.email_notifier import EmailNotifier


class TestEmailNotifier:
    """Test suite for EmailNotifier class."""

    @pytest.fixture
    def notifier(self):
        """Create EmailNotifier instance with test credentials."""
        return EmailNotifier(
            smtp_server='smtp.gmail.com',
            smtp_port=587,
            username='test@gmail.com',
            password='test_password',
            recipient='recipient@gmail.com'
        )

    @pytest.fixture
    def sample_digest(self):
        """Sample digest data."""
        return {
            'type': 'evening',
            'generated_at': datetime(2026, 1, 30, 18, 0, 0),
            'news_items': [
                {
                    'id': 'news_1',
                    'title': 'Real Estate Market Analysis',
                    'url': 'https://example.com/news1',
                    'source': 'Market News',
                    'category': 'real_estate',
                    'content': 'Detailed analysis of the real estate market trends.',
                    'signal_score': 7,
                    'impact_level': 'MEDIUM',
                    'discover_potential': 60,
                    'keywords': [
                        {'keyword': 'real estate trends', 'type': 'primary'}
                    ]
                }
            ],
            'competitor_alerts': [
                {
                    'competitor': 'Competitor News',
                    'article_title': 'Breaking Real Estate Story',
                    'article_url': 'https://competitor.com/article',
                    'published_at': datetime(2026, 1, 30, 17, 0, 0),
                    'gaps': ['Missing local angle', 'No expert quotes']
                }
            ]
        }

    @pytest.fixture
    def sample_alert(self):
        """Sample high-priority alert."""
        return {
            'id': 'alert_1',
            'title': 'Major Infrastructure Project Announced',
            'url': 'https://example.com/alert',
            'source': 'Government News',
            'category': 'infrastructure',
            'content': 'Government announces 10,000 crore infrastructure project.',
            'signal_score': 9,
            'impact_level': 'HIGH',
            'discover_potential': 85,
            'keywords': [
                {'keyword': 'infrastructure project', 'type': 'primary'},
                {'keyword': 'government investment', 'type': 'secondary'}
            ],
            'verified': True,
            'image_url': 'https://example.com/image.jpg'
        }

    def test_initialization(self):
        """Test EmailNotifier initialization."""
        notifier = EmailNotifier(
            smtp_server='smtp.test.com',
            smtp_port=587,
            username='user@test.com',
            password='pass',
            recipient='rcpt@test.com'
        )
        assert notifier.smtp_server == 'smtp.test.com'
        assert notifier.smtp_port == 587
        assert notifier.username == 'user@test.com'
        assert notifier.recipient == 'rcpt@test.com'

    def test_initialization_from_env(self, monkeypatch):
        """Test EmailNotifier initialization from environment variables."""
        monkeypatch.setenv('GMAIL_ADDRESS', 'env@gmail.com')
        monkeypatch.setenv('GMAIL_APP_PASSWORD', 'env_pass')
        monkeypatch.setenv('RECIPIENT_EMAIL', 'env_rcpt@gmail.com')

        notifier = EmailNotifier()
        assert notifier.username == 'env@gmail.com'
        assert notifier.password == 'env_pass'
        assert notifier.recipient == 'env_rcpt@gmail.com'

    def test_format_digest_html(self, notifier, sample_digest):
        """Test HTML digest formatting."""
        html = notifier._format_digest_html(sample_digest)
        assert 'EVENING DIGEST' in html
        assert 'Magic Bricks News Intelligence' in html
        assert 'Real Estate Market Analysis' in html
        assert 'Competitor News' in html
        assert 'Breaking Real Estate Story' in html
        assert 'real estate trends' in html

    def test_format_alert_html(self, notifier, sample_alert):
        """Test HTML alert formatting."""
        html = notifier._format_alert_html(sample_alert)
        assert 'HIGH-IMPACT ALERT' in html
        assert 'Score: 9/10' in html
        assert 'Major Infrastructure Project Announced' in html
        assert 'infrastructure project' in html
        assert 'Verified' in html

    @patch('smtplib.SMTP')
    def test_get_connection_success(self, mock_smtp_class, notifier):
        """Test successful SMTP connection."""
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        connection = notifier._get_connection()
        assert connection is not None
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with('test@gmail.com', 'test_password')

    @patch('smtplib.SMTP')
    def test_get_connection_failure(self, mock_smtp_class, notifier):
        """Test failed SMTP connection."""
        mock_smtp_class.side_effect = Exception("Connection failed")

        connection = notifier._get_connection()
        assert connection is None

    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp_class, notifier):
        """Test successful email sending."""
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        result = notifier._send_email(
            subject='Test Subject',
            html_body='<html><body>Test</body></html>',
            text_body='Test'
        )
        assert result is True
        mock_smtp.send_message.assert_called_once()

    @patch('smtplib.SMTP')
    def test_send_email_with_attachments(self, mock_smtp_class, notifier, tmp_path):
        """Test email sending with attachments."""
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        # Create a temporary file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        result = notifier._send_email(
            subject='Test',
            html_body='<html>Test</html>',
            attachments=[str(test_file)]
        )
        assert result is True

    @patch('smtplib.SMTP')
    def test_send_email_failure_with_retry(self, mock_smtp_class, notifier):
        """Test email sending failure with retry."""
        mock_smtp_class.side_effect = Exception("SMTP Error")

        result = notifier._send_email(
            subject='Test',
            html_body='<html>Test</html>'
        )
        assert result is False
        assert mock_smtp_class.call_count == notifier.MAX_RETRIES

    @patch('smtplib.SMTP')
    def test_send_digest(self, mock_smtp_class, notifier, sample_digest):
        """Test sending digest."""
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        result = notifier.send(sample_digest)
        assert result is True
        mock_smtp.send_message.assert_called_once()

    @patch('smtplib.SMTP')
    def test_send_alert(self, mock_smtp_class, notifier, sample_alert):
        """Test sending alert."""
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        result = notifier.send_alert(sample_alert)
        assert result is True
        mock_smtp.send_message.assert_called_once()

    @patch('smtplib.SMTP')
    def test_health_check_success(self, mock_smtp_class, notifier):
        """Test successful health check."""
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        result = notifier.health_check()
        assert result is True

    @patch('smtplib.SMTP')
    def test_health_check_failure(self, mock_smtp_class, notifier):
        """Test failed health check."""
        mock_smtp_class.side_effect = Exception("Connection failed")

        result = notifier.health_check()
        assert result is False

    def test_health_check_no_credentials(self):
        """Test health check without credentials."""
        notifier = EmailNotifier(
            username=None,
            password=None,
            recipient='test@example.com'
        )
        result = notifier.health_check()
        assert result is False

    @patch('smtplib.SMTP')
    def test_send_without_credentials(self, mock_smtp_class):
        """Test sending without credentials."""
        notifier = EmailNotifier(username=None, password=None, recipient=None)
        result = notifier._send_email('Test', '<html>Test</html>')
        assert result is False
        assert not mock_smtp_class.called

    @patch('smtplib.SMTP')
    def test_connection_pooling(self, mock_smtp_class, notifier):
        """Test SMTP connection pooling."""
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp

        # First connection
        conn1 = notifier._get_connection()
        # Second connection should reuse
        conn2 = notifier._get_connection()

        assert conn1 == conn2
        # SMTP should only be called once for initial connection
        mock_smtp_class.assert_called_once()

    def test_close_connection(self, notifier):
        """Test connection closing."""
        notifier.smtp_connection = Mock()
        notifier._close_connection()
        assert notifier.smtp_connection is None
