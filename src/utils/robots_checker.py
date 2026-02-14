"""
Robots.txt Compliance Checker
Ensures web scraping respects robots.txt rules
"""

import logging
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)


class RobotsChecker:
    """
    Checks robots.txt compliance for web scraping
    Caches robots.txt to avoid repeated requests
    """
    
    def __init__(self, cache_duration: int = 3600):
        """
        Initialize robots checker
        
        Args:
            cache_duration: How long to cache robots.txt in seconds (default: 1 hour)
        """
        self.cache_duration = cache_duration
        self._cache: Dict[str, tuple] = {}  # url -> (robot_parser, timestamp)
        self._user_agent = "KhabriBot/1.0 (News Intelligence Bot)"
    
    def _get_robots_url(self, url: str) -> str:
        """Extract robots.txt URL from any URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    
    def _get_cached_parser(self, robots_url: str) -> Optional[RobotFileParser]:
        """Get cached robots parser if valid"""
        if robots_url in self._cache:
            parser, timestamp = self._cache[robots_url]
            if time.time() - timestamp < self.cache_duration:
                return parser
            else:
                # Cache expired
                del self._cache[robots_url]
        return None
    
    def can_fetch(self, url: str) -> bool:
        """
        Check if we can fetch a URL according to robots.txt
        
        Args:
            url: URL to check
            
        Returns:
            True if allowed to fetch, False otherwise
        """
        try:
            robots_url = self._get_robots_url(url)
            
            # Check cache first
            parser = self._get_cached_parser(robots_url)
            
            if parser is None:
                # Fetch and parse robots.txt
                parser = RobotFileParser()
                parser.set_url(robots_url)
                parser.read()
                
                # Cache it
                self._cache[robots_url] = (parser, time.time())
                logger.info(f"Cached robots.txt from {robots_url}")
            
            # Check if we can fetch
            can_fetch = parser.can_fetch(self._user_agent, url)
            
            if not can_fetch:
                logger.warning(f"robots.txt disallows fetching: {url}")
            
            return can_fetch
            
        except Exception as e:
            # If robots.txt can't be fetched, assume we can fetch
            # This is the conservative approach - some sites don't have robots.txt
            logger.debug(f"Could not check robots.txt for {url}: {e}")
            return True
    
    def get_crawl_delay(self, url: str) -> Optional[float]:
        """
        Get crawl-delay directive from robots.txt
        
        Args:
            url: URL to check
            
        Returns:
            Crawl delay in seconds, or None if not specified
        """
        try:
            robots_url = self._get_robots_url(url)
            parser = self._get_cached_parser(robots_url)
            
            if parser is None:
                parser = RobotFileParser()
                parser.set_url(robots_url)
                parser.read()
                self._cache[robots_url] = (parser, time.time())
            
            # Get crawl delay
            return parser.crawl_delay(self._user_agent)
            
        except Exception:
            return None
    
    def clear_cache(self):
        """Clear the robots.txt cache"""
        self._cache.clear()
        logger.info("Robots.txt cache cleared")


# Global instance for reuse
_robots_checker: Optional[RobotsChecker] = None


def get_robots_checker() -> RobotsChecker:
    """Get global robots checker instance"""
    global _robots_checker
    if _robots_checker is None:
        _robots_checker = RobotsChecker()
    return _robots_checker


def can_fetch(url: str) -> bool:
    """Convenience function to check if URL can be fetched"""
    return get_robots_checker().can_fetch(url)
