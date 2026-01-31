"""
Unit Tests for ConfigManager
Tests configuration loading, validation, and access methods
"""

import pytest
import json
import tempfile
from pathlib import Path
from src.config import ConfigManager, ConfigLoader, ConfigValidator


class TestConfigLoader:
    """Test ConfigLoader functionality"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory with test files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create test sources.json
            sources = {
                "real_estate": [
                    {
                        "name": "Test Source",
                        "url": "https://test.com",
                        "type": "scrape",
                        "enabled": True
                    }
                ]
            }
            with open(config_dir / "sources.json", 'w') as f:
                json.dump(sources, f)

            # Create test keywords.json
            keywords = {
                "real_estate": {
                    "primary": ["property", "real estate"]
                }
            }
            with open(config_dir / "keywords.json", 'w') as f:
                json.dump(keywords, f)

            yield config_dir

    def test_load_config_file(self, temp_config_dir):
        """Test loading a single config file"""
        loader = ConfigLoader(str(temp_config_dir))
        sources = loader.load('sources')

        assert sources is not None
        assert 'real_estate' in sources
        assert len(sources['real_estate']) == 1

    def test_load_missing_file(self, temp_config_dir):
        """Test loading non-existent config file"""
        loader = ConfigLoader(str(temp_config_dir))

        with pytest.raises(FileNotFoundError):
            loader.load('nonexistent')

    def test_cache_mechanism(self, temp_config_dir):
        """Test that caching works correctly"""
        loader = ConfigLoader(str(temp_config_dir))

        # Load first time
        sources1 = loader.load('sources')

        # Load with cache
        sources2 = loader.load('sources', use_cache=True)

        # Should be same object (cached)
        assert sources1 is sources2

    def test_reload_clears_cache(self, temp_config_dir):
        """Test that reload bypasses cache"""
        loader = ConfigLoader(str(temp_config_dir))

        sources1 = loader.load('sources')
        sources2 = loader.reload('sources')

        # Different objects (reloaded)
        assert sources1 is not sources2

    def test_clear_cache(self, temp_config_dir):
        """Test cache clearing"""
        loader = ConfigLoader(str(temp_config_dir))

        loader.load('sources')
        assert 'sources' in loader._cache

        loader.clear_cache()
        assert 'sources' not in loader._cache


class TestConfigValidator:
    """Test ConfigValidator functionality"""

    def test_validate_sources_success(self):
        """Test successful sources validation"""
        valid_config = {
            "real_estate": [
                {
                    "name": "Test",
                    "url": "https://test.com",
                    "type": "scrape",
                    "enabled": True
                }
            ],
            "infrastructure": [],
            "policy": [],
            "celebrity": [],
            "personal": []
        }

        errors = ConfigValidator.validate_sources(valid_config)
        assert len(errors) == 0

    def test_validate_sources_missing_category(self):
        """Test validation with missing category"""
        invalid_config = {
            "real_estate": []
        }

        errors = ConfigValidator.validate_sources(invalid_config)
        assert len(errors) > 0
        assert any('infrastructure' in err for err in errors)

    def test_validate_sources_invalid_type(self):
        """Test validation with invalid source type"""
        invalid_config = {
            "real_estate": [
                {
                    "name": "Test",
                    "url": "https://test.com",
                    "type": "invalid_type",
                    "enabled": True
                }
            ],
            "infrastructure": [],
            "policy": [],
            "celebrity": [],
            "personal": []
        }

        errors = ConfigValidator.validate_sources(invalid_config)
        assert len(errors) > 0
        assert any('Invalid type' in err for err in errors)

    def test_validate_celebrities(self):
        """Test celebrity validation"""
        valid_config = {
            "bollywood": [
                {
                    "name": "Test Celebrity",
                    "aliases": ["TC"],
                    "priority": "high"
                }
            ]
        }

        errors = ConfigValidator.validate_celebrities(valid_config)
        assert len(errors) == 0

    def test_validate_events(self):
        """Test events validation"""
        valid_config = {
            "events": [
                {
                    "id": "test-event",
                    "name": "Test Event",
                    "date": "2026-02-01",
                    "start_time": "10:00",
                    "end_time": "18:00",
                    "active": True
                }
            ]
        }

        errors = ConfigValidator.validate_events(valid_config)
        assert len(errors) == 0


class TestConfigValidatorEdgeCases:
    """Test ConfigValidator edge cases and error paths"""

    # ===== SOURCES VALIDATION EDGE CASES =====

    def test_validate_sources_category_not_list(self):
        """Test sources validation when category is not a list"""
        invalid_config = {
            "real_estate": "not a list",
            "infrastructure": [],
            "policy": [],
            "celebrity": [],
            "personal": []
        }

        errors = ConfigValidator.validate_sources(invalid_config)
        assert len(errors) > 0
        assert any("must be a list" in err for err in errors)

    def test_validate_sources_source_not_dict(self):
        """Test sources validation when source is not a dictionary"""
        invalid_config = {
            "real_estate": ["not a dict"],
            "infrastructure": [],
            "policy": [],
            "celebrity": [],
            "personal": []
        }

        errors = ConfigValidator.validate_sources(invalid_config)
        assert len(errors) > 0
        assert any("must be a dictionary" in err for err in errors)

    def test_validate_sources_missing_required_fields(self):
        """Test sources validation with missing required fields"""
        invalid_config = {
            "real_estate": [
                {
                    "name": "Test"
                    # Missing: url, type, enabled
                }
            ],
            "infrastructure": [],
            "policy": [],
            "celebrity": [],
            "personal": []
        }

        errors = ConfigValidator.validate_sources(invalid_config)
        assert len(errors) >= 3  # url, type, enabled
        assert any("url" in err for err in errors)
        assert any("type" in err for err in errors)
        assert any("enabled" in err for err in errors)

    def test_validate_sources_all_valid_types(self):
        """Test sources validation accepts all valid types"""
        valid_config = {
            "real_estate": [
                {"name": "S1", "url": "http://t1.com", "type": "scrape", "enabled": True},
                {"name": "S2", "url": "http://t2.com", "type": "rss", "enabled": True},
                {"name": "S3", "url": "http://t3.com", "type": "api", "enabled": True}
            ],
            "infrastructure": [],
            "policy": [],
            "celebrity": [],
            "personal": []
        }

        errors = ConfigValidator.validate_sources(valid_config)
        assert len(errors) == 0

    def test_validate_sources_multiple_categories_with_errors(self):
        """Test validation errors from multiple categories"""
        invalid_config = {
            "real_estate": [
                {"name": "Test1"}  # Missing fields
            ],
            "infrastructure": "not a list",  # Wrong type
            "policy": [],
            "celebrity": [],
            "personal": []
        }

        errors = ConfigValidator.validate_sources(invalid_config)
        assert len(errors) > 0
        # Should have errors from both real_estate and infrastructure

    # ===== KEYWORDS VALIDATION EDGE CASES =====

    def test_validate_keywords_all_categories_missing(self):
        """Test keywords validation with all categories missing"""
        invalid_config = {}

        errors = ConfigValidator.validate_keywords(invalid_config)
        assert len(errors) == 4  # All 4 required categories

    def test_validate_keywords_partial_categories(self):
        """Test keywords validation with some categories missing"""
        partial_config = {
            "real_estate": {"primary": []},
            "infrastructure": {"primary": []}
            # Missing: policy, cities
        }

        errors = ConfigValidator.validate_keywords(partial_config)
        assert len(errors) == 2
        assert any("policy" in err for err in errors)
        assert any("cities" in err for err in errors)

    # ===== CELEBRITIES VALIDATION EDGE CASES =====

    def test_validate_celebrities_category_not_list(self):
        """Test celebrities validation when category is not list"""
        invalid_config = {
            "bollywood": "not a list"
        }

        errors = ConfigValidator.validate_celebrities(invalid_config)
        assert len(errors) > 0
        assert any("must be a list" in err for err in errors)

    def test_validate_celebrities_celeb_not_dict(self):
        """Test celebrities validation when celebrity is not dict"""
        invalid_config = {
            "bollywood": ["not a dict"]
        }

        errors = ConfigValidator.validate_celebrities(invalid_config)
        assert len(errors) > 0
        assert any("must be a dictionary" in err for err in errors)

    def test_validate_celebrities_missing_name(self):
        """Test celebrities validation with missing name field"""
        invalid_config = {
            "bollywood": [
                {
                    "aliases": ["SRK"]
                    # Missing: name
                }
            ]
        }

        errors = ConfigValidator.validate_celebrities(invalid_config)
        assert len(errors) > 0
        assert any("name" in err for err in errors)

    def test_validate_celebrities_aliases_not_list(self):
        """Test celebrities validation when aliases is not list"""
        invalid_config = {
            "bollywood": [
                {
                    "name": "Test",
                    "aliases": "not a list"
                }
            ]
        }

        errors = ConfigValidator.validate_celebrities(invalid_config)
        assert len(errors) > 0
        assert any("aliases" in err and "must be a list" in err for err in errors)

    def test_validate_celebrities_invalid_priority(self):
        """Test celebrities validation with invalid priority"""
        invalid_config = {
            "bollywood": [
                {
                    "name": "Test",
                    "priority": "critical"  # Not high/medium/low
                }
            ]
        }

        errors = ConfigValidator.validate_celebrities(invalid_config)
        assert len(errors) > 0
        assert any("Invalid priority" in err for err in errors)

    def test_validate_celebrities_valid_all_priorities(self):
        """Test celebrities validation accepts all valid priorities"""
        valid_config = {
            "bollywood": [
                {"name": "C1", "priority": "high"},
                {"name": "C2", "priority": "medium"},
                {"name": "C3", "priority": "low"}
            ]
        }

        errors = ConfigValidator.validate_celebrities(valid_config)
        assert len(errors) == 0

    # ===== EVENTS VALIDATION EDGE CASES =====

    def test_validate_events_missing_events_key(self):
        """Test events validation with missing 'events' key"""
        invalid_config = {}

        errors = ConfigValidator.validate_events(invalid_config)
        assert len(errors) > 0
        assert any("Missing 'events'" in err for err in errors)

    def test_validate_events_not_list(self):
        """Test events validation when 'events' is not a list"""
        invalid_config = {
            "events": "not a list"
        }

        errors = ConfigValidator.validate_events(invalid_config)
        assert len(errors) > 0
        assert any("must be a list" in err for err in errors)

    def test_validate_events_event_not_dict(self):
        """Test events validation when event is not dict"""
        invalid_config = {
            "events": ["not a dict"]
        }

        errors = ConfigValidator.validate_events(invalid_config)
        assert len(errors) > 0
        assert any("must be a dictionary" in err for err in errors)

    def test_validate_events_missing_all_fields(self):
        """Test events validation with all required fields missing"""
        invalid_config = {
            "events": [{}]
        }

        errors = ConfigValidator.validate_events(invalid_config)
        assert len(errors) >= 6  # All 6 required fields

    def test_validate_events_invalid_date_format(self):
        """Test events validation with invalid date format"""
        invalid_config = {
            "events": [
                {
                    "id": "test",
                    "name": "Test",
                    "date": "2026/01/30",  # Wrong format
                    "start_time": "10:00",
                    "end_time": "18:00",
                    "active": True
                }
            ]
        }

        errors = ConfigValidator.validate_events(invalid_config)
        assert len(errors) > 0
        assert any("Invalid date format" in err for err in errors)

    def test_validate_events_invalid_time_format(self):
        """Test events validation with invalid time format"""
        invalid_config = {
            "events": [
                {
                    "id": "test",
                    "name": "Test",
                    "date": "2026-01-30",
                    "start_time": "10AM",  # Wrong format
                    "end_time": "6:00 PM",  # Wrong format
                    "active": True
                }
            ]
        }

        errors = ConfigValidator.validate_events(invalid_config)
        assert len(errors) >= 2  # Both time fields
        assert any("start_time" in err for err in errors)
        assert any("end_time" in err for err in errors)

    # ===== INTERESTS VALIDATION EDGE CASES =====

    def test_validate_interests_missing_key(self):
        """Test interests validation with missing personal_interests key"""
        invalid_config = {}

        errors = ConfigValidator.validate_interests(invalid_config)
        assert len(errors) > 0
        assert any("personal_interests" in err for err in errors)

    def test_validate_interests_not_list(self):
        """Test interests validation when personal_interests is not list"""
        invalid_config = {
            "personal_interests": "not a list"
        }

        errors = ConfigValidator.validate_interests(invalid_config)
        assert len(errors) > 0
        assert any("must be a list" in err for err in errors)

    def test_validate_interests_interest_not_dict(self):
        """Test interests validation when interest is not dict"""
        invalid_config = {
            "personal_interests": ["not a dict"]
        }

        errors = ConfigValidator.validate_interests(invalid_config)
        assert len(errors) > 0
        assert any("must be a dictionary" in err for err in errors)

    def test_validate_interests_missing_required_fields(self):
        """Test interests validation with missing required fields"""
        invalid_config = {
            "personal_interests": [{}]
        }

        errors = ConfigValidator.validate_interests(invalid_config)
        assert len(errors) >= 4  # id, name, keywords, active

    def test_validate_interests_keywords_not_list(self):
        """Test interests validation when keywords is not list"""
        invalid_config = {
            "personal_interests": [
                {
                    "id": "test",
                    "name": "Test",
                    "keywords": "not a list",
                    "active": True
                }
            ]
        }

        errors = ConfigValidator.validate_interests(invalid_config)
        assert len(errors) > 0
        assert any("keywords" in err and "must be a list" in err for err in errors)

    # ===== SCHEDULES VALIDATION EDGE CASES =====

    def test_validate_schedules_missing_digests(self):
        """Test schedules validation with missing digests section"""
        invalid_config = {}

        errors = ConfigValidator.validate_schedules(invalid_config)
        assert len(errors) > 0
        assert any("digests" in err for err in errors)

    def test_validate_schedules_missing_morning_digest(self):
        """Test schedules validation with missing morning digest"""
        invalid_config = {
            "digests": {
                "evening": {"enabled": True, "time": "16:00", "cron_utc": "30 10 * * *"}
            }
        }

        errors = ConfigValidator.validate_schedules(invalid_config)
        assert len(errors) > 0
        assert any("morning" in err for err in errors)

    def test_validate_schedules_missing_evening_digest(self):
        """Test schedules validation with missing evening digest"""
        invalid_config = {
            "digests": {
                "morning": {"enabled": True, "time": "07:00", "cron_utc": "30 1 * * *"}
            }
        }

        errors = ConfigValidator.validate_schedules(invalid_config)
        assert len(errors) > 0
        assert any("evening" in err for err in errors)

    def test_validate_schedules_missing_digest_fields(self):
        """Test schedules validation with missing digest fields"""
        invalid_config = {
            "digests": {
                "morning": {},
                "evening": {}
            }
        }

        errors = ConfigValidator.validate_schedules(invalid_config)
        assert len(errors) >= 6  # 3 fields x 2 digests

    # ===== VALIDATE_ALL EDGE CASES =====

    def test_validate_all_with_multiple_errors(self):
        """Test validate_all collects errors from multiple configs"""
        configs = {
            "sources": {},  # Missing all categories
            "keywords": {},  # Missing all categories
            "celebrities": {},  # Empty config
            "events": {},  # Missing events key
            "interests": {},  # Missing personal_interests key
            "schedules": {}  # Missing digests
        }

        results = ConfigValidator.validate_all(configs)

        # Should have errors for all configs
        assert len(results) == 6
        assert 'sources' in results
        assert 'keywords' in results
        assert 'celebrities' in results
        assert 'events' in results
        assert 'interests' in results
        assert 'schedules' in results

    def test_validate_all_with_valid_configs(self):
        """Test validate_all returns empty dict for valid configs"""
        valid_configs = {
            "sources": {
                "real_estate": [],
                "infrastructure": [],
                "policy": [],
                "celebrity": [],
                "personal": []
            },
            "keywords": {
                "real_estate": {},
                "infrastructure": {},
                "policy": {},
                "cities": {}
            },
            "celebrities": {
                "bollywood": []
            },
            "events": {
                "events": []
            },
            "interests": {
                "personal_interests": []
            },
            "schedules": {
                "digests": {
                    "morning": {"enabled": True, "time": "07:00", "cron_utc": "30 1 * * *"},
                    "evening": {"enabled": True, "time": "16:00", "cron_utc": "30 10 * * *"}
                }
            }
        }

        results = ConfigValidator.validate_all(valid_configs)
        assert len(results) == 0  # No errors

    def test_validate_all_missing_some_configs(self):
        """Test validate_all handles missing configs gracefully"""
        partial_configs = {
            "sources": {
                "real_estate": [],
                "infrastructure": [],
                "policy": [],
                "celebrity": [],
                "personal": []
            }
            # Other configs missing
        }

        # Should not crash, just skip validation for missing configs
        results = ConfigValidator.validate_all(partial_configs)
        # Only sources should be validated (and it's valid)
        assert len(results) == 0


class TestConfigManager:
    """Test ConfigManager functionality"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create minimal valid configs that pass validation
            configs = {
                "sources": {
                    "real_estate": [],
                    "infrastructure": [],
                    "policy": [],
                    "celebrity": [],
                    "personal": []
                },
                "keywords": {
                    "real_estate": {"primary": []},
                    "infrastructure": {"primary": []},
                    "policy": {"primary": []},
                    "cities": {"tier1": []}
                },
                "celebrities": {
                    "bollywood": []
                },
                "events": {"events": []},
                "interests": {"personal_interests": []},
                "schedules": {
                    "timezone": "Asia/Kolkata",
                    "digests": {
                        "morning": {"enabled": True, "time": "07:00", "cron_utc": "30 1 * * *"},
                        "evening": {"enabled": True, "time": "16:00", "cron_utc": "30 10 * * *"}
                    }
                }
            }

            for name, data in configs.items():
                with open(config_dir / f"{name}.json", 'w') as f:
                    json.dump(data, f)

            yield config_dir

    def test_load_all_configs(self, temp_config_dir):
        """Test loading all configurations"""
        manager = ConfigManager(str(temp_config_dir))
        all_configs = manager.load_all_configs()

        assert 'sources' in all_configs
        assert 'keywords' in all_configs
        assert 'celebrities' in all_configs
        assert 'events' in all_configs
        assert 'interests' in all_configs
        assert 'schedules' in all_configs

    def test_get_sources(self, temp_config_dir):
        """Test get_sources method"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs()

        sources = manager.get_sources()
        assert sources is not None
        assert 'real_estate' in sources

    def test_get_events_active_only(self, temp_config_dir):
        """Test getting only active events"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs()

        active_events = manager.get_events(active_only=True)
        assert isinstance(active_events, list)

    def test_is_digest_enabled(self, temp_config_dir):
        """Test checking if digest is enabled"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs()

        assert manager.is_digest_enabled('morning') is True
        assert manager.is_digest_enabled('evening') is True

    def test_reload_config(self, temp_config_dir):
        """Test reloading specific config"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs()

        # Reload sources
        manager.reload_config('sources')

        # Should still be accessible
        sources = manager.get_sources()
        assert sources is not None


