import os
import tempfile
import unittest

from src.config import Config


class TestConfig(unittest.TestCase):
    
    def test_default_config_when_no_file(self):
        """Config falls back to defaults when YAML is missing."""
        cfg = Config("nonexistent_config.yaml")
        self.assertEqual(cfg.get('database.type'), 'sqlite')
        self.assertIsInstance(cfg.get('categorias'), list)
        self.assertFalse(cfg.get('notifications.enabled'))
    
    def test_dot_key_access(self):
        cfg = Config("nonexistent_config.yaml")
        self.assertEqual(cfg.get('database.path'), 'data/publications.db')
        self.assertIsNone(cfg.get('nonexistent.key'))
        self.assertEqual(cfg.get('nonexistent.key', 'fallback'), 'fallback')
    
    def test_load_yaml_file(self):
        """Config reads from a real YAML file."""
        content = "database:\n  type: sqlite\n  path: test.db\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(content)
            f.flush()
            cfg = Config(f.name)
        
        self.assertEqual(cfg.get('database.path'), 'test.db')
        os.unlink(f.name)


if __name__ == '__main__':
    unittest.main()
