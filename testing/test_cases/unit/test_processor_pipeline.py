"""
Unit Tests for Processor Pipeline
Tests deduplication, categorization, celebrity matching, and summarization
"""

import pytest
from datetime import datetime
from src.processors import (
    Deduplicator,
    Categorizer,
    CelebrityMatcher,
    Summarizer,
    ProcessorPipeline
)


class TestDeduplicator:
    """Test Deduplicator functionality"""

    def test_url_deduplication(self):
        """Test deduplication by URL"""
        dedup = Deduplicator()

        item1 = {
            'url': 'https://test.com/article1',
            'title': 'Test Article',
            'timestamp': datetime.now()
        }

        item2 = {
            'url': 'https://test.com/article1',
            'title': 'Same Article',
            'timestamp': datetime.now()
        }

        # First item is not duplicate
        assert dedup.is_duplicate(item1) is False

        # Mark as seen
        dedup.mark_as_seen(item1)

        # Second item is duplicate
        assert dedup.is_duplicate(item2) is True

    def test_title_similarity_deduplication(self):
        """Test deduplication by title similarity"""
        dedup = Deduplicator(similarity_threshold=0.85)

        item1 = {
            'url': 'https://test.com/article1',
            'title': 'Mumbai property prices rise by 5 percent',
            'timestamp': datetime.now()
        }

        item2 = {
            'url': 'https://test.com/article2',
            'title': 'Mumbai property prices rise by 5 percentage',
            'timestamp': datetime.now()
        }

        dedup.mark_as_seen(item1)
        assert dedup.is_duplicate(item2) is True

    def test_deduplicate_list(self):
        """Test deduplicating a list of items"""
        dedup = Deduplicator()

        items = [
            {'url': 'https://test.com/1', 'title': 'Mumbai property prices rise', 'timestamp': datetime.now()},
            {'url': 'https://test.com/1', 'title': 'Mumbai property prices increase', 'timestamp': datetime.now()},
            {'url': 'https://test.com/2', 'title': 'Delhi Metro expansion announced', 'timestamp': datetime.now()},
        ]

        unique = dedup.deduplicate(items)
        assert len(unique) == 2


class TestCelebrityMatcher:
    """Test CelebrityMatcher functionality"""

    @pytest.fixture
    def celeb_config(self):
        """Celebrity configuration for testing"""
        return {
            "bollywood": [
                {
                    "name": "Shah Rukh Khan",
                    "aliases": ["SRK", "King Khan"],
                    "priority": "high"
                }
            ],
            "cricket": [
                {
                    "name": "Virat Kohli",
                    "aliases": ["Kohli", "King Kohli"],
                    "priority": "high"
                }
            ]
        }

    def test_celebrity_detection(self, celeb_config):
        """Test celebrity name detection"""
        matcher = CelebrityMatcher(celeb_config)

        news_item = {
            'title': 'Shah Rukh Khan buys new apartment in Mumbai',
            'content': 'The Bollywood star purchased a luxury property.'
        }

        match = matcher.match_celebrities(news_item)

        assert match is not None
        assert match['celebrity_name'] == 'Shah Rukh Khan'
        assert match['celebrity_category'] == 'bollywood'

    def test_alias_detection(self, celeb_config):
        """Test celebrity alias detection"""
        matcher = CelebrityMatcher(celeb_config)

        news_item = {
            'title': 'SRK spotted at new property',
            'content': 'The actor visited his new home.'
        }

        match = matcher.match_celebrities(news_item)

        assert match is not None
        assert match['celebrity_name'] == 'Shah Rukh Khan'
        assert match['matched_term'] == 'srk'

    def test_property_value_extraction(self, celeb_config):
        """Test property value extraction"""
        matcher = CelebrityMatcher(celeb_config)

        news_item = {
            'title': 'Virat Kohli buys ₹34 Cr apartment',
            'content': 'The cricketer purchased a luxury home.'
        }

        match = matcher.match_celebrities(news_item)

        assert match is not None
        assert match['property_value_cr'] == 34.0
        assert match['is_high_value'] is True

    def test_high_value_detection(self, celeb_config):
        """Test high-value deal detection (₹5Cr+)"""
        matcher = CelebrityMatcher(celeb_config)

        high_value_item = {
            'title': 'SRK buys ₹100 Cr mansion',
            'content': 'Expensive property.'
        }

        low_value_item = {
            'title': 'SRK buys ₹2 Cr flat',
            'content': 'Affordable property.'
        }

        high_match = matcher.match_celebrities(high_value_item)
        low_match = matcher.match_celebrities(low_value_item)

        assert high_match['is_high_value'] is True
        assert low_match['is_high_value'] is False


