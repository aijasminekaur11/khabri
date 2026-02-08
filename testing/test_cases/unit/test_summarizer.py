"""
Unit Tests for Summarizer
Tests summary generation and key point extraction
"""

import pytest
from src.processors.summarizer import Summarizer


class TestSummarizer:
    """Test Summarizer functionality"""

    @pytest.fixture
    def summarizer(self):
        """Create a Summarizer instance"""
        return Summarizer(max_summary_length=200)

    def test_initialization(self, summarizer):
        """Test Summarizer initializes correctly"""
        assert summarizer.max_summary_length == 200

    def test_generate_summary_with_content(self, summarizer):
        """Test summary generation with content"""
        news_item = {
            'title': 'Mumbai property prices rise',
            'content': 'Property prices in Mumbai have risen by 5%. This is due to high demand. Experts predict continued growth in the coming quarters.'
        }

        summary = summarizer.generate_summary(news_item)

        assert summary is not None
        assert len(summary) <= 200
        assert len(summary) > 0
        assert 'Property prices' in summary or 'Mumbai' in summary

    def test_generate_summary_title_only(self, summarizer):
        """Test summary generation when only title is available"""
        news_item = {
            'title': 'Property market update',
            'content': ''
        }

        summary = summarizer.generate_summary(news_item)

        assert summary is not None
        assert 'Property market update' in summary

    def test_generate_summary_empty(self, summarizer):
        """Test summary generation with empty content"""
        news_item = {
            'title': '',
            'content': ''
        }

        summary = summarizer.generate_summary(news_item)

        assert summary == ""

    def test_generate_summary_truncation(self):
        """Test summary truncation for long content"""
        summarizer = Summarizer(max_summary_length=60)
        
        news_item = {
            'title': 'Long article',
            'content': 'This is a very long article with lots of content that should definitely be truncated because it exceeds the maximum allowed length of sixty characters by quite a significant margin.'
        }

        summary = summarizer.generate_summary(news_item)

        assert len(summary) <= 60
        assert summary.endswith('...')

    def test_clean_text(self, summarizer):
        """Test text cleaning"""
        text = "  This   has   extra   spaces  and  special#chars!  "
        cleaned = summarizer._clean_text(text)

        assert "  " not in cleaned
        assert cleaned.strip() == cleaned

    def test_extract_first_sentences(self, summarizer):
        """Test extracting first sentences"""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        
        result = summarizer._extract_first_sentences(text, max_sentences=2)

        assert "First sentence" in result
        assert "Second sentence" in result
        assert "Third sentence" not in result
        assert result.endswith('.')

    def test_extract_key_points_category(self, summarizer):
        """Test key points extraction with category"""
        news_item = {
            'title': 'Test news',
            'category': 'real_estate',
            'priority': 'high',
            'matched_keywords': ['property', 'mumbai']
        }

        key_points = summarizer.extract_key_points(news_item)

        assert any('Category' in kp for kp in key_points)
        assert any('Real Estate' in kp or 'real_estate' in kp for kp in key_points)

    def test_extract_key_points_celebrity(self, summarizer):
        """Test key points extraction with celebrity info"""
        news_item = {
            'title': 'Celebrity property deal',
            'category': 'real_estate',
            'is_celebrity_news': True,
            'celebrity_match': {
                'celebrity_name': 'Shah Rukh Khan',
                'property_value_cr': 50.0
            },
            'matched_keywords': ['property', 'luxury']
        }

        key_points = summarizer.extract_key_points(news_item)

        assert any('Celebrity' in kp for kp in key_points)
        assert any('Shah Rukh Khan' in kp for kp in key_points)
        assert any('₹50' in kp or '50' in kp for kp in key_points)

    def test_extract_key_points_keywords(self, summarizer):
        """Test key points extraction with matched keywords"""
        news_item = {
            'title': 'Test news',
            'category': 'real_estate',
            'matched_keywords': ['property', 'mumbai', 'dlf', 'luxury']
        }

        key_points = summarizer.extract_key_points(news_item)

        # Should include keywords key point
        keywords_point = [kp for kp in key_points if 'Keywords' in kp]
        assert len(keywords_point) > 0

    def test_extract_key_points_uncategorized(self, summarizer):
        """Test key points extraction for uncategorized item"""
        news_item = {
            'title': 'Test news',
            'category': 'uncategorized',
            'matched_keywords': []
        }

        key_points = summarizer.extract_key_points(news_item)

        # Should not include category for uncategorized
        assert not any('Category' in kp for kp in key_points)

    def test_generate_headline_from_title(self, summarizer):
        """Test headline generation from title"""
        news_item = {
            'title': 'Mumbai Property Market Update',
            'content': 'Content here'
        }

        headline = summarizer.generate_headline(news_item)

        assert headline == 'Mumbai Property Market Update'

    def test_generate_headline_truncate_long(self, summarizer):
        """Test headline truncation for long titles"""
        news_item = {
            'title': 'A' * 150,  # Very long title
            'content': 'Content'
        }

        headline = summarizer.generate_headline(news_item)

        assert len(headline) <= 100
        assert headline.endswith('...')

    def test_generate_headline_from_content(self, summarizer):
        """Test headline generation from content when no title"""
        news_item = {
            'title': '',
            'content': 'This is the first sentence. This is the second sentence.'
        }

        headline = summarizer.generate_headline(news_item)

        assert len(headline) > 0
        assert 'This is the first sentence' in headline

    def test_generate_headline_empty(self, summarizer):
        """Test headline generation with empty input"""
        news_item = {
            'title': '',
            'content': ''
        }

        headline = summarizer.generate_headline(news_item)

        assert headline == "Untitled News Item"

    def test_process_items(self, summarizer):
        """Test processing multiple items"""
        news_items = [
            {
                'title': 'News item 1',
                'content': 'Content for item 1. More content here.'
            },
            {
                'title': 'News item 2',
                'content': 'Content for item 2. Additional details.'
            }
        ]

        processed = summarizer.process_items(news_items)

        assert len(processed) == 2
        
        # All items should have summary, key_points, and headline
        for item in processed:
            assert 'summary' in item
            assert 'key_points' in item
            assert 'headline' in item
            assert isinstance(item['key_points'], list)

    def test_process_items_with_celebrity_data(self, summarizer):
        """Test processing items with celebrity information"""
        news_items = [
            {
                'title': 'Celebrity buys property',
                'content': 'A famous celebrity purchased a luxury home.',
                'category': 'real_estate',
                'is_celebrity_news': True,
                'celebrity_match': {
                    'celebrity_name': 'Test Celebrity',
                    'property_value_cr': 25.0
                },
                'matched_keywords': ['property', 'luxury']
            }
        ]

        processed = summarizer.process_items(news_items)

        assert len(processed) == 1
        item = processed[0]
        
        # Check key points include celebrity info
        assert any('Celebrity' in kp for kp in item['key_points'])
        assert any('Test Celebrity' in kp for kp in item['key_points'])

    def test_static_clean_text(self):
        """Test static text cleaning method"""
        text = "Text   with  extra   spaces\n\nand\ttabs"
        cleaned = Summarizer._clean_text(text)

        assert "  " not in cleaned
        assert "\n" not in cleaned
        assert "\t" not in cleaned

    def test_static_extract_key_points(self):
        """Test static key points extraction"""
        news_item = {
            'category': 'policy',
            'matched_keywords': ['RBI', 'interest rate']
        }

        key_points = Summarizer.extract_key_points(news_item)

        assert isinstance(key_points, list)
        assert len(key_points) > 0
