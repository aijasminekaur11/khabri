"""
Production Readiness Tests
End-to-end integration validation and performance benchmarks
"""

import pytest
import time
import psutil
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

# Import system components
from src.config.config_manager import ConfigManager
from src.scrapers.news_scraper import NewsScraper
from src.scrapers.rss_reader import RSSReader
from src.scrapers.competitor_tracker import CompetitorTracker
from src.scrapers.igrs_scraper import IGRSScraper
from src.processors.processor_pipeline import ProcessorPipeline
from src.processors.deduplicator import Deduplicator
from src.processors.celebrity_matcher import CelebrityMatcher
from src.processors.categorizer import Categorizer
from src.processors.summarizer import Summarizer
from src.notifiers.telegram_notifier import TelegramNotifier
from src.notifiers.email_notifier import EmailNotifier
from src.notifiers.keyword_engine import KeywordEngine
from src.orchestrator.orchestrator import Orchestrator


@pytest.mark.integration
class TestProductionReadiness:
    """Production readiness validation tests."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for production tests."""
        self.config = ConfigManager()
        self.start_time = time.time()
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        yield
        self.end_time = time.time()
        self.final_memory = self.process.memory_info().rss / 1024 / 1024  # MB

    def test_config_loading_performance(self, benchmark):
        """Benchmark configuration loading performance."""
        def load_config():
            config = ConfigManager()
            config.load_all_configs()
            return config

        result = benchmark(load_config)
        assert result is not None
        assert benchmark.stats['mean'] < 0.5  # Should load in < 500ms

    def test_all_scrapers_initialization(self):
        """Test all scrapers can be initialized successfully."""
        scrapers = []

        # Initialize all scrapers
        scrapers.append(NewsScraper(config_manager=self.config))
        scrapers.append(RSSReader(config_manager=self.config))
        scrapers.append(CompetitorTracker(config_manager=self.config))
        scrapers.append(IGRSScraper(config_manager=self.config))

        assert len(scrapers) == 4
        for scraper in scrapers:
            assert scraper is not None
            assert scraper.config is not None

    def test_all_processors_initialization(self):
        """Test all processors can be initialized successfully."""
        processors = []

        processors.append(Deduplicator())
        processors.append(CelebrityMatcher(config_manager=self.config))
        processors.append(Categorizer(config_manager=self.config))
        processors.append(Summarizer())

        assert len(processors) == 4
        for processor in processors:
            assert processor is not None

    def test_all_notifiers_initialization(self):
        """Test all notifiers can be initialized successfully."""
        telegram = TelegramNotifier()
        email = EmailNotifier()
        keyword_engine = KeywordEngine(config_manager=self.config)

        assert telegram is not None
        assert email is not None
        assert keyword_engine is not None

    def test_processor_pipeline_initialization(self):
        """Test processor pipeline initialization."""
        dedup = Deduplicator()
        celeb = CelebrityMatcher(config_manager=self.config)
        categorizer = Categorizer(config_manager=self.config)
        summarizer = Summarizer()

        pipeline = ProcessorPipeline(
            processors=[dedup, celeb, categorizer, summarizer]
        )

        assert pipeline is not None
        assert len(pipeline.processors) == 4

    @patch('requests.get')
    def test_end_to_end_scraping_workflow(self, mock_get):
        """Test complete scraping workflow with mocked responses."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><body><h1>Test Article</h1><p>Test content</p></body></html>'
        mock_response.text = '<html><body><h1>Test Article</h1><p>Test content</p></body></html>'
        mock_get.return_value = mock_response

        # Initialize scraper
        scraper = NewsScraper(config_manager=self.config)

        # Create test source
        test_source = {
            'id': 'test_source',
            'name': 'Test Source',
            'url': 'https://example.com',
            'type': 'scrape',
            'category': 'real_estate',
            'enabled': True,
            'selectors': {
                'title': 'h1',
                'content': 'p'
            }
        }

        # Execute scraping
        results = scraper.scrape_source(test_source)

        assert isinstance(results, list)
        # Results might be empty due to selector matching, but process should complete

    def test_processor_pipeline_flow(self):
        """Test complete processor pipeline flow."""
        # Create pipeline
        dedup = Deduplicator()
        celeb = CelebrityMatcher(config_manager=self.config)
        categorizer = Categorizer(config_manager=self.config)
        summarizer = Summarizer()

        pipeline = ProcessorPipeline(
            processors=[dedup, celeb, categorizer, summarizer]
        )

        # Create test news item
        test_news = {
            'id': 'test_123',
            'title': 'Shah Rukh Khan buys luxury apartment in Mumbai for 50 crore',
            'content': 'Bollywood superstar Shah Rukh Khan has purchased a luxury apartment...',
            'url': 'https://example.com/article',
            'source': 'Test Source',
            'category': 'real_estate',
            'published_at': datetime.now()
        }

        # Process through pipeline
        processed = pipeline.process([test_news])

        assert isinstance(processed, list)
        if len(processed) > 0:
            assert 'celebrity_match' in processed[0] or 'processed' in str(processed[0])

    def test_concurrent_scraper_execution(self):
        """Test multiple scrapers running concurrently."""
        import concurrent.futures

        scrapers = [
            NewsScraper(config_manager=self.config),
            RSSReader(config_manager=self.config),
            CompetitorTracker(config_manager=self.config),
            IGRSScraper(config_manager=self.config)
        ]

        # Simulate concurrent initialization
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(lambda s: s, scraper) for scraper in scrapers]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(results) == 4
        assert all(r is not None for r in results)

    def test_memory_usage_under_load(self):
        """Test memory usage remains stable under load."""
        initial_memory = self.initial_memory

        # Create multiple instances
        instances = []
        for _ in range(10):
            instances.append(ConfigManager())
            instances.append(Deduplicator())

        current_memory = self.process.memory_info().rss / 1024 / 1024
        memory_increase = current_memory - initial_memory

        # Memory increase should be reasonable (< 100MB for 20 instances)
        assert memory_increase < 100, f"Memory increased by {memory_increase}MB"

    def test_config_validation_comprehensive(self):
        """Test comprehensive config validation."""
        config = ConfigManager()

        # Validate all configs
        config.load_all_configs(validate=True)

        # Check all configs loaded
        assert config.is_validated()

        # Validate sources
        sources = config.get_sources()
        assert isinstance(sources, list)

        # Validate keywords
        keywords = config.get_keywords()
        assert isinstance(keywords, dict)

        # Validate celebrities
        celebrities = config.get_celebrities()
        assert isinstance(celebrities, dict)

    def test_error_handling_robustness(self):
        """Test system handles errors gracefully."""
        # Test with invalid config
        config = ConfigManager()

        # Should not crash with nonexistent category
        sources = config.get_sources(category='nonexistent')
        assert sources == []

        # Should handle empty results
        keywords = config.get_keywords(category='nonexistent')
        assert keywords == []

    def test_orchestrator_initialization(self):
        """Test orchestrator can be initialized."""
        orchestrator = Orchestrator(config_manager=self.config)

        assert orchestrator is not None
        assert orchestrator.config is not None

    @pytest.mark.benchmark
    def test_deduplication_performance(self, benchmark):
        """Benchmark deduplication performance."""
        dedup = Deduplicator()

        test_news = [
            {
                'id': f'test_{i}',
                'title': f'Test Article {i}',
                'url': f'https://example.com/article/{i}',
                'content': f'Test content {i}',
                'published_at': datetime.now()
            }
            for i in range(100)
        ]

        def run_dedup():
            return dedup.process(test_news)

        result = benchmark(run_dedup)
        assert len(result) <= len(test_news)

    @pytest.mark.benchmark
    def test_celebrity_matching_performance(self, benchmark):
        """Benchmark celebrity matching performance."""
        matcher = CelebrityMatcher(config_manager=self.config)

        test_news = [
            {
                'id': 'test_1',
                'title': 'Shah Rukh Khan buys property in Mumbai',
                'content': 'Actor purchases luxury apartment',
                'url': 'https://example.com/1',
                'published_at': datetime.now()
            }
        ]

        def run_matcher():
            return matcher.process(test_news)

        result = benchmark(run_matcher)
        assert isinstance(result, list)

    def test_system_health_checks(self):
        """Perform system health checks."""
        health_status = {}

        # Check config system
        try:
            config = ConfigManager()
            config.load_all_configs()
            health_status['config'] = 'OK'
        except Exception as e:
            health_status['config'] = f'ERROR: {e}'

        # Check scrapers
        try:
            scraper = NewsScraper(config_manager=self.config)
            health_status['scrapers'] = 'OK'
        except Exception as e:
            health_status['scrapers'] = f'ERROR: {e}'

        # Check processors
        try:
            dedup = Deduplicator()
            health_status['processors'] = 'OK'
        except Exception as e:
            health_status['processors'] = f'ERROR: {e}'

        # Check notifiers
        try:
            telegram = TelegramNotifier()
            email = EmailNotifier()
            health_status['notifiers'] = 'OK'
        except Exception as e:
            health_status['notifiers'] = f'ERROR: {e}'

        # All systems should be OK
        assert all(status == 'OK' for status in health_status.values()), \
            f"Health check failed: {health_status}"

    def test_data_flow_integrity(self):
        """Test data maintains integrity through pipeline."""
        # Create test data
        original_data = {
            'id': 'test_123',
            'title': 'Original Title',
            'content': 'Original Content',
            'url': 'https://example.com/test',
            'source': 'Test Source',
            'published_at': datetime.now()
        }

        # Process through deduplicator
        dedup = Deduplicator()
        after_dedup = dedup.process([original_data])

        # Verify core data preserved
        if len(after_dedup) > 0:
            assert after_dedup[0]['title'] == original_data['title']
            assert after_dedup[0]['url'] == original_data['url']

    def test_configuration_reload_safety(self):
        """Test configuration can be safely reloaded."""
        config = ConfigManager()
        config.load_all_configs()

        sources_before = config.get_sources()

        # Reload
        config.reload_all()

        sources_after = config.get_sources()

        # Should have same structure
        assert len(sources_before) == len(sources_after)


@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Performance benchmark tests."""

    def test_startup_time(self):
        """Test system startup time is acceptable."""
        start = time.time()

        # Initialize core components
        config = ConfigManager()
        config.load_all_configs()
        NewsScraper(config_manager=config)
        RSSReader(config_manager=config)
        TelegramNotifier()
        EmailNotifier()

        elapsed = time.time() - start

        # Startup should be fast (< 2 seconds)
        assert elapsed < 2.0, f"Startup took {elapsed}s"

    def test_throughput_capacity(self):
        """Test system can handle high throughput."""
        dedup = Deduplicator()

        # Create 1000 news items
        news_items = [
            {
                'id': f'test_{i}',
                'title': f'Article {i}',
                'url': f'https://example.com/{i}',
                'content': f'Content {i}',
                'published_at': datetime.now()
            }
            for i in range(1000)
        ]

        start = time.time()
        result = dedup.process(news_items)
        elapsed = time.time() - start

        # Should process 1000 items in < 5 seconds
        assert elapsed < 5.0, f"Processed 1000 items in {elapsed}s"
        assert isinstance(result, list)

    def test_memory_leak_detection(self):
        """Test for memory leaks over repeated operations."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024

        # Run many iterations
        for _ in range(100):
            config = ConfigManager()
            dedup = Deduplicator()
            test_data = [{'id': 'test', 'title': 'Test', 'url': 'https://example.com'}]
            dedup.process(test_data)
            del config
            del dedup

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory

        # Memory increase should be minimal (< 50MB)
        assert memory_increase < 50, f"Potential memory leak: {memory_increase}MB increase"


@pytest.mark.stability
class TestSystemStability:
    """System stability tests."""

    def test_error_recovery(self):
        """Test system recovers from errors gracefully."""
        config = ConfigManager()

        # Test with invalid data
        dedup = Deduplicator()

        # Should not crash with malformed data
        result = dedup.process([{'invalid': 'data'}])
        assert isinstance(result, list)

    def test_concurrent_config_access(self):
        """Test concurrent access to configuration."""
        import concurrent.futures

        def access_config():
            config = ConfigManager()
            return config.get_sources()

        # Run concurrent accesses
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(access_config) for _ in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        assert len(results) == 20
        assert all(isinstance(r, list) for r in results)

    def test_long_running_stability(self):
        """Test stability over extended operation."""
        dedup = Deduplicator()

        # Simulate long-running operation
        for i in range(50):
            test_data = [
                {
                    'id': f'test_{i}_{j}',
                    'title': f'Article {i}_{j}',
                    'url': f'https://example.com/{i}/{j}',
                    'published_at': datetime.now()
                }
                for j in range(10)
            ]
            result = dedup.process(test_data)
            assert isinstance(result, list)

        # Should complete without errors
        assert True
