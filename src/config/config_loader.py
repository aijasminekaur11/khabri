"""
Configuration Loader
Handles loading YAML configuration files from the config/ directory
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class ConfigLoader:
    """Loads configuration files from the config directory"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize ConfigLoader

        Args:
            config_dir: Path to configuration directory. If None, uses default ./config/
        """
        if config_dir is None:
            # Default to config/ directory in project root
            project_root = Path(__file__).parent.parent.parent
            self.config_dir = project_root / "config"
        else:
            self.config_dir = Path(config_dir)

        self._cache = {}
        self._last_loaded = {}

    def load(self, config_name: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Load a configuration file

        Args:
            config_name: Name of the config file (without .yaml extension)
            use_cache: Whether to use cached version if available

        Returns:
            Dictionary containing configuration data

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file has invalid YAML
        """
        config_path = self.config_dir / f"{config_name}.yaml"

        # Check cache if enabled
        if use_cache and config_name in self._cache:
            return self._cache[config_name]

        # Load from file
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}

        # Update cache
        self._cache[config_name] = config_data
        self._last_loaded[config_name] = datetime.now()

        return config_data

    def load_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all configuration files from the config directory

        Returns:
            Dictionary mapping config names to their data
        """
        all_configs = {}

        # Config files that exist as YAML
        yaml_files = [
            'sources',
            'keywords',
            'celebrities',
            'schedules'
        ]
        
        # Optional config files (may not exist)
        optional_files = [
            'events',
            'interests'
        ]

        for config_name in yaml_files:
            try:
                all_configs[config_name] = self.load(config_name)
            except FileNotFoundError:
                # Config file doesn't exist - return empty dict
                all_configs[config_name] = {}
            except yaml.YAMLError as e:
                # Invalid YAML - re-raise with more context
                raise ValueError(f"Invalid YAML in {config_name}.yaml: {str(e)}")
        
        # Load optional files if they exist
        for config_name in optional_files:
            try:
                all_configs[config_name] = self.load(config_name)
            except FileNotFoundError:
                # Optional config doesn't exist - return empty dict
                all_configs[config_name] = {}

        return all_configs

    def reload(self, config_name: str) -> Dict[str, Any]:
        """
        Force reload a configuration file (ignoring cache)

        Args:
            config_name: Name of the config file

        Returns:
            Reloaded configuration data
        """
        return self.load(config_name, use_cache=False)

    def clear_cache(self):
        """Clear all cached configurations"""
        self._cache.clear()
        self._last_loaded.clear()

    def get_last_loaded_time(self, config_name: str) -> Optional[datetime]:
        """
        Get the last time a config was loaded

        Args:
            config_name: Name of the config file

        Returns:
            Datetime of last load, or None if never loaded
        """
        return self._last_loaded.get(config_name)
