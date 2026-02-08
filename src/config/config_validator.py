"""
Configuration Validator
Validates configuration files against expected schemas
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class ConfigValidator:
    """Validates configuration data structures"""

    @staticmethod
    def validate_sources(config: Dict[str, Any]) -> List[str]:
        """
        Validate sources.yaml configuration

        Args:
            config: Sources configuration dictionary

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check for required top-level keys (YAML structure)
        source_sections = ['news_sources', 'rss_feeds', 'competitors']
        
        for section in source_sections:
            if section not in config:
                # These are optional - config may not have all sections
                continue

            # Validate each source in the section
            if not isinstance(config[section], list):
                errors.append(f"Section '{section}' must be a list")
                continue

            for idx, source in enumerate(config[section]):
                if not isinstance(source, dict):
                    errors.append(f"{section}[{idx}]: Source must be a dictionary")
                    continue

                # Check required fields
                required_fields = ['name', 'url']
                for field in required_fields:
                    if field not in source:
                        errors.append(f"{section}[{idx}]: Missing required field '{field}'")

        return errors

    @staticmethod
    def validate_keywords(config: Dict[str, Any]) -> List[str]:
        """
        Validate keywords.yaml configuration

        Args:
            config: Keywords configuration dictionary

        Returns:
            List of validation errors
        """
        errors = []

        # Check for at least one keyword section (YAML structure is flexible)
        if not config:
            errors.append("Keywords config is empty")
            return errors

        # Validate that keyword sections are dictionaries or lists
        for section_name, section_data in config.items():
            if section_name == 'exclude_keywords':
                if not isinstance(section_data, list):
                    errors.append(f"'exclude_keywords' must be a list")
            elif isinstance(section_data, dict):
                # Nested categories like categories.market_updates
                for subcategory, keywords in section_data.items():
                    if not isinstance(keywords, list):
                        errors.append(f"'{section_name}.{subcategory}' must be a list of keywords")
            elif not isinstance(section_data, list):
                errors.append(f"'{section_name}' has invalid type")

        return errors

    @staticmethod
    def validate_celebrities(config: Dict[str, Any]) -> List[str]:
        """
        Validate celebrities.yaml configuration

        Args:
            config: Celebrities configuration dictionary

        Returns:
            List of validation errors
        """
        errors = []

        # Check for at least one category
        if not config:
            errors.append("Celebrities config is empty")
            return errors

        # Validate each category (YAML has nested structure like bollywood.a_list)
        for category_name, category_data in config.items():
            if isinstance(category_data, dict):
                # Nested structure like bollywood: {a_list: [], producers_directors: []}
                for subcategory, celebrities in category_data.items():
                    if not isinstance(celebrities, list):
                        errors.append(f"'{category_name}.{subcategory}' must be a list")
                        continue
                    
                    for idx, celeb in enumerate(celebrities):
                        if not isinstance(celeb, str):
                            errors.append(f"'{category_name}.{subcategory}[{idx}]' must be a celebrity name string")
            elif isinstance(category_data, list):
                # Simple list structure
                for idx, celeb in enumerate(category_data):
                    if not isinstance(celeb, str):
                        errors.append(f"'{category_name}[{idx}]' must be a celebrity name string")
            else:
                errors.append(f"Category '{category_name}' has invalid structure")

        return errors

    @staticmethod
    def validate_events(config: Dict[str, Any]) -> List[str]:
        """
        Validate events.yaml configuration

        Args:
            config: Events configuration dictionary

        Returns:
            List of validation errors
        """
        errors = []

        # Skip validation if config is empty or doesn't have expected keys
        # (events.yaml is optional and may not exist)
        if not config:
            return errors

        # Support both old structure and new schedules.yaml embedded structure
        events = config.get('events', config.get('event_based_schedules', []))
        
        if not events:
            return errors

        if not isinstance(events, list):
            errors.append("'events' must be a list")
            return errors

        for idx, event in enumerate(events):
            if not isinstance(event, dict):
                errors.append(f"events[{idx}]: Event must be a dictionary")
                continue

            required_fields = ['name', 'date']
            for field in required_fields:
                if field not in event:
                    errors.append(f"events[{idx}]: Missing required field '{field}'")

        return errors

    @staticmethod
    def validate_interests(config: Dict[str, Any]) -> List[str]:
        """
        Validate interests.yaml configuration

        Args:
            config: Interests configuration dictionary

        Returns:
            List of validation errors
        """
        errors = []

        # Skip validation if config is empty
        # (interests.yaml is optional and may not exist)
        if not config:
            return errors

        if 'personal_interests' not in config:
            errors.append("Missing 'personal_interests' key")
            return errors

        if not isinstance(config['personal_interests'], list):
            errors.append("'personal_interests' must be a list")
            return errors

        for idx, interest in enumerate(config['personal_interests']):
            if not isinstance(interest, dict):
                errors.append(f"personal_interests[{idx}]: Interest must be a dictionary")
                continue

            # Check required fields
            required_fields = ['id', 'name', 'keywords', 'active']
            for field in required_fields:
                if field not in interest:
                    errors.append(f"personal_interests[{idx}]: Missing required field '{field}'")

            # Validate keywords is a list
            if 'keywords' in interest and not isinstance(interest['keywords'], list):
                errors.append(f"personal_interests[{idx}]: 'keywords' must be a list")

        return errors

    @staticmethod
    def validate_schedules(config: Dict[str, Any]) -> List[str]:
        """
        Validate schedules.yaml configuration

        Args:
            config: Schedules configuration dictionary

        Returns:
            List of validation errors
        """
        errors = []

        # Skip validation if config is empty
        if not config:
            return errors

        # Check for digests section
        if 'digests' in config:
            # Validate digest configurations (morning, evening, etc.)
            for digest_name, digest in config['digests'].items():
                if not isinstance(digest, dict):
                    errors.append(f"digests.{digest_name}: Must be a dictionary")
                    continue
                    
                # Check for required fields in YAML structure
                # Note: 'time' is used instead of 'cron_utc' in YAML configs
                if 'enabled' not in digest:
                    errors.append(f"{digest_name} digest: Missing required field 'enabled'")
                if 'time' not in digest and 'cron_utc' not in digest:
                    errors.append(f"{digest_name} digest: Missing time field (expected 'time' or 'cron_utc')")

        # Check for realtime_alerts section
        if 'realtime_alerts' in config:
            alerts = config['realtime_alerts']
            if not isinstance(alerts, dict):
                errors.append("'realtime_alerts' must be a dictionary")
            else:
                if 'check_interval_minutes' not in alerts:
                    errors.append("realtime_alerts: Missing 'check_interval_minutes' field")

        # Validate events if present (embedded in schedules.yaml)
        if 'events' in config:
            events = config['events']
            if not isinstance(events, list):
                errors.append("'events' must be a list")
            else:
                for idx, event in enumerate(events):
                    if not isinstance(event, dict):
                        errors.append(f"events[{idx}]: Event must be a dictionary")
                        continue
                    if 'name' not in event:
                        errors.append(f"events[{idx}]: Missing required field 'name'")
                    if 'date' not in event:
                        errors.append(f"events[{idx}]: Missing required field 'date'")

        return errors

    @staticmethod
    def validate_all(configs: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Validate all configurations

        Args:
            configs: Dictionary of all configuration data

        Returns:
            Dictionary mapping config names to their validation errors
        """
        validation_results = {}

        validators = {
            'sources': ConfigValidator.validate_sources,
            'keywords': ConfigValidator.validate_keywords,
            'celebrities': ConfigValidator.validate_celebrities,
            'events': ConfigValidator.validate_events,
            'interests': ConfigValidator.validate_interests,
            'schedules': ConfigValidator.validate_schedules
        }

        for config_name, validator_func in validators.items():
            if config_name in configs:
                errors = validator_func(configs[config_name])
                if errors:
                    validation_results[config_name] = errors

        return validation_results
