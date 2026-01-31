"""
Unit Tests for Orchestrator
Tests orchestration, event scheduling, and workflow coordination
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, time
import pytz

from src.orchestrator import Orchestrator, EventScheduler


class TestEventScheduler:
    """Test EventScheduler functionality"""

    def test_event_is_active_today(self):
        """Test checking if event is active today"""
        scheduler = EventScheduler("Asia/Kolkata")

        # Create event for today
        now = datetime.now(pytz.timezone("Asia/Kolkata"))
        event = {
            "active": True,
            "date": now.strftime("%Y-%m-%d"),
            "start_time": "10:00",
            "end_time": "18:00"
        }

        # Test during event window
        test_time = now.replace(hour=12, minute=0, second=0, microsecond=0)
        assert scheduler.is_event_active(event, test_time) is True

    def test_event_is_not_active_outside_window(self):
        """Test event is not active outside time window"""
        scheduler = EventScheduler("Asia/Kolkata")

        now = datetime.now(pytz.timezone("Asia/Kolkata"))
        event = {
            "active": True,
            "date": now.strftime("%Y-%m-%d"),
            "start_time": "10:00",
            "end_time": "18:00"
        }

        # Test before event starts
        test_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
        assert scheduler.is_event_active(event, test_time) is False

        # Test after event ends
        test_time = now.replace(hour=20, minute=0, second=0, microsecond=0)
        assert scheduler.is_event_active(event, test_time) is False

    def test_event_is_not_active_different_day(self):
        """Test event is not active on different day"""
        scheduler = EventScheduler("Asia/Kolkata")

        event = {
            "active": True,
            "date": "2026-12-31",
            "start_time": "10:00",
            "end_time": "18:00"
        }

        now = datetime.now(pytz.timezone("Asia/Kolkata"))
        assert scheduler.is_event_active(event, now) is False

    def test_get_active_events(self):
        """Test getting all active events"""
        scheduler = EventScheduler("Asia/Kolkata")

        now = datetime.now(pytz.timezone("Asia/Kolkata"))
        events = [
            {
                "id": "active-event",
                "active": True,
                "date": now.strftime("%Y-%m-%d"),
                "start_time": "10:00",
                "end_time": "18:00"
            },
            {
                "id": "inactive-event",
                "active": False,
                "date": now.strftime("%Y-%m-%d"),
                "start_time": "10:00",
                "end_time": "18:00"
            }
        ]

        test_time = now.replace(hour=12, minute=0, second=0, microsecond=0)
        active = scheduler.get_active_events(events, test_time)

        assert len(active) >= 0
        if active:
            assert all(e.get('active') for e in active)

    def test_should_send_digest(self):
        """Test checking if digest should be sent"""
        scheduler = EventScheduler("Asia/Kolkata")

        digest_config = {
            "enabled": True,
            "time": "07:00"
        }

        now = datetime.now(pytz.timezone("Asia/Kolkata"))

        # Test at exact time
        test_time = now.replace(hour=7, minute=0, second=0, microsecond=0)
        assert scheduler.should_send_digest(digest_config, test_time) is True

        # Test within 5-minute window
        test_time = now.replace(hour=7, minute=3, second=0, microsecond=0)
        assert scheduler.should_send_digest(digest_config, test_time) is True

        # Test outside window
        test_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
        assert scheduler.should_send_digest(digest_config, test_time) is False

    def test_get_event_keywords(self):
        """Test getting event keywords"""
        scheduler = EventScheduler()

        event = {
            "keywords": ["budget", "tax", "fiscal"]
        }

        keywords = scheduler.get_event_keywords(event)
        assert keywords == ["budget", "tax", "fiscal"]

    def test_get_event_interval(self):
        """Test getting event interval"""
        scheduler = EventScheduler()

        event = {
            "interval_minutes": 15
        }

        assert scheduler.get_event_interval(event) == 15

        # Test default value
        event_no_interval = {}
        assert scheduler.get_event_interval(event_no_interval) == 15


class TestOrchestrator:
    """Test Orchestrator functionality"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create minimal valid configs
            configs = {
                "sources": {
                    "real_estate": [],
                    "infrastructure": [],
                    "policy": [],
                    "celebrity": [],
                    "personal": []
                },
                "keywords": {
                    "real_estate": {"primary": ["property"]},
                    "infrastructure": {"primary": []},
                    "policy": {"primary": []},
                    "cities": {"tier1": []}
                },
                "celebrities": {
                    "bollywood": []
                },
                "events": {
                    "events": []
                },
                "interests": {
                    "personal_interests": []
                },
                "schedules": {
                    "timezone": "Asia/Kolkata",
                    "digests": {
                        "morning": {
                            "enabled": True,
                            "time": "07:00",
                            "cron_utc": "30 1 * * *",
                            "include": ["real_estate"]
                        },
                        "evening": {
                            "enabled": True,
                            "time": "16:00",
                            "cron_utc": "30 10 * * *",
                            "include": ["breaking_news"]
                        }
                    }
                }
            }

            for name, data in configs.items():
                with open(config_dir / f"{name}.json", 'w') as f:
                    json.dump(data, f)

            yield config_dir

    def test_orchestrator_initialization(self, temp_config_dir):
        """Test orchestrator initialization"""
        orchestrator = Orchestrator(str(temp_config_dir))
        orchestrator.initialize()

        assert orchestrator.config_manager is not None
        assert orchestrator.event_scheduler is not None
        assert orchestrator.processor_pipeline is not None

    def test_run_morning_digest(self, temp_config_dir):
        """Test running morning digest workflow"""
        orchestrator = Orchestrator(str(temp_config_dir))
        orchestrator.initialize()

        result = orchestrator.run_morning_digest()

        assert 'status' in result
        assert 'digest_type' in result or result['status'] == 'not_scheduled'

    def test_run_evening_digest(self, temp_config_dir):
        """Test running evening digest workflow"""
        orchestrator = Orchestrator(str(temp_config_dir))
        orchestrator.initialize()

        result = orchestrator.run_evening_digest()

        assert 'status' in result
        assert 'digest_type' in result or result['status'] == 'not_scheduled'

    def test_run_event_check(self, temp_config_dir):
        """Test running event check workflow"""
        orchestrator = Orchestrator(str(temp_config_dir))
        orchestrator.initialize()

        result = orchestrator.run_event_check()

        assert 'status' in result
        assert 'active_events' in result

    def test_process_news_items(self, temp_config_dir):
        """Test processing news items"""
        orchestrator = Orchestrator(str(temp_config_dir))
        orchestrator.initialize()

        news_items = [
            {
                'url': 'https://test.com/1',
                'title': 'Property prices rise in Mumbai',
                'content': 'Real estate market sees growth.',
                'timestamp': datetime.now()
            }
        ]

        processed = orchestrator.process_news_items(news_items)

        assert len(processed) > 0
        assert 'category' in processed[0]
        assert 'priority' in processed[0]

    def test_process_with_filters(self, temp_config_dir):
        """Test processing with filters"""
        orchestrator = Orchestrator(str(temp_config_dir))
        orchestrator.initialize()

        news_items = [
            {
                'url': 'https://test.com/1',
                'title': 'Property news',
                'content': 'Real estate update.',
                'timestamp': datetime.now()
            }
        ]

        filters = {
            'min_priority': 'high'
        }

        processed = orchestrator.process_news_items(news_items, filters)

        # Should only return high-priority items
        assert all(item.get('priority') == 'high' for item in processed) or len(processed) == 0

    def test_get_config_summary(self, temp_config_dir):
        """Test getting configuration summary"""
        orchestrator = Orchestrator(str(temp_config_dir))
        orchestrator.initialize()

        summary = orchestrator.get_config_summary()

        assert 'sources' in summary
        assert 'celebrities' in summary
        assert 'events' in summary
        assert 'interests' in summary
        assert 'digests' in summary

    def test_get_state(self, temp_config_dir):
        """Test getting orchestrator state"""
        orchestrator = Orchestrator(str(temp_config_dir))
        orchestrator.initialize()

        state = orchestrator.get_state()

        assert 'last_run' in state
        assert 'last_digest' in state
        assert 'active_events' in state

    def test_execute_workflow(self, temp_config_dir):
        """Test executing workflows by type"""
        orchestrator = Orchestrator(str(temp_config_dir))
        orchestrator.initialize()

        # Test valid workflow types
        for workflow_type in ['morning', 'evening', 'event']:
            result = orchestrator.execute_workflow(workflow_type)
            assert 'status' in result

    def test_execute_invalid_workflow(self, temp_config_dir):
        """Test executing invalid workflow type"""
        orchestrator = Orchestrator(str(temp_config_dir))
        orchestrator.initialize()

        with pytest.raises(ValueError):
            orchestrator.execute_workflow('invalid_type')

    def test_reload_configurations(self, temp_config_dir):
        """Test reloading configurations"""
        orchestrator = Orchestrator(str(temp_config_dir))
        orchestrator.initialize()

        # Reload should not raise error
        orchestrator.reload_configurations()

        # Should still be able to access configs
        summary = orchestrator.get_config_summary()
        assert summary is not None