class TestConfigManagerErrorPaths:
    """Test ConfigManager error handling and edge cases"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create minimal valid configs
            configs = {
                "sources": {
                    "real_estate": [],
                    "infrastructure": [],
                    "policy": [],
                    "celebrity": [],
                    "personal": []
                },
                "keywords": {
                    "real_estate": {"primary": []},
                    "infrastructure": {"primary": []},
                    "policy": {"primary": []},
                    "cities": {"tier1": []}
                },
                "celebrities": {"bollywood": []},
                "events": {"events": []},
                "interests": {"personal_interests": []},
                "schedules": {
                    "timezone": "Asia/Kolkata",
                    "digests": {
                        "morning": {"enabled": True, "time": "07:00", "cron_utc": "30 1 * * *"},
                        "evening": {"enabled": True, "time": "16:00", "cron_utc": "30 10 * * *"}
                    }
                }
            }

            for name, data in configs.items():
                with open(config_dir / f"{name}.json", 'w') as f:
                    json.dump(data, f)

            yield config_dir

    def test_load_all_configs_with_validation_error(self):
        """Test load_all_configs raises error on invalid config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create invalid config (missing categories)
            invalid_sources = {"real_estate": []}
            with open(config_dir / "sources.json", 'w') as f:
                json.dump(invalid_sources, f)

            manager = ConfigManager(str(config_dir))

            with pytest.raises(ValueError, match="Configuration validation failed"):
                manager.load_all_configs(validate=True)

    def test_load_all_configs_without_validation(self):
        """Test load_all_configs skips validation when validate=False"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create invalid config
            invalid_sources = {"real_estate": []}
            with open(config_dir / "sources.json", 'w') as f:
                json.dump(invalid_sources, f)

            manager = ConfigManager(str(config_dir))

            # Should not raise error
            configs = manager.load_all_configs(validate=False)
            assert configs is not None

    def test_get_sources_with_category_filter(self, temp_config_dir):
        """Test get_sources with category filter"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs()

        real_estate = manager.get_sources(category='real_estate')
        assert isinstance(real_estate, list)

    def test_get_sources_with_nonexistent_category(self, temp_config_dir):
        """Test get_sources with non-existent category returns empty list"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs()

        result = manager.get_sources(category='nonexistent')
        assert result == []

    def test_get_sources_lazy_load(self, temp_config_dir):
        """Test get_sources loads config if not already loaded"""
        manager = ConfigManager(str(temp_config_dir))

        # Don't call load_all_configs first
        sources = manager.get_sources()
        assert sources is not None

    def test_get_keywords_with_category(self, temp_config_dir):
        """Test get_keywords with category filter"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs()

        keywords = manager.get_keywords(category='real_estate')
        assert isinstance(keywords, dict)

    def test_get_keywords_with_nonexistent_category(self, temp_config_dir):
        """Test get_keywords with non-existent category returns empty dict"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs()

        result = manager.get_keywords(category='nonexistent')
        assert result == {}

    def test_get_keywords_lazy_load(self, temp_config_dir):
        """Test get_keywords loads config if not already loaded"""
        manager = ConfigManager(str(temp_config_dir))

        keywords = manager.get_keywords()
        assert keywords is not None

    def test_get_celebrities_with_category(self, temp_config_dir):
        """Test get_celebrities with category filter"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs()

        celebs = manager.get_celebrities(category='bollywood')
        assert isinstance(celebs, list)

    def test_get_celebrities_with_nonexistent_category(self, temp_config_dir):
        """Test get_celebrities with non-existent category returns empty list"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs()

        result = manager.get_celebrities(category='nonexistent')
        assert result == []

    def test_get_celebrities_lazy_load(self, temp_config_dir):
        """Test get_celebrities loads config if not already loaded"""
        manager = ConfigManager(str(temp_config_dir))

        celebs = manager.get_celebrities()
        assert celebs is not None

    def test_get_events_all(self, temp_config_dir):
        """Test get_events returns all events"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs()

        events = manager.get_events(active_only=False)
        assert isinstance(events, list)

    def test_get_events_active_only_with_data(self):
        """Test get_events with active_only filter"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            events_config = {
                "events": [
                    {"id": "e1", "name": "Event 1", "date": "2026-02-01",
                     "start_time": "10:00", "end_time": "18:00", "active": True},
                    {"id": "e2", "name": "Event 2", "date": "2026-02-02",
                     "start_time": "10:00", "end_time": "18:00", "active": False}
                ]
            }
            with open(config_dir / "events.json", 'w') as f:
                json.dump(events_config, f)

            manager = ConfigManager(str(config_dir))
            manager.load_all_configs(validate=False)

            active_events = manager.get_events(active_only=True)
            assert len(active_events) == 1
            assert active_events[0]['id'] == 'e1'

    def test_get_events_lazy_load(self, temp_config_dir):
        """Test get_events loads config if not already loaded"""
        manager = ConfigManager(str(temp_config_dir))

        events = manager.get_events()
        assert isinstance(events, list)

    def test_get_interests_all(self, temp_config_dir):
        """Test get_interests returns all interests"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs()

        interests = manager.get_interests(active_only=False)
        assert isinstance(interests, list)

    def test_get_interests_active_only_with_data(self):
        """Test get_interests with active_only filter"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            interests_config = {
                "personal_interests": [
                    {"id": "i1", "name": "Interest 1", "keywords": ["k1"], "active": True},
                    {"id": "i2", "name": "Interest 2", "keywords": ["k2"], "active": False}
                ]
            }
            with open(config_dir / "interests.json", 'w') as f:
                json.dump(interests_config, f)

            manager = ConfigManager(str(config_dir))
            manager.load_all_configs(validate=False)

            active_interests = manager.get_interests(active_only=True)
            assert len(active_interests) == 1
            assert active_interests[0]['id'] == 'i1'

    def test_get_interests_lazy_load(self, temp_config_dir):
        """Test get_interests loads config if not already loaded"""
        manager = ConfigManager(str(temp_config_dir))

        interests = manager.get_interests()
        assert isinstance(interests, list)

    def test_get_schedules_lazy_load(self, temp_config_dir):
        """Test get_schedules loads config if not already loaded"""
        manager = ConfigManager(str(temp_config_dir))

        schedules = manager.get_schedules()
        assert schedules is not None

    def test_get_digest_schedule_morning(self, temp_config_dir):
        """Test get_digest_schedule for morning"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs()

        morning = manager.get_digest_schedule('morning')
        assert morning is not None
        assert morning['enabled'] is True

    def test_get_digest_schedule_evening(self, temp_config_dir):
        """Test get_digest_schedule for evening"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs()

        evening = manager.get_digest_schedule('evening')
        assert evening is not None
        assert evening['enabled'] is True

    def test_get_digest_schedule_nonexistent(self, temp_config_dir):
        """Test get_digest_schedule with non-existent digest type"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs()

        result = manager.get_digest_schedule('nonexistent')
        assert result is None

    def test_is_digest_enabled_true(self, temp_config_dir):
        """Test is_digest_enabled returns True for enabled digest"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs()

        assert manager.is_digest_enabled('morning') is True

    def test_is_digest_enabled_false_when_disabled(self):
        """Test is_digest_enabled returns False for disabled digest"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            schedules = {
                "digests": {
                    "morning": {"enabled": False, "time": "07:00", "cron_utc": "30 1 * * *"}
                }
            }
            with open(config_dir / "schedules.json", 'w') as f:
                json.dump(schedules, f)

            manager = ConfigManager(str(config_dir))
            manager.load_all_configs(validate=False)

            assert manager.is_digest_enabled('morning') is False

    def test_is_digest_enabled_false_when_nonexistent(self, temp_config_dir):
        """Test is_digest_enabled returns False for non-existent digest"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs()

        assert manager.is_digest_enabled('nonexistent') is False

    def test_reload_config_marks_unvalidated(self, temp_config_dir):
        """Test reload_config marks config as unvalidated"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs(validate=True)

        assert manager.is_validated() is True

        manager.reload_config('sources')

        assert manager.is_validated() is False

    def test_reload_all_revalidates(self, temp_config_dir):
        """Test reload_all revalidates configs"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs(validate=True)

        manager.reload_all()

        assert manager.is_validated() is True

    def test_get_all_loads_if_empty(self, temp_config_dir):
        """Test get_all loads configs if not already loaded"""
        manager = ConfigManager(str(temp_config_dir))

        # Don't call load_all_configs
        all_configs = manager.get_all()

        assert all_configs is not None
        assert len(all_configs) > 0

    def test_is_validated_initially_false(self, temp_config_dir):
        """Test is_validated is False initially"""
        manager = ConfigManager(str(temp_config_dir))

        assert manager.is_validated() is False

    def test_is_validated_after_loading(self, temp_config_dir):
        """Test is_validated is True after successful load with validation"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs(validate=True)

        assert manager.is_validated() is True

    def test_is_validated_false_after_load_without_validation(self, temp_config_dir):
        """Test is_validated is False after load without validation"""
        manager = ConfigManager(str(temp_config_dir))
        manager.load_all_configs(validate=False)

        assert manager.is_validated() is False
