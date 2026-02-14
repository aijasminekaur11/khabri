"""
IGRS Scraper

Scrapes IGRS (Integrated Grievance Redressal System / Inspector General of Registration and Stamps)
data for real estate transaction insights and market intelligence.
"""

import hashlib
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

from src.config import ConfigManager
from src.utils import can_fetch

logger = logging.getLogger(__name__)


class IGRSScraper:
    """
    Specialized scraper for IGRS government data sources.
    Extracts property registration data and transaction trends.
    """

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize the IGRS scraper.

        Args:
            config_manager: ConfigManager instance. If None, creates a new one.
        """
        self.config = config_manager or ConfigManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MagicBricks-IGRSBot/1.0 (Real Estate Data Analysis)'
        })
        self.last_request_time = {}

    def close(self):
        """Close the requests session to free resources."""
        if self.session:
            self.session.close()
            logger.debug("IGRSScraper session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures session is closed."""
        self.close()
        return False

    def _generate_id(self, url: str) -> str:
        """Generate unique ID from URL using hash."""
        return hashlib.md5(url.encode()).hexdigest()

    def _respect_rate_limit(self, source_id: str, rate_limit_ms: int):
        """
        Enforce rate limiting for a specific source.

        Args:
            source_id: The source identifier
            rate_limit_ms: Minimum milliseconds between requests
        """
        if source_id in self.last_request_time:
            elapsed = (time.time() - self.last_request_time[source_id]) * 1000
            if elapsed < rate_limit_ms:
                sleep_time = (rate_limit_ms - elapsed) / 1000
                time.sleep(sleep_time)

        self.last_request_time[source_id] = time.time()

    def _parse_registration_data(self, html: str, selectors: Dict[str, str]) -> List[Dict]:
        """
        Parse property registration data from IGRS pages.

        Args:
            html: Raw HTML content
            selectors: CSS selectors for data extraction

        Returns:
            List of parsed registration records
        """
        soup = BeautifulSoup(html, 'html.parser')
        records = []

        # Find all registration entries
        entry_elements = soup.select(selectors.get('container', '.registration-entry'))

        for element in entry_elements:
            district_el = element.select_one(selectors.get('district', '.district'))
            property_type_el = element.select_one(selectors.get('property_type', '.property-type'))
            count_el = element.select_one(selectors.get('count', '.count'))
            value_el = element.select_one(selectors.get('value', '.value'))
            date_el = element.select_one(selectors.get('date', '.date'))

            if district_el:
                record = {
                    'district': district_el.get_text(strip=True),
                    'property_type': property_type_el.get_text(strip=True) if property_type_el else 'Unknown',
                    'registration_count': count_el.get_text(strip=True) if count_el else '0',
                    'total_value': value_el.get_text(strip=True) if value_el else '0',
                    'date': date_el.get_text(strip=True) if date_el else None
                }
                records.append(record)

        return records

    def _convert_to_news_item(self, record: Dict, source: Dict) -> Dict:
        """
        Convert IGRS registration data to NewsItem format.

        Args:
            record: Registration record
            source: Source configuration

        Returns:
            NewsItem dictionary
        """
        # Create a descriptive title
        title = f"IGRS: {record['registration_count']} {record['property_type']} registrations in {record['district']}"

        # Create content summary
        content = (
            f"Property registrations in {record['district']}: "
            f"{record['registration_count']} units of {record['property_type']} "
            f"with total value of {record['total_value']}."
        )

        # Generate URL (may be same as source URL)
        url = f"{source['url']}#{record['district']}"

        district = record.get('district') or ''
        district_tag = district.lower() if isinstance(district, str) and district else ''

        news_item = {
            'id': self._generate_id('|'.join([url, str(record.get('district', '')), str(record.get('property_type', '')), str(record.get('date', ''))])),
            'title': title,
            'url': url,
            'source': source.get('name', 'IGRS'),
            'source_id': source['id'],
            'category': 'infrastructure',
            'content': content,
            'published_at': datetime.now(),  # TODO: Parse from record['date']
            'scraped_at': datetime.now(),
            'author': 'IGRS Data',
            'image_url': None,
            'tags': ['igrs', 'property-registration'] + ([district_tag] if district_tag else [])
        }

        return news_item

    def scrape_igrs_source(self, source: Dict) -> List[Dict]:
        """
        Scrape a single IGRS data source.

        Args:
            source: Source configuration dictionary

        Returns:
            List of NewsItem dictionaries
        """
        if not source.get('enabled', False):
            return []

        # Check if this is an IGRS source (by ID or category)
        if 'igrs' not in source.get('id', '').lower():
            return []

        source_id = source['id']
        url = source['url']
        rate_limit = source.get('rate_limit_ms', 3000)  # Be polite to govt sites
        selectors = source.get('selectors', {})

        # Check robots.txt compliance
        if not can_fetch(url):
            logger.warning(f"robots.txt disallows IGRS scraping {source_id}: {url}")
            return []

        # Respect rate limiting
        self._respect_rate_limit(source_id, rate_limit)

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            # Parse registration data
            records = self._parse_registration_data(response.text, selectors)

            # Convert to NewsItem format
            news_items = []
            for record in records:
                news_item = self._convert_to_news_item(record, source)
                news_items.append(news_item)

            return news_items

        except requests.RequestException as e:
            logger.error(f"Error scraping IGRS source {source_id} ({url}): {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error scraping IGRS source {source_id}: {e}")
            return []

    def scrape_all_igrs(self) -> List[Dict]:
        """
        Scrape all IGRS sources from configuration.

        Returns:
            List of all NewsItem dictionaries from IGRS sources
        """
        sources = self.config.get_sources()
        all_items = []

        for source in sources:
            if 'igrs' in source.get('id', '').lower():
                items = self.scrape_igrs_source(source)
                all_items.extend(items)

        return all_items

    def get_district_summary(self, district: str) -> Optional[Dict]:
        """
        Get registration summary for a specific district.

        Args:
            district: District name

        Returns:
            Summary dictionary or None if not found
        """
        all_items = self.scrape_all_igrs()

        district_items = [
            item for item in all_items
            if district.lower() in item.get('title', '').lower()
        ]

        if not district_items:
            return None

        return {
            'district': district,
            'total_items': len(district_items),
            'items': district_items,
            'latest_update': max(item['scraped_at'] for item in district_items)
        }
