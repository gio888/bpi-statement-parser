"""
Configuration Loader for BPI Statement Parser
Handles loading and validation of user configuration
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

class ConfigLoader:
    """Central configuration management for BPI Statement Parser"""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize configuration loader
        
        Args:
            config_dir: Path to config directory (default: ./config)
        """
        # Determine config directory
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Look for config in project root
            project_root = Path(__file__).parent.parent
            self.config_dir = project_root / "config"
        
        self.config = {}
        self.transaction_rules = {}
        self.is_loaded = False
        self.errors = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def load(self) -> bool:
        """
        Load all configuration files
        
        Returns:
            bool: True if configuration loaded successfully
        """
        self.errors = []
        
        # Check if config directory exists
        if not self.config_dir.exists():
            self.logger.warning(f"Config directory not found: {self.config_dir}")
            self.logger.info("Using default configuration. Run setup.py to create personal config.")
            self._load_defaults()
            return True
        
        # Load main config
        config_file = self.config_dir / "config.py"
        if config_file.exists():
            self._load_config_file(config_file)
        else:
            self.logger.warning("config.py not found, using defaults")
            self._load_defaults()
        
        # Load transaction rules
        rules_file = self.config_dir / "transaction_rules.json"
        if rules_file.exists():
            self._load_transaction_rules(rules_file)
        
        # Validate configuration
        self._validate_config()
        
        self.is_loaded = len(self.errors) == 0
        
        if self.errors:
            self.logger.error("Configuration errors found:")
            for error in self.errors:
                self.logger.error(f"  - {error}")
        
        return self.is_loaded
    
    def _load_config_file(self, config_file: Path):
        """Load main configuration from Python file"""
        try:
            # Add config directory to path temporarily
            sys.path.insert(0, str(self.config_dir))
            
            # Import config module
            import config
            
            # Extract configuration values
            for key in dir(config):
                if not key.startswith('_'):
                    value = getattr(config, key)
                    # Skip functions and modules
                    if not callable(value) and not hasattr(value, '__module__'):
                        self.config[key] = value
            
            # Remove from path
            sys.path.remove(str(self.config_dir))
            
            self.logger.info(f"Loaded configuration from {config_file}")
            
        except Exception as e:
            self.errors.append(f"Failed to load config.py: {e}")
            self._load_defaults()
    
    def _load_transaction_rules(self, rules_file: Path):
        """Load transaction categorization rules from JSON"""
        try:
            with open(rules_file, 'r') as f:
                self.transaction_rules = json.load(f)
            self.logger.info(f"Loaded transaction rules from {rules_file}")
        except Exception as e:
            self.errors.append(f"Failed to load transaction rules: {e}")
    
    def _load_defaults(self):
        """Load default configuration values"""
        self.config = {
            # File paths - use environment variables as fallback
            'PDF_INPUT_FOLDER': os.environ.get('BPI_PDF_FOLDER', './data/input'),
            'OUTPUT_FOLDER': os.environ.get('BPI_OUTPUT_FOLDER', './data/output'),
            'ACCOUNTS_CSV_PATH': os.environ.get('BPI_ACCOUNTS_CSV', None),
            
            # Processing options
            'DEFAULT_CUTOFF_DATE': '2024-01-01',
            'MAX_BATCH_SIZE': 50,
            'CSV_DATE_FORMAT': '%Y-%m-%d',
            'SORT_BY_DATE': True,
            
            # Card mappings
            'CARD_ACCOUNT_MAPPINGS': {
                'BPI ECREDIT CARD': 'Liabilities:Credit Card:BPI Mastercard:e-credit',
                'BPI GOLD REWARDS CARD': 'Liabilities:Credit Card:BPI Mastercard:Gold',
            },
            'DEFAULT_CARD_ACCOUNT': 'Liabilities:Credit Card:BPI Mastercard',
            
            # Currency settings
            'PRIMARY_CURRENCY': 'PHP',
            'SUPPORTED_CURRENCIES': ['PHP', 'USD', 'SGD', 'NZD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD'],
            'INCLUDE_FOREIGN_AMOUNTS': True,
            
            # Transaction categorization
            'CUSTOM_MERCHANT_MAPPINGS': {},
            'KEYWORD_CATEGORIES': {},
            'DEFAULT_CATEGORY': 'Manual Review',
            
            # Advanced options
            'ENABLE_LOGGING': True,
            'LOG_LEVEL': 'INFO',
            'SKIP_FAILED_PDFS': True,
            'SHOW_DETAILED_ERRORS': False,
        }
        
        self.logger.info("Using default configuration")
    
    def _validate_config(self):
        """Validate configuration values"""
        # Check required paths
        pdf_folder = self.get('PDF_INPUT_FOLDER')
        if pdf_folder and not os.path.exists(pdf_folder):
            self.logger.warning(f"PDF_INPUT_FOLDER does not exist: {pdf_folder}")
        
        # Validate date format
        try:
            cutoff_date = self.get('DEFAULT_CUTOFF_DATE')
            if cutoff_date:
                datetime.strptime(cutoff_date, '%Y-%m-%d')
        except ValueError:
            self.errors.append(f"Invalid DEFAULT_CUTOFF_DATE format: {cutoff_date}")
        
        # Create output folder if it doesn't exist
        output_folder = self.get('OUTPUT_FOLDER')
        if output_folder:
            try:
                os.makedirs(output_folder, exist_ok=True)
            except Exception as e:
                self.errors.append(f"Cannot create OUTPUT_FOLDER: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        # First check environment variables (highest priority)
        env_key = f"BPI_{key}"
        env_value = os.environ.get(env_key)
        if env_value:
            return env_value
        
        # Then check loaded config
        return self.config.get(key, default)
    
    def get_accounts_csv_path(self) -> Optional[str]:
        """Get path to accounts CSV file"""
        # First check config
        path = self.get('ACCOUNTS_CSV_PATH')
        if path and os.path.exists(path):
            return path
        
        # Check config directory for personal accounts mapping
        config_accounts = self.config_dir / "accounts_mapping.csv"
        if config_accounts.exists():
            return str(config_accounts)
        
        # No fallback to data directory - accounts must be in personal config
        self.logger.warning("No accounts CSV found. Please run setup.py to configure your personal accounts.")
        return None
    
    def get_output_folder(self) -> str:
        """Get output folder path, creating if necessary"""
        folder = self.get('OUTPUT_FOLDER', './data/output')
        os.makedirs(folder, exist_ok=True)
        return folder
    
    def get_card_account(self, card_name: str) -> str:
        """
        Get account mapping for a specific card
        
        Args:
            card_name: Name of the credit card
        
        Returns:
            Account path for the card
        """
        mappings = self.get('CARD_ACCOUNT_MAPPINGS', {})
        
        # Check exact match first
        if card_name in mappings:
            return mappings[card_name]
        
        # Check partial matches
        card_upper = card_name.upper()
        for key, value in mappings.items():
            if key.upper() in card_upper or card_upper in key.upper():
                return value
        
        # Return default
        return self.get('DEFAULT_CARD_ACCOUNT', 'Liabilities:Credit Card:BPI Mastercard')
    
    def get_transaction_rules(self) -> Dict:
        """Get transaction categorization rules"""
        if self.transaction_rules:
            return self.transaction_rules.get('rules', {})
        return {}
    
    def get_merchant_mapping(self, merchant: str) -> Optional[str]:
        """
        Get account category for a merchant
        
        Args:
            merchant: Merchant name from transaction
        
        Returns:
            Account category or None if not found
        """
        # Check custom mappings first
        custom_mappings = self.get('CUSTOM_MERCHANT_MAPPINGS', {})
        
        # Case-insensitive exact match
        merchant_lower = merchant.lower()
        for key, value in custom_mappings.items():
            if key.lower() == merchant_lower:
                return value
        
        # Check transaction rules if loaded
        if self.transaction_rules:
            rules = self.get_transaction_rules()
            
            # Check exact matches
            exact_matches = rules.get('exact_matches', {}).get('mappings', {})
            for key, value in exact_matches.items():
                if key.lower() == merchant_lower:
                    return value
            
            # Check partial matches
            partial_matches = rules.get('partial_matches', {}).get('mappings', {})
            for key, value in partial_matches.items():
                if key.lower() in merchant_lower:
                    return value
        
        # Check keyword categories
        keyword_categories = self.get('KEYWORD_CATEGORIES', {})
        for keyword, category in keyword_categories.items():
            if keyword.lower() in merchant_lower:
                return category
        
        return None
    
    def save_transaction_rules(self):
        """Save updated transaction rules back to file"""
        if not self.transaction_rules:
            return
        
        rules_file = self.config_dir / "transaction_rules.json"
        try:
            with open(rules_file, 'w') as f:
                json.dump(self.transaction_rules, f, indent=2)
            self.logger.info(f"Saved transaction rules to {rules_file}")
        except Exception as e:
            self.logger.error(f"Failed to save transaction rules: {e}")
    
    def update_statistics(self, rule_type: str, rule_name: str):
        """Update rule usage statistics"""
        if not self.transaction_rules:
            return
        
        stats = self.transaction_rules.setdefault('statistics', {})
        stats['total_processed'] = stats.get('total_processed', 0) + 1
        
        rule_matches = stats.setdefault('rule_matches', {})
        key = f"{rule_type}:{rule_name}"
        rule_matches[key] = rule_matches.get(key, 0) + 1

# Global config instance
_config = None

def get_config() -> ConfigLoader:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = ConfigLoader()
        _config.load()
    return _config

def reload_config():
    """Reload configuration from files"""
    global _config
    _config = ConfigLoader()
    _config.load()
    return _config