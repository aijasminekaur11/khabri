"""
Main Orchestrator
Coordinates the entire news intelligence system workflow
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..config import ConfigManager
from ..processors import ProcessorPipeline
from .event_scheduler import EventScheduler


class Orchestrator:
    """
    Main orchestrator for the News Intelligence System
    Coordinates configuration, scraping, processing, and notifications
    """

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize Orchestrator

        Args:
            config_dir: Path to configuration directory (optional)
        """
        self.logger = logging.getLogger(__name__)

        # Initialize configuration manager
        self.config_manager = ConfigManager(config_dir)

        # Initialize event scheduler
        self.event_scheduler = EventScheduler()

        # Processor pipeline (initialized after loading config)
        self.processor_pipeline: Optional[ProcessorPipeline] = None

        # State tracking
        self.state = {
            'last_run': None,
            'last_digest': {
                'morning': None,
                'evening': None
            },
            'active_events': [],
            'total_news_processed': 0
        }

    def initialize(self):
        """
        Initialize the orchestrator by loading configurations
        """
        self.logger.info("Initializing orchestrator...")

        # Load all configurations
        try:
            self.config_manager.load_all_configs(validate=True)
            self.logger.info("Configurations loaded and validated successfully")
        except ValueError as e:
            self.logger.error(f"Configuration validation failed: {e}")
            raise

        # Initialize processor pipeline with loaded configs
        self._initialize_processor_pipeline()

        self.logger.info("Orchestrator initialized successfully")

    def _initialize_processor_pipeline(self):
        """Initialize the processor pipeline with loaded configurations"""
        celebrities_config = self.config_manager.get_celebrities()
        keywords_config = self.config_manager.get_keywords()

        self.processor_pipeline = ProcessorPipeline(
            celebrities_config=celebrities_config,
            keywords_config=keywords_config,
            enable_deduplication=True,
            enable_celebrity_matching=True,
            enable_categorization=True,
            enable_summarization=True
        )

    def run_morning_digest(self) -> Dict[str, Any]:
        """
        Run morning digest workflow

        Returns:
            Dictionary with execution results
        """
        self.logger.info("Starting morning digest workflow...")

        digest_config = self.config_manager.get_digest_schedule('morning')

        if not digest_config or not digest_config.get('enabled', False):
            self.logger.warning("Morning digest is not enabled")
            return {'status': 'disabled', 'items_processed': 0}

        # Check if it's time to send
        if not self.event_scheduler.should_send_digest(digest_config):
            self.logger.info("Not the scheduled time for morning digest")
            return {'status': 'not_scheduled', 'items_processed': 0}

        result = {
            'status': 'success',
            'digest_type': 'morning',
            'timestamp': datetime.now().isoformat(),
            'items_processed': 0,
            'categories': digest_config.get('include', [])
        }

        # Note: Actual scraping would be done by CLI 2 (scrapers)
        # This orchestrator coordinates the workflow

        self.state['last_digest']['morning'] = datetime.now().isoformat()

        return result

    def run_evening_digest(self) -> Dict[str, Any]:
        """
        Run evening digest workflow

        Returns:
            Dictionary with execution results
        """
        self.logger.info("Starting evening digest workflow...")

        digest_config = self.config_manager.get_digest_schedule('evening')

        if not digest_config or not digest_config.get('enabled', False):
            self.logger.warning("Evening digest is not enabled")
            return {'status': 'disabled', 'items_processed': 0}

        # Check if it's time to send
        if not self.event_scheduler.should_send_digest(digest_config):
            self.logger.info("Not the scheduled time for evening digest")
            return {'status': 'not_scheduled', 'items_processed': 0}

        result = {
            'status': 'success',
            'digest_type': 'evening',
            'timestamp': datetime.now().isoformat(),
            'items_processed': 0,
            'categories': digest_config.get('include', [])
        }

        self.state['last_digest']['evening'] = datetime.now().isoformat()

        return result

    def run_event_check(self) -> Dict[str, Any]:
        """
        Check for active events and send alerts if needed

        Returns:
            Dictionary with execution results
        """
        self.logger.info("Checking for active events...")

        # Get all events
        events = self.config_manager.get_events()

        # Find active events
        active_events = self.event_scheduler.get_active_events(events)

        result = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'active_events': len(active_events),
            'event_names': [e.get('name') for e in active_events]
        }

        if not active_events:
            self.logger.info("No active events at this time")
            result['status'] = 'no_active_events'
            return result

        # Process each active event
        for event in active_events:
            self.logger.info(f"Processing active event: {event.get('name')}")
            # Event-specific processing would be coordinated here

        self.state['active_events'] = [e.get('id') for e in active_events]

        return result

    def process_news_items(
        self,
        news_items: List[Dict[str, Any]],
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process news items through the pipeline

        Args:
            news_items: List of raw news items
            filters: Optional filters to apply

        Returns:
            List of processed news items
        """
        if not self.processor_pipeline:
            raise RuntimeError("Processor pipeline not initialized. Call initialize() first.")

        if filters:
            processed = self.processor_pipeline.process_with_filters(
                news_items,
                categories=filters.get('categories'),
                min_priority=filters.get('min_priority'),
                celebrity_only=filters.get('celebrity_only', False),
                high_value_only=filters.get('high_value_only', False)
            )
        else:
            processed = self.processor_pipeline.process(news_items)

        self.state['total_news_processed'] += len(processed)

        return processed

    def get_processor_stats(self) -> Dict[str, int]:
        """
        Get processing statistics

        Returns:
            Dictionary with processing stats
        """
        if not self.processor_pipeline:
            return {}

        return self.processor_pipeline.get_stats()

    def get_state(self) -> Dict[str, Any]:
        """
        Get current orchestrator state

        Returns:
            Current state dictionary
        """
        return self.state.copy()

    def reload_configurations(self):
        """Reload all configurations"""
        self.logger.info("Reloading configurations...")
        self.config_manager.reload_all()
        self._initialize_processor_pipeline()
        self.logger.info("Configurations reloaded successfully")

    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of loaded configurations

        Returns:
            Configuration summary
        """
        all_configs = self.config_manager.get_all()

        summary = {
            'sources': {
                category: len(sources)
                for category, sources in all_configs.get('sources', {}).items()
            },
            'celebrities': {
                category: len(celebs)
                for category, celebs in all_configs.get('celebrities', {}).items()
            },
            'events': {
                'total': len(all_configs.get('events', {}).get('events', [])),
                'active': len(self.config_manager.get_events(active_only=True))
            },
            'interests': {
                'total': len(all_configs.get('interests', {}).get('personal_interests', [])),
                'active': len(self.config_manager.get_interests(active_only=True))
            },
            'digests': {
                'morning_enabled': self.config_manager.is_digest_enabled('morning'),
                'evening_enabled': self.config_manager.is_digest_enabled('evening')
            }
        }

        return summary

    def execute_workflow(self, workflow_type: str) -> Dict[str, Any]:
        """
        Execute a specific workflow type

        Args:
            workflow_type: Type of workflow ('morning', 'evening', 'event')

        Returns:
            Execution result dictionary
        """
        workflow_map = {
            'morning': self.run_morning_digest,
            'evening': self.run_evening_digest,
            'event': self.run_event_check
        }

        if workflow_type not in workflow_map:
            raise ValueError(f"Unknown workflow type: {workflow_type}")

        return workflow_map[workflow_type]()
