"""
Processing Pipeline Module
Handles deduplication, categorization, celebrity matching, and summarization
"""

from .deduplicator import Deduplicator
from .categorizer import Categorizer
from .celebrity_matcher import CelebrityMatcher
from .summarizer import Summarizer
from .processor_pipeline import ProcessorPipeline

__all__ = [
    'Deduplicator',
    'Categorizer',
    'CelebrityMatcher',
    'Summarizer',
    'ProcessorPipeline'
]
