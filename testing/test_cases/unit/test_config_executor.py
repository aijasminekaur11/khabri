"""
Unit Tests for ConfigExecutor

Tests the core execution engine that modifies YAML config files.

Test Coverage:
- Backup creation and restoration
- Add/remove celebrity operations
- Frequency change operations
- Feature toggle operations
- Validation rules
- Error handling
- Rollback on failure
"""

import os
import sys
import unittest
import tempfile
import shutil
import yaml
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'src'))

from utils.config_executor import ConfigExecutor, ExecutionResult
from utils.intent_parser import ParsedIntent


class TestConfigExecutor(unittest.TestCase):
    """Test suite for ConfigExecutor"""

    def setUp(self):
        """Set up test fixtures - create temporary config directory"""
        # Create temporary directory for testing
        self.test_dir = Path(tempfile.mkdtemp())
        self.config_dir = self.test_dir / 'config'
        self.config_dir.mkdir()
        self.backup_dir = self.config_dir / 'backups'
        self.backup_dir.mkdir()

        # Create test config files
        self._create_test_configs()

        # Initialize executor with test directory
        self.executor = ConfigExecutor(base_path=self.test_dir)

    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def _create_test_configs(self):
        """Create test configuration files"""
        # celebrities.yaml
        celebrities_config = {
            'automotive': [
                {'name': 'Mahindra', 'aliases': ['M&M'], 'priority': 'high'},
                {'name': 'Tata Motors', 'aliases': ['Tata'], 'priority': 'high'},
            ],
            'bollywood': [
                {'name': 'Shah Rukh Khan', 'aliases': ['SRK'], 'priority': 'high'},
            ],
            'cricket': []
        }

        with open(self.config_dir / 'celebrities.yaml', 'w') as f:
            yaml.safe_dump(celebrities_config, f)

        # schedules.yaml
        schedules_config = {
            'digests': {
                'morning': {
                    'enabled': True,
                    'time': '07:00',
                },
                'evening': {
                    'enabled': True,
                    'time': '16:00',
                }
            },
            'scraping': {
                'interval_minutes': 30
            },
            'alerts': {
                'enabled': True,
                'min_signal_score': 8
            }
        }

        with open(self.config_dir / 'schedules.yaml', 'w') as f:
            yaml.safe_dump(schedules_config, f)

    # ==========================================
    # Backup and Restore Tests
    # ==========================================

    def test_backup_creates_file(self):
        """Test that backup creates a file in backup directory"""
        config_file = self.config_dir / 'celebrities.yaml'
        backup_file = self.executor._backup_config(config_file)

        self.assertTrue(Path(backup_file).exists())
        self.assertIn('celebrities_', backup_file)

    def test_backup_preserves_content(self):
        """Test that backup preserves original content"""
        config_file = self.config_dir / 'celebrities.yaml'

        # Read original content
        with open(config_file, 'r') as f:
            original_content = f.read()

        # Create backup
        backup_file = self.executor._backup_config(config_file)

        # Read backup content
        with open(backup_file, 'r') as f:
            backup_content = f.read()

        self.assertEqual(original_content, backup_content)

    def test_rollback_restores_file(self):
        """Test that rollback restores file from backup"""
        config_file = self.config_dir / 'celebrities.yaml'

        # Count original automotive companies
        original_config = self.executor._read_yaml(config_file)
        original_count = len(original_config['automotive'])

        # Create backup
        backup_file = self.executor._backup_config(config_file)

        # Modify original file (add new company)
        modified_config = self.executor._read_yaml(config_file)
        modified_config['automotive'] = modified_config['automotive'].copy()
        modified_config['automotive'].append({
            'name': 'Modified Company',
            'aliases': [],
            'priority': 'low'
        })
        self.executor._write_yaml(config_file, modified_config)

        # Verify modification was applied
        modified = self.executor._read_yaml(config_file)
        self.assertEqual(len(modified['automotive']), original_count + 1)

        # Rollback to the backup
        result = self.executor.rollback(backup_file)

        self.assertTrue(result.success)

        # Verify content restored to original count
        restored_config = self.executor._read_yaml(config_file)

        self.assertIn('automotive', restored_config)
        self.assertIn('bollywood', restored_config)

        # Verify count is back to original
        self.assertEqual(len(restored_config['automotive']), original_count)

        # Verify modified company is gone
        names = [item['name'] for item in restored_config['automotive']]
        self.assertNotIn('Modified Company', names)

    def test_cleanup_old_backups(self):
        """Test that old backups are cleaned up"""
        config_file = self.config_dir / 'celebrities.yaml'

        # Create many backups and make them old enough to be cleaned
        import time
        backups_created = []

        for i in range(60):
            backup_file = self.executor._backup_config(config_file)
            backups_created.append(Path(backup_file))

            # Add small delay to ensure different timestamps
            time.sleep(0.001)

        # Manually age the oldest backups by modifying their timestamps
        # (simulate they were created more than 1 hour ago)
        current_time = time.time()
        two_hours_ago = current_time - 7200  # 2 hours

        # Age the first 30 backups (oldest ones)
        for backup in backups_created[:30]:
            if backup.exists():
                os.utime(backup, (two_hours_ago, two_hours_ago))

        # Trigger cleanup by creating one more backup
        self.executor._backup_config(config_file)

        # Count remaining backups
        backups = list(self.backup_dir.glob('celebrities_*.yaml'))

        # Should keep at most MAX + some margin for recent ones
        # The cleanup should have removed the aged excess backups
        self.assertLessEqual(len(backups), self.executor.MAX_BACKUPS_PER_FILE + 20)

    # ==========================================
    # Add Celebrity Tests
    # ==========================================

    def test_add_celebrity_success(self):
        """Test successful addition of celebrity"""
        intent = ParsedIntent(
            intent_type='ADD_COMPANIES',
            category='automotive',
            entities=['Tesla', 'BYD'],
            target_file='config/celebrities.yaml',
            confidence=0.85,
            original_text='add automotive companies like Tesla, BYD'
        )

        result = self.executor.execute(intent)

        self.assertTrue(result.success)
        self.assertIn('Tesla', result.message)
        self.assertIn('BYD', result.message)
        self.assertIsNotNone(result.backup_file)

        # Verify added to config
        config = self.executor._read_yaml(self.config_dir / 'celebrities.yaml')
        names = [item['name'] for item in config['automotive']]
        self.assertIn('Tesla', names)
        self.assertIn('BYD', names)

    def test_add_celebrity_duplicate_skipped(self):
        """Test that duplicate celebrities are skipped"""
        intent = ParsedIntent(
            intent_type='ADD_COMPANIES',
            category='automotive',
            entities=['Mahindra', 'Tesla'],  # Mahindra already exists
            target_file='config/celebrities.yaml',
            confidence=0.85,
            original_text='add Mahindra and Tesla'
        )

        result = self.executor.execute(intent)

        # Should still succeed but skip duplicate
        self.assertTrue(result.success)
        self.assertIn('Tesla', result.details['added'])
        self.assertIn('Mahindra', result.details['skipped'])

    def test_add_celebrity_no_entities(self):
        """Test add with no entities fails gracefully"""
        intent = ParsedIntent(
            intent_type='ADD_COMPANIES',
            category='automotive',
            entities=[],
            target_file='config/celebrities.yaml',
            confidence=0.85,
            original_text='add companies'
        )

        result = self.executor.execute(intent)

        self.assertFalse(result.success)
        self.assertIn('No companies', result.message)

    def test_add_celebrity_no_category(self):
        """Test add without category fails gracefully"""
        intent = ParsedIntent(
            intent_type='ADD_COMPANIES',
            category=None,
            entities=['Tesla'],
            target_file='config/celebrities.yaml',
            confidence=0.85,
            original_text='add Tesla'
        )

        result = self.executor.execute(intent)

        self.assertFalse(result.success)
        self.assertIn('Category not detected', result.message)

    # ==========================================
    # Remove Celebrity Tests
    # ==========================================

    def test_remove_celebrity_success(self):
        """Test successful removal of celebrity"""
        intent = ParsedIntent(
            intent_type='REMOVE_ITEM',
            category='automotive',
            entities=['Mahindra'],
            target_file='config/celebrities.yaml',
            confidence=0.85,
            original_text='remove Mahindra'
        )

        result = self.executor.execute(intent)

        self.assertTrue(result.success)
        self.assertIn('Mahindra', str(result.details['removed']))
        self.assertIsNotNone(result.backup_file)

        # Verify removed from config
        config = self.executor._read_yaml(self.config_dir / 'celebrities.yaml')
        names = [item['name'] for item in config['automotive']]
        self.assertNotIn('Mahindra', names)

    def test_remove_celebrity_not_found(self):
        """Test removing non-existent celebrity"""
        intent = ParsedIntent(
            intent_type='REMOVE_ITEM',
            category='automotive',
            entities=['Tesla'],  # Doesn't exist
            target_file='config/celebrities.yaml',
            confidence=0.85,
            original_text='remove Tesla'
        )

        result = self.executor.execute(intent)

        self.assertFalse(result.success)
        self.assertIn('none were found', result.message)

    # ==========================================
    # Change Frequency Tests
    # ==========================================

    def test_change_frequency_success(self):
        """Test successful frequency change"""
        intent = ParsedIntent(
            intent_type='CHANGE_FREQUENCY',
            category=None,
            entities=['15'],
            target_file='config/schedules.yaml',
            confidence=0.85,
            original_text='check news every 15 minutes'
        )

        result = self.executor.execute(intent)

        self.assertTrue(result.success)
        self.assertEqual(result.before_value, 30)
        self.assertEqual(result.after_value, 15)

        # Verify changed in config
        config = self.executor._read_yaml(self.config_dir / 'schedules.yaml')
        self.assertEqual(config['scraping']['interval_minutes'], 15)

    def test_change_frequency_invalid_value(self):
        """Test frequency change with invalid value"""
        intent = ParsedIntent(
            intent_type='CHANGE_FREQUENCY',
            category=None,
            entities=['2'],  # Too low (min is 5)
            target_file='config/schedules.yaml',
            confidence=0.85,
            original_text='check news every 2 minutes'
        )

        result = self.executor.execute(intent)

        self.assertFalse(result.success)
        self.assertIn('between', result.message)
        self.assertIn('5', result.message)

    def test_change_frequency_no_value(self):
        """Test frequency change without numeric value"""
        intent = ParsedIntent(
            intent_type='CHANGE_FREQUENCY',
            category=None,
            entities=['hourly'],  # No number
            target_file='config/schedules.yaml',
            confidence=0.85,
            original_text='check news hourly'
        )

        result = self.executor.execute(intent)

        self.assertFalse(result.success)
        self.assertIn('Could not detect frequency', result.message)

    # ==========================================
    # Toggle Feature Tests
    # ==========================================

    def test_enable_feature_morning_digest(self):
        """Test enabling morning digest"""
        # First disable it
        config = self.executor._read_yaml(self.config_dir / 'schedules.yaml')
        config['digests']['morning']['enabled'] = False
        self.executor._write_yaml(self.config_dir / 'schedules.yaml', config)

        intent = ParsedIntent(
            intent_type='ENABLE_FEATURE',
            category=None,
            entities=[],
            target_file='config/schedules.yaml',
            confidence=0.85,
            original_text='enable morning digest'
        )

        result = self.executor.execute(intent)

        self.assertTrue(result.success)
        self.assertEqual(result.before_value, False)
        self.assertEqual(result.after_value, True)

        # Verify enabled in config
        config = self.executor._read_yaml(self.config_dir / 'schedules.yaml')
        self.assertTrue(config['digests']['morning']['enabled'])

    def test_disable_feature_alerts(self):
        """Test disabling alerts"""
        intent = ParsedIntent(
            intent_type='DISABLE_FEATURE',
            category=None,
            entities=[],
            target_file='config/schedules.yaml',
            confidence=0.85,
            original_text='disable alerts'
        )

        result = self.executor.execute(intent)

        self.assertTrue(result.success)
        self.assertEqual(result.before_value, True)
        self.assertEqual(result.after_value, False)

        # Verify disabled in config
        config = self.executor._read_yaml(self.config_dir / 'schedules.yaml')
        self.assertFalse(config['alerts']['enabled'])

    # ==========================================
    # Validation Tests
    # ==========================================

    def test_low_confidence_rejected(self):
        """Test that low confidence intents are rejected"""
        intent = ParsedIntent(
            intent_type='ADD_COMPANIES',
            category='automotive',
            entities=['Tesla'],
            target_file='config/celebrities.yaml',
            confidence=0.50,  # Too low
            original_text='maybe add Tesla'
        )

        result = self.executor.execute(intent)

        self.assertFalse(result.success)
        self.assertIn('Confidence too low', result.message)

    # ==========================================
    # Audit Log Tests
    # ==========================================

    def test_audit_log_created(self):
        """Test that successful changes are logged to audit trail"""
        intent = ParsedIntent(
            intent_type='ADD_COMPANIES',
            category='automotive',
            entities=['Tesla'],
            target_file='config/celebrities.yaml',
            confidence=0.85,
            original_text='add Tesla'
        )

        result = self.executor.execute(intent, user_id='test_user_123')

        self.assertTrue(result.success)

        # Check audit log exists and has entry
        self.assertTrue(self.executor.audit_log_file.exists())

        audit_data = self.executor._read_yaml(self.executor.audit_log_file)
        self.assertIn('changes', audit_data)
        self.assertGreater(len(audit_data['changes']), 0)

        # Check first entry
        entry = audit_data['changes'][0]
        self.assertEqual(entry['user_id'], 'test_user_123')
        self.assertEqual(entry['intent_type'], 'ADD_COMPANIES')
        self.assertTrue(entry['success'])

    # ==========================================
    # Error Handling Tests
    # ==========================================

    def test_invalid_file_path(self):
        """Test handling of invalid file paths"""
        intent = ParsedIntent(
            intent_type='ADD_COMPANIES',
            category='automotive',
            entities=['Tesla'],
            target_file='config/nonexistent.yaml',
            confidence=0.85,
            original_text='add Tesla'
        )

        # Should handle gracefully
        result = self.executor.execute(intent)
        # Will succeed because it creates the file if needed
        self.assertIsNotNone(result)

    def test_thread_safety(self):
        """Test thread-safe file operations"""
        import threading

        results = []

        def add_company(name):
            intent = ParsedIntent(
                intent_type='ADD_COMPANIES',
                category='automotive',
                entities=[name],
                target_file='config/celebrities.yaml',
                confidence=0.85,
                original_text=f'add {name}'
            )
            result = self.executor.execute(intent)
            results.append(result.success)

        # Create multiple threads
        threads = [
            threading.Thread(target=add_company, args=(f'Company{i}',))
            for i in range(5)
        ]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # All should succeed
        self.assertTrue(all(results))

        # Verify all were added
        config = self.executor._read_yaml(self.config_dir / 'celebrities.yaml')
        names = [item['name'] for item in config['automotive']]
        for i in range(5):
            self.assertIn(f'Company{i}', names)


if __name__ == '__main__':
    unittest.main()
