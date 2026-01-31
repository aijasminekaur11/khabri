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
        Validate sources.json configuration

        Args:
            config: Sources configuration dictionary

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check for required categories
        required_categories = ['real_estate', 'infrastructure', 'policy', 'celebrity', 'personal']

        for category in required_categories:
            if category not in config:
                errors.append(f"Missing required category: {category}")
                continue

            # Validate each source in the category
            if not isinstance(config[category], list):
                errors.append(f"Category '{category}' must be a list")
                continue

            for idx, source in enumerate(config[category]):
                if not isinstance(source, dict):
                    errors.append(f"{category}[{idx}]: Source must be a dictionary")
                    continue

                # Check required fields
                required_fields = ['name', 'url', 'type', 'enabled']
                for field in required_fields:
                    if field not in source:
                        errors.append(f"{category}[{idx}]: Missing required field '{field}'")

                # Validate type field
                if 'type' in source and source['type'] not in ['scrape', 'rss', 'api']:
                    errors.append(f"{category}[{idx}]: Invalid type '{source['type']}'. Must be 'scrape', 'rss', or 'api'")

        return errors

    @staticmethod
    def validate_keywords(config: Dict[str, Any]) -> List[str]:
        """
        Validate keywords.json configuration

        Args:
            config: Keywords configuration dictionary

        Returns:
            List of validation errors
        """
        errors = []

        # Check for required categories
        required_categories = ['real_estate', 'infrastructure', 'policy', 'cities']

        for category in required_categories:
            if category not in config:
                errors.append(f"Missing required category: {category}")

        return errors

    @staticmethod
    def validate_celebrities(config: Dict[str, Any]) -> List[str]:
        """
        Validate celebrities.json configuration

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

        # Validate each category
        for category_name, celebrities in config.items():
            if not isinstance(celebrities, list):
                errors.append(f"Category '{category_name}' must be a list")
                continue

            for idx, celeb in enumerate(celebrities):
                if not isinstance(celeb, dict):
                    errors.append(f"{category_name}[{idx}]: Celebrity must be a dictionary")
                    continue

                # Check required fields
                if 'name' not in celeb:
                    errors.append(f"{category_name}[{idx}]: Missing required field 'name'")

                # Validate aliases (optional but must be list if present)
                if 'aliases' in celeb and not isinstance(celeb['aliases'], list):
                    errors.append(f"{category_name}[{idx}]: 'aliases' must be a list")

                # Validate priority (optional but must be valid if present)
                if 'priority' in celeb and celeb['priority'] not in ['high', 'medium', 'low']:
                    errors.append(f"{category_name}[{idx}]: Invalid priority '{celeb['priority']}'")

        return errors

    @staticmethod
    def validate_events(config: Dict[str, Any]) -> List[str]:
        """
        Validate events.json configuration

        Args:
            config: Events configuration dictionary

        Returns:
            List of validation errors
        """
        errors = []

        if 'events' not in config:
            errors.append("Missing 'events' key in configuration")
            return errors

        if not isinstance(config['events'], list):
            errors.append("'events' must be a list")
            return errors

        for idx, event in enumerate(config['events']):
            if not isinstance(event, dict):
                errors.append(f"events[{idx}]: Event must be a dictionary")
                continue

            # Check required fields
            required_fields = ['id', 'name', 'date', 'start_time', 'end_time', 'active']
            for field in required_fields:
                if field not in event:
                    errors.append(f"events[{idx}]: Missing required field '{field}'")

            # Validate date format (YYYY-MM-DD)
            if 'date' in event:
                try:
                    datetime.strptime(event['date'], '%Y-%m-%d')
                except ValueError:
                    errors.append(f"events[{idx}]: Invalid date format. Expected YYYY-MM-DD")

            # Validate time format (HH:MM)
            for time_field in ['start_time', 'end_time']:
                if time_field in event:
                    try:
                        datetime.strptime(event[time_field], '%H:%M')
                    except ValueError:
                        errors.append(f"events[{idx}]: Invalid {time_field} format. Expected HH:MM")

        return errors

    @staticmethod
    def validate_interests(config: Dict[str, Any]) -> List[str]:
        """
        Validate interests.json configuration

        Args:
            config: Interests configuration dictionary

        Returns:
            List of validation errors
        """
        errors = []

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
        Validate schedules.json configuration

        Args:
            config: Schedules configuration dictionary

        Returns:
            List of validation errors
        """
        errors = []

        # Check for required sections
        if 'digests' not in config:
            errors.append("Missing 'digests' section")

        if 'digests' in config:
            # Check for morning and evening digests
            for digest_type in ['morning', 'evening']:
                if digest_type not in config['digests']:
                    errors.append(f"Missing '{digest_type}' digest configuration")
                else:
                    digest = config['digests'][digest_type]
                    required_fields = ['enabled', 'time', 'cron_utc']
                    for field in required_fields:
                        if field not in digest:
                            errors.append(f"{digest_type} digest: Missing required field '{field}'")

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
