"""
Event Scheduler
Manages event-based alerts and scheduled digests
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, time
import pytz


class EventScheduler:
    """
    Manages event schedules and determines when to send alerts
    """

    def __init__(self, timezone: str = "Asia/Kolkata"):
        """
        Initialize EventScheduler

        Args:
            timezone: Timezone for schedule checks (default: Asia/Kolkata)
        """
        self.timezone = pytz.timezone(timezone)

    def is_event_active(self, event: Dict[str, Any], current_time: Optional[datetime] = None) -> bool:
        """
        Check if an event is currently active

        Args:
            event: Event configuration dictionary
            current_time: Current time (default: now)

        Returns:
            True if event is active, False otherwise
        """
        if not event.get('active', False):
            return False

        if current_time is None:
            current_time = datetime.now(self.timezone)

        # Parse event date
        try:
            event_date_str = event.get('date', '')
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
        except (ValueError, AttributeError):
            return False

        # Check if today is the event date
        if current_time.date() != event_date:
            return False

        # Parse start and end times
        try:
            start_time_str = event.get('start_time', '00:00')
            end_time_str = event.get('end_time', '23:59')

            start_hour, start_min = map(int, start_time_str.split(':'))
            end_hour, end_min = map(int, end_time_str.split(':'))

            start_time = time(start_hour, start_min)
            end_time = time(end_hour, end_min)
        except (ValueError, AttributeError):
            return False

        # Check if current time is within event window
        current_time_only = current_time.time()
        return start_time <= current_time_only <= end_time

    def get_active_events(
        self,
        events: List[Dict[str, Any]],
        current_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all currently active events

        Args:
            events: List of event configurations
            current_time: Current time (default: now)

        Returns:
            List of active events
        """
        return [
            event for event in events
            if self.is_event_active(event, current_time)
        ]

    def should_send_digest(
        self,
        digest_config: Dict[str, Any],
        current_time: Optional[datetime] = None
    ) -> bool:
        """
        Check if a digest should be sent now

        Args:
            digest_config: Digest configuration (morning or evening)
            current_time: Current time (default: now)

        Returns:
            True if digest should be sent, False otherwise
        """
        if not digest_config.get('enabled', False):
            return False

        if current_time is None:
            current_time = datetime.now(self.timezone)

        # Parse scheduled time
        try:
            scheduled_time_str = digest_config.get('time', '')
            hour, minute = map(int, scheduled_time_str.split(':'))
            scheduled_time = time(hour, minute)
        except (ValueError, AttributeError):
            return False

        # Check if current time matches scheduled time (within 5 minute window)
        current_time_only = current_time.time()
        time_diff_minutes = abs(
            (current_time_only.hour * 60 + current_time_only.minute) -
            (scheduled_time.hour * 60 + scheduled_time.minute)
        )

        return time_diff_minutes <= 5

    def get_event_keywords(self, event: Dict[str, Any]) -> List[str]:
        """
        Get keywords associated with an event

        Args:
            event: Event configuration

        Returns:
            List of keywords
        """
        return event.get('keywords', [])

    def get_event_sources(self, event: Dict[str, Any]) -> List[str]:
        """
        Get news sources to monitor for an event

        Args:
            event: Event configuration

        Returns:
            List of source URLs
        """
        return event.get('sources', [])

    def get_event_interval(self, event: Dict[str, Any]) -> int:
        """
        Get alert interval for an event in minutes

        Args:
            event: Event configuration

        Returns:
            Interval in minutes (default: 15)
        """
        return event.get('interval_minutes', 15)

    def format_event_summary(self, event: Dict[str, Any]) -> str:
        """
        Format event information as a summary string

        Args:
            event: Event configuration

        Returns:
            Formatted summary
        """
        name = event.get('name', 'Unknown Event')
        date = event.get('date', 'Unknown Date')
        start_time = event.get('start_time', '00:00')
        end_time = event.get('end_time', '23:59')

        return (
            f"{name}\n"
            f"Date: {date}\n"
            f"Time: {start_time} - {end_time} IST\n"
            f"Alert Interval: Every {self.get_event_interval(event)} minutes"
        )
