"""
Unit Tests for Categorizer
Tests news categorization based on keywords and priority assignment
"""

import pytest
from src.processors.categorizer import Categorizer


class TestCategorizer:
    """Test Categorizer functionality"""

    @pytest.fixture
    def keywords_config(self):
        """Keywords configuration for testing"""
        return {
            "real_estate": {
                "primary": ["property", "real estate", "housing", "apartment"],
                "builders": ["DLF", "Godrej", "Oberoi"]
            },
            "infrastructure": {
                "primary": ["metro", "airport", "expressway", "highway"]
            },
            "policy": {
                "primary": ["RBI", "policy", "regulation", "government"]
            }
        }

    @pytest.fixture
    def categorizer(self, keywords_config):
        """Create a Categorizer instance"""
        return Categorizer(keywords_config)

    def test_initialization(self, categorizer, keywords_config):
        """Test Categorizer initializes correctly"""
        assert categorizer.keywords_config == keywords_config
        assert "real_estate" in categorizer.category_keywords
        assert "infrastructure" in categorizer.category_keywords
        assert "policy" in categorizer.category_keywords

    def test_categorization_real_estate(self, categorizer):
        """Test categorization of real estate news"""
        news_item = {
            'title': 'New DLF apartment project in Gurgaon',
            'content': 'DLF launches new residential property with modern amenities.'
        }

        result = categorizer.categorize(news_item)

        assert result['category'] == 'real_estate'
        assert result['score'] > 0
        assert 'dlf' in result['matched_keywords']
        assert 'property' in result['matched_keywords']

    def test_categorization_infrastructure(self, categorizer):
        """Test categorization of infrastructure news"""
        news_item = {
            'title': 'New metro line announced for Mumbai',
            'content': 'The government announced a new metro line connecting suburbs.'
        }

        result = categorizer.categorize(news_item)

        assert result['category'] == 'infrastructure'
        assert 'metro' in result['matched_keywords']

    def test_categorization_policy(self, categorizer):
        """Test categorization of policy news"""
        news_item = {
            'title': 'RBI announces new housing policy',
            'content': 'The Reserve Bank of India introduced new regulations for home loans.'
        }

        result = categorizer.categorize(news_item)

        assert result['category'] == 'policy'
        assert 'rbi' in result['matched_keywords'] or 'policy' in result['matched_keywords']

    def test_uncategorized_content(self, categorizer):
        """Test handling of uncategorized content"""
        news_item = {
            'title': 'Random unrelated news',
            'content': 'This content does not match any category.'
        }

        result = categorizer.categorize(news_item)

        assert result['category'] == 'uncategorized'
        assert result['score'] < 0.01

    def test_empty_content(self, categorizer):
        """Test handling of empty content"""
        news_item = {
            'title': '',
            'content': ''
        }

        result = categorizer.categorize(news_item)

        assert result['category'] == 'uncategorized'
        assert result['score'] == 0.0

    def test_calculate_match_score(self, categorizer):
        """Test the match score calculation"""
        text = "DLF launches new property in Mumbai"
        keywords = {"dlf", "property", "mumbai", "apartment"}

        score = categorizer._calculate_match_score(text, keywords)

        assert 0 <= score <= 1
        assert score > 0  # Should match at least "dlf" and "property"

    def test_priority_assignment_high_celebrity(self, categorizer):
        """Test high priority for celebrity news"""
        news_item = {
            'title': 'Celebrity buys property',
            'category': 'real_estate',
            'score': 0.1,
            'is_celebrity_news': True
        }

        priority = categorizer.assign_priority(news_item)
        assert priority == 'high'

    def test_priority_assignment_high_value(self, categorizer):
        """Test high priority for high-value deals"""
        news_item = {
            'title': 'Big property deal',
            'category': 'real_estate',
            'score': 0.05,
            'is_celebrity_news': False,
            'celebrity_match': {
                'is_high_value': True
            }
        }

        priority = categorizer.assign_priority(news_item)
        assert priority == 'high'

    def test_priority_assignment_high_policy(self, categorizer):
        """Test high priority for policy news"""
        news_item = {
            'title': 'Policy update',
            'category': 'policy',
            'score': 0.15,
            'is_celebrity_news': False
        }

        priority = categorizer.assign_priority(news_item)
        assert priority == 'high'

    def test_priority_assignment_medium(self, categorizer):
        """Test medium priority assignment"""
        news_item = {
            'title': 'Infrastructure update',
            'category': 'infrastructure',
            'score': 0.08,
            'is_celebrity_news': False
        }

        priority = categorizer.assign_priority(news_item)
        assert priority == 'medium'

    def test_priority_assignment_low(self, categorizer):
        """Test low priority assignment"""
        news_item = {
            'title': 'Minor news',
            'category': 'uncategorized',
            'score': 0.01,
            'is_celebrity_news': False
        }

        priority = categorizer.assign_priority(news_item)
        assert priority == 'low'

    def test_process_items(self, categorizer):
        """Test processing multiple items"""
        news_items = [
            {
                'title': 'DLF new project',
                'content': 'Real estate news'
            },
            {
                'title': 'Metro line update',
                'content': 'Infrastructure news'
            },
            {
                'title': 'Random news',
                'content': 'No category match'
            }
        ]

        processed = categorizer.process_items(news_items)

        assert len(processed) == 3
        assert processed[0]['category'] == 'real_estate'
        assert processed[1]['category'] == 'infrastructure'
        assert processed[2]['category'] == 'uncategorized'

        # All items should have priority
        for item in processed:
            assert 'priority' in item

    def test_filter_by_category(self, categorizer):
        """Test filtering by category"""
        news_items = [
            {'category': 'real_estate', 'title': 'RE news'},
            {'category': 'infrastructure', 'title': 'Infra news'},
            {'category': 'policy', 'title': 'Policy news'},
            {'category': 'real_estate', 'title': 'More RE news'}
        ]

        filtered = categorizer.filter_by_category(news_items, ['real_estate'])

        assert len(filtered) == 2
        assert all(item['category'] == 'real_estate' for item in filtered)

    def test_filter_by_priority(self, categorizer):
        """Test filtering by minimum priority"""
        news_items = [
            {'category': 'real_estate', 'priority': 'high'},
            {'category': 'infrastructure', 'priority': 'medium'},
            {'category': 'policy', 'priority': 'low'},
            {'category': 'real_estate', 'priority': 'high'}
        ]

        # Filter for medium and above
        filtered = categorizer.filter_by_priority(news_items, 'medium')

        assert len(filtered) == 3
        assert all(item['priority'] in ['high', 'medium'] for item in filtered)

    def test_filter_by_priority_high_only(self, categorizer):
        """Test filtering for high priority only"""
        news_items = [
            {'category': 'real_estate', 'priority': 'high'},
            {'category': 'infrastructure', 'priority': 'medium'},
            {'category': 'policy', 'priority': 'low'}
        ]

        filtered = categorizer.filter_by_priority(news_items, 'high')

        assert len(filtered) == 1
        assert filtered[0]['priority'] == 'high'

    def test_nested_keyword_structure(self):
        """Test handling of nested keyword structures"""
        config = {
            "category1": {
                "sub1": ["keyword1", "keyword2"],
                "sub2": ["keyword3"]
            }
        }

        categorizer = Categorizer(config)
        
        # Should flatten nested structure
        assert "keyword1" in categorizer.category_keywords["category1"]
        assert "keyword2" in categorizer.category_keywords["category1"]
        assert "keyword3" in categorizer.category_keywords["category1"]

    def test_list_keyword_structure(self):
        """Test handling of flat list keyword structures"""
        config = {
            "category1": ["keyword1", "keyword2", "keyword3"]
        }

        categorizer = Categorizer(config)
        
        assert "keyword1" in categorizer.category_keywords["category1"]
        assert "keyword2" in categorizer.category_keywords["category1"]
