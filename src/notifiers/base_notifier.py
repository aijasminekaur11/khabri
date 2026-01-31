"""
Base Notifier Interface
Abstract base class that all notifiers must implement
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseNotifier(ABC):
    """
    Abstract base class for all notifiers.
    Defines the contract that TelegramNotifier and EmailNotifier must follow.
    """

    @abstractmethod
    def send(self, digest: Dict[str, Any]) -> bool:
        """
        Send a digest to the recipient.

        Args:
            digest: The Digest dictionary containing:
                - type: str (morning | evening | event)
                - generated_at: datetime
                - news_items: List[Dict] (ProcessedNews items)
                - competitor_alerts: List[Dict] (CompetitorAlert items)
                - content_plan: Optional[Dict] (ContentPlan)

        Returns:
            bool: True if sent successfully, False otherwise
        """
        pass

    @abstractmethod
    def send_alert(self, news: Dict[str, Any]) -> bool:
        """
        Send a single high-priority alert.

        Args:
            news: The ProcessedNews dictionary containing:
                - id, title, url, source, category, content, published_at, scraped_at
                - signal_score, impact_level, discover_potential
                - celebrity_match, celebrity_deal_amount
                - keywords, verified, confidence, sources_checked

        Returns:
            bool: True if sent successfully, False otherwise
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the notifier service is available.

        Returns:
            bool: True if service is healthy, False otherwise
        """
        pass
