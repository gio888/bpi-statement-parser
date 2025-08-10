"""
Unit tests for config_loader module
"""

import unittest
import tempfile
import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config_loader import ConfigLoader

class TestConfigLoader(unittest.TestCase):
    """Test cases for ConfigLoader class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test config
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_load_defaults_when_no_config(self):
        """Test that defaults are loaded when config directory doesn't exist"""
        loader = ConfigLoader(config_dir=Path("/nonexistent/path"))
        result = loader.load()
        
        self.assertTrue(result)
        self.assertIsNotNone(loader.config)
        self.assertEqual(loader.get('PRIMARY_CURRENCY'), 'PHP')
        self.assertEqual(loader.get('MAX_BATCH_SIZE'), 50)
    
    def test_create_valid_config_file(self):
        """Test loading a valid config.py file"""
        config_content = """
PDF_INPUT_FOLDER = "/test/input"
OUTPUT_FOLDER = "/test/output"
ACCOUNTS_CSV_PATH = None
DEFAULT_CUTOFF_DATE = "2024-01-01"
PRIMARY_CURRENCY = "PHP"
MAX_BATCH_SIZE = 50
"""
        config_file = self.config_dir / "config.py"
        config_file.write_text(config_content)
        
        loader = ConfigLoader(config_dir=self.config_dir)
        result = loader.load()
        
        self.assertTrue(result)
        self.assertEqual(loader.get('PDF_INPUT_FOLDER'), '/test/input')
        self.assertEqual(loader.get('OUTPUT_FOLDER'), '/test/output')
    
    def test_environment_variable_override(self):
        """Test that environment variables override config values"""
        os.environ['BPI_PRIMARY_CURRENCY'] = 'USD'
        
        loader = ConfigLoader(config_dir=self.config_dir)
        loader.load()
        
        self.assertEqual(loader.get('PRIMARY_CURRENCY'), 'USD')
        
        # Clean up
        del os.environ['BPI_PRIMARY_CURRENCY']
    
    def test_get_card_account_mapping(self):
        """Test card account mapping functionality"""
        loader = ConfigLoader(config_dir=self.config_dir)
        loader.config = {
            'CARD_ACCOUNT_MAPPINGS': {
                'BPI ECREDIT CARD': 'Liabilities:Credit Card:BPI:e-credit',
                'BPI GOLD REWARDS CARD': 'Liabilities:Credit Card:BPI:Gold'
            },
            'DEFAULT_CARD_ACCOUNT': 'Liabilities:Credit Card:BPI'
        }
        
        # Test exact match
        account = loader.get_card_account('BPI ECREDIT CARD')
        self.assertEqual(account, 'Liabilities:Credit Card:BPI:e-credit')
        
        # Test partial match
        account = loader.get_card_account('Something with BPI GOLD REWARDS CARD in it')
        self.assertEqual(account, 'Liabilities:Credit Card:BPI:Gold')
        
        # Test default
        account = loader.get_card_account('Unknown Card')
        self.assertEqual(account, 'Liabilities:Credit Card:BPI')
    
    def test_validate_date_format(self):
        """Test date format validation"""
        config_content = """
DEFAULT_CUTOFF_DATE = "invalid-date-format"
"""
        config_file = self.config_dir / "config.py"
        config_file.write_text(config_content)
        
        loader = ConfigLoader(config_dir=self.config_dir)
        loader.load()
        
        # Should have an error about invalid date
        self.assertTrue(any('DEFAULT_CUTOFF_DATE' in error for error in loader.errors))
    
    def test_output_folder_creation(self):
        """Test that output folder is created if it doesn't exist"""
        output_dir = self.temp_dir + "/test_output"
        loader = ConfigLoader(config_dir=self.config_dir)
        loader.config = {'OUTPUT_FOLDER': output_dir}
        loader._validate_config()
        
        self.assertTrue(os.path.exists(output_dir))
    
    def test_transaction_rules_loading(self):
        """Test loading transaction rules from JSON"""
        rules = {
            "rules": {
                "exact_matches": {
                    "mappings": {
                        "Netflix.Com": "Expenses:Entertainment"
                    }
                }
            }
        }
        
        rules_file = self.config_dir / "transaction_rules.json"
        rules_file.write_text(json.dumps(rules))
        
        loader = ConfigLoader(config_dir=self.config_dir)
        loader.load()
        
        self.assertIsNotNone(loader.transaction_rules)
        self.assertIn('rules', loader.transaction_rules)
    
    def test_get_merchant_mapping(self):
        """Test merchant mapping lookup"""
        loader = ConfigLoader(config_dir=self.config_dir)
        loader.config = {
            'CUSTOM_MERCHANT_MAPPINGS': {
                'Starbucks': 'Expenses:Food:Coffee'
            },
            'KEYWORD_CATEGORIES': {
                'restaurant': 'Expenses:Food:Dining'
            }
        }
        
        # Test exact match
        mapping = loader.get_merchant_mapping('Starbucks')
        self.assertEqual(mapping, 'Expenses:Food:Coffee')
        
        # Test keyword match
        mapping = loader.get_merchant_mapping('Pizza Restaurant')
        self.assertEqual(mapping, 'Expenses:Food:Dining')
        
        # Test no match
        mapping = loader.get_merchant_mapping('Unknown Merchant')
        self.assertIsNone(mapping)

if __name__ == '__main__':
    unittest.main()