class TestCategorizer:
    """Test Categorizer functionality"""

    @pytest.fixture
    def keywords_config(self):
        """Keywords configuration for testing"""
        return {
            "real_estate": {
                "primary": ["property", "real estate", "housing", "apartment"],
                "builders": ["DLF", "Godrej"]
            },
            "infrastructure": {
                "primary": ["metro", "airport", "expressway"]
            }
        }

    def test_categorization(self, keywords_config):
        """Test basic categorization"""
        categorizer = Categorizer(keywords_config)

        news_item = {
            'title': 'New DLF apartment project in Gurgaon',
            'content': 'DLF launches new residential property.'
        }

        result = categorizer.categorize(news_item)

        assert result['category'] == 'real_estate'
        assert result['score'] > 0
        assert 'dlf' in result['matched_keywords']

    def test_priority_assignment(self, keywords_config):
        """Test priority assignment"""
        categorizer = Categorizer(keywords_config)

        high_priority_item = {
            'title': 'Major property policy change',
            'content': 'Government announces new real estate regulations',
            'category': 'policy',
            'score': 0.15
        }

        low_priority_item = {
            'title': 'Minor news',
            'content': 'Small update',
            'category': 'uncategorized',
            'score': 0.01
        }

        assert categorizer.assign_priority(high_priority_item) == 'high'
        assert categorizer.assign_priority(low_priority_item) == 'low'

    def test_filter_by_category(self, keywords_config):
        """Test filtering by category"""
        categorizer = Categorizer(keywords_config)

        items = [
            {'category': 'real_estate', 'title': 'RE news'},
            {'category': 'infrastructure', 'title': 'Infra news'},
            {'category': 'policy', 'title': 'Policy news'}
        ]

        filtered = categorizer.filter_by_category(items, ['real_estate'])

        assert len(filtered) == 1
        assert filtered[0]['category'] == 'real_estate'


class TestSummarizer:
    """Test Summarizer functionality"""

    def test_generate_summary(self):
        """Test summary generation"""
        summarizer = Summarizer(max_summary_length=100)

        news_item = {
            'title': 'Mumbai property prices rise',
            'content': 'Property prices in Mumbai have risen by 5%. This is due to high demand. Experts predict continued growth.'
        }

        summary = summarizer.generate_summary(news_item)

        assert summary is not None
        assert len(summary) <= 100
        assert len(summary) > 0

    def test_extract_key_points(self):
        """Test key points extraction"""
        summarizer = Summarizer()

        news_item = {
            'title': 'Celebrity property deal',
            'category': 'real_estate',
            'is_celebrity_news': True,
            'celebrity_match': {
                'celebrity_name': 'Shah Rukh Khan',
                'property_value_cr': 50.0
            },
            'matched_keywords': ['property', 'luxury', 'mumbai']
        }

        key_points = summarizer.extract_key_points(news_item)

        assert len(key_points) > 0
        assert any('Celebrity' in kp for kp in key_points)
        assert any('Value' in kp for kp in key_points)

    def test_generate_headline(self):
        """Test headline generation"""
        summarizer = Summarizer()

        news_item = {
            'title': 'This is a very long title that should be truncated because it exceeds the maximum allowed length for headlines',
            'content': 'Content here'
        }

        headline = summarizer.generate_headline(news_item)

        assert headline is not None
        assert len(headline) <= 100


class TestProcessorPipeline:
    """Test complete ProcessorPipeline"""

    @pytest.fixture
    def pipeline_config(self):
        """Configuration for pipeline testing"""
        celebrities = {
            "bollywood": [
                {"name": "Test Celebrity", "aliases": ["TC"], "priority": "high"}
            ]
        }

        keywords = {
            "real_estate": {
                "primary": ["property", "real estate"]
            }
        }

        return celebrities, keywords

    def test_full_pipeline(self, pipeline_config):
        """Test complete processing pipeline"""
        celebs, keywords = pipeline_config

        pipeline = ProcessorPipeline(
            celebrities_config=celebs,
            keywords_config=keywords
        )

        news_items = [
            {
                'url': 'https://test.com/1',
                'title': 'Test Celebrity buys property',
                'content': 'The celebrity purchased real estate in Mumbai.',
                'timestamp': datetime.now()
            },
            {
                'url': 'https://test.com/2',
                'title': 'Property market update',
                'content': 'Real estate prices are rising.',
                'timestamp': datetime.now()
            },
            {
                'url': 'https://test.com/1',  # Duplicate
                'title': 'Test Celebrity buys property',
                'content': 'Duplicate article.',
                'timestamp': datetime.now()
            }
        ]

        processed = pipeline.process(news_items)

        # Should have 2 items (1 duplicate removed)
        assert len(processed) == 2

        # Check processing fields added
        for item in processed:
            assert 'category' in item
            assert 'priority' in item
            assert 'summary' in item
            assert 'headline' in item

    def test_pipeline_stats(self, pipeline_config):
        """Test pipeline statistics"""
        celebs, keywords = pipeline_config

        pipeline = ProcessorPipeline(
            celebrities_config=celebs,
            keywords_config=keywords
        )

        news_items = [
            {
                'url': 'https://test.com/1',
                'title': 'Test Celebrity property deal',
                'content': 'Celebrity news about real estate.',
                'timestamp': datetime.now()
            }
        ]

        pipeline.process(news_items)
        stats = pipeline.get_stats()

        assert stats['total_input'] == 1
        assert stats['total_output'] == 1
        assert stats['duplicates_removed'] == 0
