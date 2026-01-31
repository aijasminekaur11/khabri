"""
Test fixtures for scraper modules.

Provides mock HTML responses, RSS feeds, and configuration data for testing.
"""

import pytest


# HTML Fixtures

HTML_NEWS_ARTICLE = """
<html>
    <head>
        <title>Test News Site</title>
    </head>
    <body>
        <article>
            <h1 class="article-title">New Real Estate Development in Mumbai</h1>
            <div class="article-meta">
                <span class="author">John Doe</span>
                <time class="publish-date" datetime="2026-01-30">Jan 30, 2026</time>
            </div>
            <div class="article-content">
                <p>A major real estate development project has been announced in Mumbai...</p>
                <p>The project will include residential and commercial spaces.</p>
            </div>
            <a class="read-more" href="/articles/mumbai-development">Read more</a>
        </article>
    </body>
</html>
"""

HTML_COMPETITOR_HOMEPAGE = """
<html>
    <body>
        <div class="articles-list">
            <article class="article-card">
                <h2>Property Prices Soar in Bangalore</h2>
                <a href="/articles/bangalore-prices">Read</a>
                <time datetime="2026-01-30">Today</time>
            </article>
            <article class="article-card">
                <h2>New Infrastructure Projects Announced</h2>
                <a href="/articles/infrastructure">Read</a>
                <time datetime="2026-01-29">Yesterday</time>
            </article>
            <article class="article-card">
                <h2>Celebrity Invests in Real Estate</h2>
                <a href="/articles/celebrity-investment">Read</a>
                <time datetime="2026-01-29">Yesterday</time>
            </article>
        </div>
    </body>
</html>
"""

HTML_IGRS_DATA = """
<html>
    <head>
        <title>IGRS Maharashtra - Property Registration Data</title>
    </head>
    <body>
        <div class="data-container">
            <h1>Property Registration Statistics</h1>

            <div class="registration-entry">
                <span class="district">Mumbai</span>
                <span class="property-type">Residential</span>
                <span class="count">245</span>
                <span class="value">₹850 Crores</span>
                <span class="date">2026-01-30</span>
            </div>

            <div class="registration-entry">
                <span class="district">Pune</span>
                <span class="property-type">Residential</span>
                <span class="count">180</span>
                <span class="value">₹520 Crores</span>
                <span class="date">2026-01-30</span>
            </div>

            <div class="registration-entry">
                <span class="district">Mumbai</span>
                <span class="property-type">Commercial</span>
                <span class="count">89</span>
                <span class="value">₹420 Crores</span>
                <span class="date">2026-01-30</span>
            </div>

            <div class="registration-entry">
                <span class="district">Nashik</span>
                <span class="property-type">Residential</span>
                <span class="count">65</span>
                <span class="value">₹180 Crores</span>
                <span class="date">2026-01-30</span>
            </div>
        </div>
    </body>
</html>
"""


# RSS Feed Fixtures

RSS_FEED_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Real Estate News Feed</title>
        <link>https://example.com/feed</link>
        <description>Latest real estate news and updates</description>

        <item>
            <title>Housing Prices Rise in Major Cities</title>
            <link>https://example.com/articles/housing-prices</link>
            <description>Real estate prices have increased by 12% in major metros...</description>
            <author>Jane Smith</author>
            <pubDate>Thu, 30 Jan 2026 08:00:00 GMT</pubDate>
            <category>real-estate</category>
            <category>market-trends</category>
        </item>

        <item>
            <title>New Government Policy for Affordable Housing</title>
            <link>https://example.com/articles/govt-policy</link>
            <description>The government has announced new subsidies for affordable housing...</description>
            <author>Policy Desk</author>
            <pubDate>Wed, 29 Jan 2026 15:30:00 GMT</pubDate>
            <category>policy</category>
            <category>affordable-housing</category>
        </item>

        <item>
            <title>Infrastructure Development in Tier-2 Cities</title>
            <link>https://example.com/articles/infrastructure</link>
            <description>New metro and highway projects announced for tier-2 cities...</description>
            <pubDate>Wed, 29 Jan 2026 10:00:00 GMT</pubDate>
            <category>infrastructure</category>
        </item>
    </channel>
</rss>
"""


# Configuration Fixtures

@pytest.fixture
def sample_sources_config():
    """Sample sources configuration."""
    return [
        {
            'id': 'times_property',
            'name': 'Times Property',
            'url': 'https://timesproperty.com/news',
            'type': 'scrape',
            'category': 'real_estate',
            'enabled': True,
            'rate_limit_ms': 1000,
            'selectors': {
                'title': 'h1.article-title',
                'content': 'div.article-content',
                'date': 'time.publish-date',
                'link': 'a.read-more'
            }
        },
        {
            'id': 'housing_rss',
            'name': 'Housing.com RSS',
            'url': 'https://housing.com/news/feed',
            'type': 'rss',
            'category': 'real_estate',
            'enabled': True,
            'rate_limit_ms': 1000
        },
        {
            'id': 'competitor_99acres',
            'name': '99acres Blog',
            'url': 'https://99acres.com/blog',
            'type': 'scrape',
            'category': 'competitor',
            'enabled': True,
            'rate_limit_ms': 2000,
            'selectors': {
                'container': 'article.article-card',
                'title': 'h2',
                'link': 'a',
                'date': 'time'
            }
        },
        {
            'id': 'igrs_maharashtra',
            'name': 'IGRS Maharashtra',
            'url': 'https://igr.maharashtra.gov.in/statistics',
            'type': 'scrape',
            'category': 'infrastructure',
            'enabled': True,
            'rate_limit_ms': 3000,
            'selectors': {
                'container': '.registration-entry',
                'district': '.district',
                'property_type': '.property-type',
                'count': '.count',
                'value': '.value',
                'date': '.date'
            }
        }
    ]


@pytest.fixture
def sample_news_items():
    """Sample NewsItem dictionaries."""
    return [
        {
            'id': 'abc123',
            'title': 'Property Market Update',
            'url': 'https://example.com/article/1',
            'source': 'Test Source',
            'source_id': 'test_1',
            'category': 'real_estate',
            'content': 'Market overview content...',
            'published_at': '2026-01-30T08:00:00',
            'scraped_at': '2026-01-30T09:00:00',
            'author': 'John Doe',
            'image_url': None,
            'tags': ['market', 'update']
        },
        {
            'id': 'def456',
            'title': 'New Infrastructure Project',
            'url': 'https://example.com/article/2',
            'source': 'Test Source',
            'source_id': 'test_1',
            'category': 'infrastructure',
            'content': 'Infrastructure project details...',
            'published_at': '2026-01-29T15:00:00',
            'scraped_at': '2026-01-30T09:00:00',
            'author': None,
            'image_url': None,
            'tags': ['infrastructure']
        }
    ]
