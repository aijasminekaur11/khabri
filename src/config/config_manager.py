"""
Configuration Manager
Main interface for accessing and managing all configurations
"""

from typing import Dict, Any, Optional, List
from .config_loader import ConfigLoader
from .config_validator import ConfigValidator


class ConfigManager:
    """
    Central configuration management interface
    Provides unified access to all configuration files with validation
    """

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize ConfigManager

        Args:
            config_dir: Path to configuration directory
        """
        self.loader = ConfigLoader(config_dir)
        self.validator = ConfigValidator()
        self._configs = {}
        self._validated = False

    def load_all_configs(self, validate: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Load all configuration files

        Args:
            validate: Whether to validate configs after loading

        Returns:
            Dictionary of all loaded configurations

        Raises:
            ValueError: If validation fails and validate=True
        """
        self._configs = self.loader.load_all()

        if validate:
            validation_errors = self.validator.validate_all(self._configs)
            if validation_errors:
                error_messages = []
                for config_name, errors in validation_errors.items():
                    error_messages.append(f"\n{config_name}:")
                    for error in errors:
                        error_messages.append(f"  - {error}")
                raise ValueError("Configuration validation failed:" + "".join(error_messages))

            self._validated = True

        return self._configs

    def get_sources(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get sources configuration

        Args:
            category: Optional category filter (real_estate, infrastructure, etc.)

        Returns:
            Sources configuration or specific category
        """
        if 'sources' not in self._configs:
            self._configs['sources'] = self.loader.load('sources')

        if category:
            return self._configs['sources'].get(category, [])

        return self._configs['sources']

    def get_keywords(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get keywords configuration

        Args:
            category: Optional category filter

        Returns:
            Keywords configuration or specific category
        """
        if 'keywords' not in self._configs:
            self._configs['keywords'] = self.loader.load('keywords')

        if category:
            return self._configs['keywords'].get(category, {})

        return self._configs['keywords']

    def get_celebrities(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get celebrities configuration

        Args:
            category: Optional category filter (bollywood, cricket, business)

        Returns:
            Celebrities list or specific category
        """
        if 'celebrities' not in self._configs:
            self._configs['celebrities'] = self.loader.load('celebrities')

        if category:
            return self._configs['celebrities'].get(category, [])

        return self._configs['celebrities']

    def get_events(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get events configuration

        Args:
            active_only: If True, return only active events

        Returns:
            List of events
        """
        if 'events' not in self._configs:
            self._configs['events'] = self.loader.load('events')

        events = self._configs['events'].get('events', [])

        if active_only:
            return [e for e in events if e.get('active', False)]

        return events

    def get_interests(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get personal interests configuration

        Args:
            active_only: If True, return only active interests

        Returns:
            List of personal interests
        """
        if 'interests' not in self._configs:
            self._configs['interests'] = self.loader.load('interests')

        interests = self._configs['interests'].get('personal_interests', [])

        if active_only:
            return [i for i in interests if i.get('active', False)]

        return interests

    def get_schedules(self) -> Dict[str, Any]:
        """
        Get schedules configuration

        Returns:
            Schedules configuration
        """
        if 'schedules' not in self._configs:
            self._configs['schedules'] = self.loader.load('schedules')

        return self._configs['schedules']

    def get_digest_schedule(self, digest_type: str) -> Optional[Dict[str, Any]]:
        """
        Get specific digest schedule

        Args:
            digest_type: Type of digest (morning or evening)

        Returns:
            Digest schedule configuration or None
        """
        schedules = self.get_schedules()
        return schedules.get('digests', {}).get(digest_type)

    def is_digest_enabled(self, digest_type: str) -> bool:
        """
        Check if a digest is enabled

        Args:
            digest_type: Type of digest (morning or evening)

        Returns:
            True if enabled, False otherwise
        """
        digest = self.get_digest_schedule(digest_type)
        return digest.get('enabled', False) if digest else False

    def reload_config(self, config_name: str):
        """
        Reload a specific configuration file

        Args:
            config_name: Name of config to reload
        """
        self._configs[config_name] = self.loader.reload(config_name)
        self._validated = False

    def reload_all(self):
        """Reload all configuration files"""
        self.loader.clear_cache()
        self.load_all_configs(validate=True)

    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all configurations

        Returns:
            Dictionary of all configurations
        """
        if not self._configs:
            self.load_all_configs()

        return self._configs

    def is_validated(self) -> bool:
        """
        Check if configurations have been validated

        Returns:
            True if validated, False otherwise
        """
        return self._validated
