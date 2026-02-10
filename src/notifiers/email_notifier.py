"""
Email Notifier
Sends HTML email notifications via SMTP
"""

import os
import html as html_module
import logging
import smtplib
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from .base_notifier import BaseNotifier, NotificationError


logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):
    """
    Email notification implementation using SMTP.

    Requirements:
    - Use smtplib with Gmail SMTP
    - Support HTML email with templates
    - Support attachments (optional)
    - Handle connection pooling
    - Implement retry logic
    """

    # Gmail SMTP configuration
    DEFAULT_SMTP_SERVER = "smtp.gmail.com"
    DEFAULT_SMTP_PORT = 587

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0  # seconds

    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        recipient: Optional[str] = None
    ):
        """
        Initialize EmailNotifier

        Args:
            smtp_server: SMTP server address (defaults to Gmail)
            smtp_port: SMTP server port (defaults to 587)
            username: SMTP username (defaults to env SMTP_USERNAME)
            password: SMTP password (defaults to env SMTP_PASSWORD)
            recipient: Recipient email address (defaults to env EMAIL_RECIPIENT)
        """
        self.smtp_server = smtp_server or self.DEFAULT_SMTP_SERVER
        self.smtp_port = smtp_port or self.DEFAULT_SMTP_PORT
        self.username = username or os.getenv('SMTP_USERNAME')
        self.password = password or os.getenv('SMTP_PASSWORD')
        self.recipient = recipient or os.getenv('EMAIL_RECIPIENT')

        if not all([self.username, self.password, self.recipient]):
            logger.warning("Email credentials not fully configured. Notifier will not function.")

        self.smtp_connection = None

    def _get_connection(self):
        """
        Get or create SMTP connection with connection pooling

        Returns:
            SMTP connection object
        """
        try:
            # Test existing connection
            if self.smtp_connection:
                self.smtp_connection.noop()
                return self.smtp_connection
        except:
            self.smtp_connection = None

        # Create new connection
        try:
            connection = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
            connection.starttls()
            connection.login(self.username, self.password)
            self.smtp_connection = connection
            logger.info("SMTP connection established")
            return connection
        except Exception as e:
            logger.error(f"Failed to establish SMTP connection: {e}")
            return None

    def _close_connection(self):
        """Close SMTP connection"""
        if self.smtp_connection:
            try:
                self.smtp_connection.quit()
            except:
                pass
            self.smtp_connection = None

    def _send_email(
        self,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email with retry logic

        Args:
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text alternative (optional)
            attachments: List of file paths to attach (optional)

        Returns:
            bool: True if sent successfully
        """
        if not all([self.username, self.password, self.recipient]):
            logger.error("Email credentials not configured")
            return False

        for attempt in range(self.MAX_RETRIES):
            try:
                # Create message
                msg = MIMEMultipart('alternative')
                msg['From'] = self.username
                msg['To'] = self.recipient
                msg['Subject'] = subject

                # Attach plain text version
                if text_body:
                    msg.attach(MIMEText(text_body, 'plain'))

                # Attach HTML version
                msg.attach(MIMEText(html_body, 'html'))

                # Attach files if provided
                if attachments:
                    for filepath in attachments:
                        try:
                            with open(filepath, 'rb') as f:
                                part = MIMEBase('application', 'octet-stream')
                                part.set_payload(f.read())
                                encoders.encode_base64(part)
                                part.add_header(
                                    'Content-Disposition',
                                    f'attachment; filename={os.path.basename(filepath)}'
                                )
                                msg.attach(part)
                        except Exception as e:
                            logger.warning(f"Failed to attach file {filepath}: {e}")

                # Get connection and send
                connection = self._get_connection()
                if not connection:
                    raise Exception("Failed to get SMTP connection")

                connection.send_message(msg)
                logger.info(f"Email sent successfully (attempt {attempt + 1})")
                return True

            except Exception as e:
                logger.error(f"Email send error (attempt {attempt + 1}): {e}")
                self._close_connection()

                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                    time.sleep(delay)

        logger.error("Failed to send email after all retries")
        return False

    def _format_digest_html(self, digest: Dict[str, Any]) -> str:
        """
        Format digest as HTML email

        Args:
            digest: Digest dictionary

        Returns:
            HTML string
        """
        digest_type = digest.get('type', 'unknown').upper()
        generated_at = digest.get('generated_at', datetime.now())
        news_items = digest.get('news_items', [])
        competitor_alerts = digest.get('competitor_alerts', [])

        # Group by category
        categories = {}
        for item in news_items:
            category = item.get('category', 'uncategorized')
            if category not in categories:
                categories[category] = []
            categories[category].append(item)

        # Build HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                }}
                .category {{
                    margin-bottom: 30px;
                    border-left: 4px solid #667eea;
                    padding-left: 20px;
                }}
                .category h2 {{
                    color: #667eea;
                    font-size: 20px;
                    margin-bottom: 15px;
                }}
                .news-item {{
                    background: #f8f9fa;
                    padding: 15px;
                    margin-bottom: 15px;
                    border-radius: 5px;
                    border-left: 3px solid #ddd;
                }}
                .news-item.high {{
                    border-left-color: #dc3545;
                }}
                .news-item.medium {{
                    border-left-color: #ffc107;
                }}
                .news-item.low {{
                    border-left-color: #28a745;
                }}
                .news-item h3 {{
                    margin: 0 0 10px 0;
                    font-size: 18px;
                    color: #333;
                }}
                .news-item p {{
                    margin: 5px 0;
                    font-size: 14px;
                    color: #666;
                }}
                .metadata {{
                    display: flex;
                    gap: 15px;
                    margin-top: 10px;
                    font-size: 13px;
                }}
                .badge {{
                    display: inline-block;
                    padding: 3px 8px;
                    border-radius: 3px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                .badge.high {{
                    background: #dc3545;
                    color: white;
                }}
                .badge.medium {{
                    background: #ffc107;
                    color: #333;
                }}
                .badge.low {{
                    background: #28a745;
                    color: white;
                }}
                .keywords {{
                    margin-top: 10px;
                    color: #667eea;
                    font-size: 13px;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 2px solid #eee;
                    text-align: center;
                    color: #999;
                    font-size: 13px;
                }}
                .competitor-alert {{
                    background: #fff3cd;
                    border: 2px solid #ffc107;
                    padding: 15px;
                    margin-bottom: 15px;
                    border-radius: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{digest_type} DIGEST</h1>
                <p>Magic Bricks News Intelligence</p>
                <p>Generated: {generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """

        # Add competitor alerts if any
        if competitor_alerts:
            html += """
            <div class="category">
                <h2>🎯 Competitor Alerts</h2>
            """
            for alert in competitor_alerts:
                competitor = html_module.escape(alert.get('competitor', 'Unknown'))
                title = html_module.escape(alert.get('article_title', 'No title'))
                url = html_module.escape(alert.get('article_url', '#'), quote=True)
                gaps = [html_module.escape(g) for g in alert.get('gaps', [])]

                html += f"""
                <div class="competitor-alert">
                    <h3>{competitor} Published</h3>
                    <p><a href="{url}">{title}</a></p>
                    <p><strong>Gaps we can exploit:</strong> {', '.join(gaps[:3]) if gaps else 'None identified'}</p>
                </div>
                """
            html += "</div>"

        # Add news by category
        for category, items in categories.items():
            category_display = category.replace('_', ' ').title()
            html += f"""
            <div class="category">
                <h2>{category_display} ({len(items)})</h2>
            """

            for item in items:
                title = html_module.escape(item.get('title', 'No title'))
                url = html_module.escape(item.get('url', '#'), quote=True)
                source = html_module.escape(item.get('source', 'Unknown'))
                impact = item.get('impact_level', 'LOW').lower()
                score = item.get('signal_score', 0)
                discover = item.get('discover_potential', 0)
                content = item.get('content', '')
                keywords = item.get('keywords', [])

                # Extract snippet
                snippet = html_module.escape(content[:200] + "..." if len(content) > 200 else content)

                # Format keywords
                kw_list = []
                for kw in keywords[:5]:
                    if isinstance(kw, dict):
                        kw_list.append(html_module.escape(kw.get('keyword', '')))
                    else:
                        kw_list.append(html_module.escape(str(kw)))

                html += f"""
                <div class="news-item {impact}">
                    <h3><a href="{url}">{title}</a></h3>
                    <p>{snippet}</p>
                    <div class="metadata">
                        <span>Source: {source}</span>
                        <span class="badge {impact}">Impact: {impact.upper()}</span>
                        <span>Score: {score}/10</span>
                        <span>Discover: {discover}%</span>
                    </div>
                    {f'<div class="keywords">Keywords: {", ".join(kw_list)}</div>' if kw_list else ''}
                </div>
                """

            html += "</div>"

        html += """
            <div class="footer">
                <p>Magic Bricks News Intelligence System</p>
                <p>Automated digest generated by Claude Code</p>
            </div>
        </body>
        </html>
        """

        return html

    def _format_alert_html(self, news: Dict[str, Any]) -> str:
        """
        Format high-priority alert as HTML

        Args:
            news: ProcessedNews dictionary

        Returns:
            HTML string
        """
        title = html_module.escape(news.get('title', 'No title'))
        url = html_module.escape(news.get('url', '#'), quote=True)
        source = html_module.escape(news.get('source', 'Unknown'))
        impact = news.get('impact_level', 'LOW')
        score = news.get('signal_score', 0)
        discover = news.get('discover_potential', 0)
        content = news.get('content', '')
        keywords = news.get('keywords', [])
        celebrity = news.get('celebrity_match')
        verified = news.get('verified', False)

        # Escape content snippet
        content_snippet = html_module.escape(content[:300] + '...' if len(content) > 300 else content)

        # Escape celebrity if present
        safe_celebrity = html_module.escape(celebrity) if celebrity else None

        # Extract keywords
        kw_list = []
        for kw in keywords[:5]:
            if isinstance(kw, dict):
                kw_list.append(html_module.escape(kw.get('keyword', '')))
            else:
                kw_list.append(html_module.escape(str(kw)))

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .alert-header {{
                    background: #dc3545;
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }}
                .alert-header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .alert-content {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 5px;
                }}
                .alert-content h2 {{
                    margin-top: 0;
                    color: #333;
                }}
                .metrics {{
                    display: flex;
                    gap: 20px;
                    margin: 15px 0;
                }}
                .metric {{
                    flex: 1;
                    background: white;
                    padding: 10px;
                    border-radius: 5px;
                    text-align: center;
                }}
                .metric .value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #667eea;
                }}
                .metric .label {{
                    font-size: 12px;
                    color: #666;
                }}
                .keywords-section {{
                    margin: 15px 0;
                    padding: 10px;
                    background: white;
                    border-radius: 5px;
                }}
                .button {{
                    display: inline-block;
                    background: #667eea;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="alert-header">
                <h1>🚨 HIGH-IMPACT ALERT</h1>
                <p>Signal Score: {score}/10</p>
            </div>
            <div class="alert-content">
                <h2>{title}</h2>
                <p><strong>Source:</strong> {source}</p>
                {f'<p><strong>⭐ Celebrity:</strong> {safe_celebrity}</p>' if safe_celebrity else ''}
                <p>{content_snippet}</p>

                <div class="metrics">
                    <div class="metric">
                        <div class="value">{impact}</div>
                        <div class="label">Impact</div>
                    </div>
                    <div class="metric">
                        <div class="value">{score}/10</div>
                        <div class="label">Score</div>
                    </div>
                    <div class="metric">
                        <div class="value">{discover}%</div>
                        <div class="label">Discover</div>
                    </div>
                </div>

                {f'''<div class="keywords-section">
                    <strong>🎯 Keywords:</strong> {", ".join(kw_list)}
                </div>''' if kw_list else ''}

                <p><strong>Status:</strong> {'✅ Verified' if verified else '⚠️ Unverified'}</p>

                <a href="{url}" class="button">Read Full Article</a>
            </div>
        </body>
        </html>
        """

        return html

    def send(self, digest: Dict[str, Any]) -> bool:
        """
        Send a digest via email

        Args:
            digest: Digest dictionary

        Returns:
            bool: True if sent successfully
        """
        try:
            digest_type = digest.get('type', 'unknown').upper()
            subject = f"Magic Bricks {digest_type} Digest - {datetime.now().strftime('%Y-%m-%d')}"

            html_body = self._format_digest_html(digest)

            # Create plain text fallback
            text_body = f"{digest_type} DIGEST\n\n"
            text_body += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            text_body += "Please view in HTML-enabled email client for full formatting.\n"

            return self._send_email(subject, html_body, text_body)

        except Exception as e:
            logger.error(f"Error sending email digest: {e}")
            raise NotificationError(f"Failed to send email digest", e)

    def send_alert(self, news: Dict[str, Any]) -> bool:
        """
        Send a single high-priority alert via email

        Args:
            news: ProcessedNews dictionary

        Returns:
            bool: True if sent successfully
        """
        try:
            title = news.get('title', 'High-Impact News Alert')
            subject = f"🚨 ALERT: {title[:50]}"

            html_body = self._format_alert_html(news)

            # Create plain text fallback
            text_body = f"HIGH-IMPACT ALERT\n\n{title}\n\n"
            text_body += f"Score: {news.get('signal_score', 0)}/10\n"
            text_body += f"Impact: {news.get('impact_level', 'LOW')}\n\n"
            text_body += news.get('content', '')[:500] + "...\n\n"
            text_body += f"URL: {news.get('url', 'N/A')}"

            return self._send_email(subject, html_body, text_body)

        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            raise NotificationError(f"Failed to send email alert", e)

    def health_check(self) -> bool:
        """
        Check if SMTP service is accessible

        Returns:
            bool: True if service is healthy
        """
        if not all([self.username, self.password]):
            logger.error("Email credentials not configured")
            return False

        try:
            connection = self._get_connection()
            if connection:
                logger.info("Email health check passed")
                return True
            else:
                logger.warning("Email health check failed")
                return False

        except Exception as e:
            logger.error(f"Email health check error: {e}")
            return False

    def __del__(self):
        """Cleanup: close SMTP connection"""
        self._close_connection()
