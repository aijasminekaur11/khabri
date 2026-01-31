"""
Scrapers Module

This module contains all data collection scrapers for the Magic Bricks News Intelligence System.

Modules:
- news_scraper: General web scraping for news articles
- rss_reader: RSS feed parsing
- competitor_tracker: Competitor content monitoring
- igrs_scraper: IGRS-specific data scraping
"""

from .news_scraper import NewsScraper
from .rss_reader import RSSReader
from .competitor_tracker import CompetitorTracker
from .igrs_scraper import IGRSScraper

__all__ = [
    'NewsScraper',
    'RSSReader',
    'CompetitorTracker',
    'IGRSScraper'
]
