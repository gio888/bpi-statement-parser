#!/usr/bin/env python3
"""
BPI Statement Parser - Setup Wizard
Interactive setup script for first-time configuration
"""

import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime

class SetupWizard:
    """Interactive setup wizard for BPI Statement Parser"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.config_dir = self.project_root / "config"
        self.templates_dir = self.project_root / "config_templates"
        self.config = {}
        
    def run(self):
        """Run the setup wizard"""
        print("=" * 70)
        print("🎯 BPI STATEMENT PARSER - SETUP WIZARD")
        print("=" * 70)
        print("\nThis wizard will help you configure the BPI Statement Parser")
        print("for your personal use. Your configuration will be stored locally")
        print("and will NOT be committed to version control.\n")
        
        # Check if config already exists
        if self.config_dir.exists() and (self.config_dir / "config.py").exists():
            response = input("⚠️  Configuration already exists. Overwrite? (y/N): ").strip().lower()
            if response != 'y':
                print("Setup cancelled.")
                return
        
        # Create config directory
        self.create_config_directory()
        
        # Gather user inputs
        self.gather_paths()
        self.gather_card_mappings()
        self.gather_processing_options()
        
        # Copy template files
        self.copy_template_files()
        
        # Generate config file
        self.generate_config_file()
        
        # Test configuration
        self.test_configuration()
        
        print("\n" + "=" * 70)
        print("✅ SETUP COMPLETE!")
        print("=" * 70)
        print("\nYour personal configuration has been created in: config/")
        print("\nYou can now run the parser with:")
        print("  python src/main_enhanced.py")
        print("\nTo modify your configuration, edit: config/config.py")
    
    def create_config_directory(self):
        """Create config directory if it doesn't exist"""
        self.config_dir.mkdir(exist_ok=True)
        print(f"✓ Created config directory: {self.config_dir}")
    
    def gather_paths(self):
        """Gather file path configurations from user"""
        print("\n" + "-" * 50)
        print("📁 FILE PATHS CONFIGURATION")
        print("-" * 50)
        
        # PDF Input Folder
        default_pdf = str(self.project_root / "data" / "input")
        pdf_folder = input(f"\n1. PDF input folder [{default_pdf}]: ").strip()
        if not pdf_folder:
            pdf_folder = default_pdf
        
        # Validate and create if needed
        pdf_path = Path(pdf_folder).expanduser()
        if not pdf_path.exists():
            create = input(f"   Folder doesn't exist. Create it? (Y/n): ").strip().lower()
            if create != 'n':
                pdf_path.mkdir(parents=True, exist_ok=True)
                print(f"   ✓ Created: {pdf_path}")
        
        self.config['PDF_INPUT_FOLDER'] = str(pdf_path)
        
        # Output Folder
        default_output = str(self.project_root / "data" / "output")
        output_folder = input(f"\n2. Output folder [{default_output}]: ").strip()
        if not output_folder:
            output_folder = default_output
        
        output_path = Path(output_folder).expanduser()
        if not output_path.exists():
            create = input(f"   Folder doesn't exist. Create it? (Y/n): ").strip().lower()
            if create != 'n':
                output_path.mkdir(parents=True, exist_ok=True)
                print(f"   ✓ Created: {output_path}")
        
        self.config['OUTPUT_FOLDER'] = str(output_path)
        
        # Accounts CSV (optional)
        print("\n3. Accounts mapping CSV (optional)")
        print("   This file contains your chart of accounts for auto-categorization")
        accounts_csv = input("   Path to accounts CSV (press Enter to skip): ").strip()
        
        if accounts_csv:
            accounts_path = Path(accounts_csv).expanduser()
            if accounts_path.exists():
                self.config['ACCOUNTS_CSV_PATH'] = str(accounts_path)
                print(f"   ✓ Will use: {accounts_path}")
            else:
                print(f"   ⚠️  File not found, skipping")
                self.config['ACCOUNTS_CSV_PATH'] = None
        else:
            self.config['ACCOUNTS_CSV_PATH'] = None
    
    def gather_card_mappings(self):
        """Gather credit card to account mappings"""
        print("\n" + "-" * 50)
        print("💳 CREDIT CARD MAPPINGS")
        print("-" * 50)
        print("\nMap your credit cards to accounting accounts")
        print("(Used for creating separate CSV files for each card)")
        
        self.config['CARD_ACCOUNT_MAPPINGS'] = {}
        
        # Common BPI cards
        cards = [
            ("BPI ECREDIT CARD", "Liabilities:Credit Card:BPI Mastercard:e-credit"),
            ("BPI GOLD REWARDS CARD", "Liabilities:Credit Card:BPI Mastercard:Gold"),
        ]
        
        print("\nDefault card mappings:")
        for card_name, default_account in cards:
            print(f"\n  {card_name}")
            account = input(f"  Account [{default_account}]: ").strip()
            if not account:
                account = default_account
            self.config['CARD_ACCOUNT_MAPPINGS'][card_name] = account
        
        # Additional cards
        while True:
            print("\nAdd another card? (press Enter to skip)")
            card_name = input("  Card name: ").strip()
            if not card_name:
                break
            account = input("  Account path: ").strip()
            if account:
                self.config['CARD_ACCOUNT_MAPPINGS'][card_name] = account
        
        # Default account
        default = "Liabilities:Credit Card:BPI Mastercard"
        self.config['DEFAULT_CARD_ACCOUNT'] = input(f"\nDefault account for unknown cards [{default}]: ").strip() or default
    
    def gather_processing_options(self):
        """Gather processing preferences"""
        print("\n" + "-" * 50)
        print("⚙️  PROCESSING OPTIONS")
        print("-" * 50)
        
        # Cutoff date
        default_date = "2024-01-01"
        cutoff = input(f"\n1. Default cutoff date (YYYY-MM-DD) [{default_date}]: ").strip()
        if not cutoff:
            cutoff = default_date
        
        # Validate date format
        try:
            datetime.strptime(cutoff, "%Y-%m-%d")
            self.config['DEFAULT_CUTOFF_DATE'] = cutoff
        except ValueError:
            print(f"   ⚠️  Invalid date format, using {default_date}")
            self.config['DEFAULT_CUTOFF_DATE'] = default_date
        
        # Currency settings
        self.config['PRIMARY_CURRENCY'] = "PHP"
        self.config['SUPPORTED_CURRENCIES'] = ["PHP", "USD", "SGD", "NZD", "EUR", "GBP", "JPY", "AUD", "CAD"]
        
        # Other options
        self.config['MAX_BATCH_SIZE'] = 50
        self.config['CSV_DATE_FORMAT'] = "%Y-%m-%d"
        self.config['SORT_BY_DATE'] = True
        self.config['INCLUDE_FOREIGN_AMOUNTS'] = True
        self.config['DEFAULT_CATEGORY'] = "Manual Review"
        
        print("\n✓ Processing options configured")
    
    def copy_template_files(self):
        """Copy template files to config directory"""
        print("\n" + "-" * 50)
        print("📋 COPYING TEMPLATE FILES")
        print("-" * 50)
        
        # Copy accounts mapping template if user doesn't have one
        if not self.config.get('ACCOUNTS_CSV_PATH'):
            src = self.templates_dir / "accounts_mapping_template.csv"
            dst = self.config_dir / "accounts_mapping.csv"
            if src.exists():
                shutil.copy2(src, dst)
                print(f"✓ Created accounts mapping template: {dst}")
                self.config['ACCOUNTS_CSV_PATH'] = str(dst)
        
        # Copy transaction rules template
        src = self.templates_dir / "transaction_rules_template.json"
        dst = self.config_dir / "transaction_rules.json"
        if src.exists():
            shutil.copy2(src, dst)
            print(f"✓ Created transaction rules template: {dst}")
    
    def generate_config_file(self):
        """Generate the config.py file"""
        print("\n" + "-" * 50)
        print("📝 GENERATING CONFIGURATION FILE")
        print("-" * 50)
        
        config_file = self.config_dir / "config.py"
        
        # Generate config content
        content = '''"""
BPI Statement Parser - Personal Configuration
Generated by setup wizard on {date}

DO NOT COMMIT THIS FILE TO VERSION CONTROL
"""

import os
from pathlib import Path

# ===========================
# FILE PATHS
# ===========================

PDF_INPUT_FOLDER = r"{pdf_input}"
ACCOUNTS_CSV_PATH = {accounts_csv}
OUTPUT_FOLDER = r"{output}"

# ===========================
# PROCESSING OPTIONS
# ===========================

DEFAULT_CUTOFF_DATE = "{cutoff_date}"
CSV_DATE_FORMAT = "{date_format}"
MAX_BATCH_SIZE = {batch_size}
SORT_BY_DATE = {sort_by_date}

# ===========================
# CARD TO ACCOUNT MAPPINGS
# ===========================

CARD_ACCOUNT_MAPPINGS = {card_mappings}

DEFAULT_CARD_ACCOUNT = "{default_card}"

# ===========================
# CURRENCY SETTINGS
# ===========================

PRIMARY_CURRENCY = "{primary_currency}"
SUPPORTED_CURRENCIES = {currencies}
INCLUDE_FOREIGN_AMOUNTS = {include_foreign}

# ===========================
# TRANSACTION CATEGORIZATION
# ===========================

CUSTOM_MERCHANT_MAPPINGS = {{}}
KEYWORD_CATEGORIES = {{}}
DEFAULT_CATEGORY = "{default_category}"

# ===========================
# ADVANCED OPTIONS
# ===========================

ENABLE_LOGGING = True
LOG_LEVEL = "INFO"
SKIP_FAILED_PDFS = True
SHOW_DETAILED_ERRORS = False
'''.format(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            pdf_input=self.config['PDF_INPUT_FOLDER'],
            accounts_csv=f'r"{self.config["ACCOUNTS_CSV_PATH"]}"' if self.config.get('ACCOUNTS_CSV_PATH') else 'None',
            output=self.config['OUTPUT_FOLDER'],
            cutoff_date=self.config['DEFAULT_CUTOFF_DATE'],
            date_format=self.config['CSV_DATE_FORMAT'],
            batch_size=self.config['MAX_BATCH_SIZE'],
            sort_by_date=self.config['SORT_BY_DATE'],
            card_mappings=json.dumps(self.config['CARD_ACCOUNT_MAPPINGS'], indent=4),
            default_card=self.config['DEFAULT_CARD_ACCOUNT'],
            primary_currency=self.config['PRIMARY_CURRENCY'],
            currencies=self.config['SUPPORTED_CURRENCIES'],
            include_foreign=self.config['INCLUDE_FOREIGN_AMOUNTS'],
            default_category=self.config['DEFAULT_CATEGORY']
        )
        
        # Write config file
        with open(config_file, 'w') as f:
            f.write(content)
        
        print(f"✓ Generated config file: {config_file}")
    
    def test_configuration(self):
        """Test the configuration by importing it"""
        print("\n" + "-" * 50)
        print("🧪 TESTING CONFIGURATION")
        print("-" * 50)
        
        try:
            # Add config directory to path
            sys.path.insert(0, str(self.config_dir))
            
            # Try to import config
            import config
            
            # Test key values
            tests = [
                ('PDF_INPUT_FOLDER', Path(config.PDF_INPUT_FOLDER).exists(), "PDF input folder exists"),
                ('OUTPUT_FOLDER', True, "Output folder configured"),
                ('CARD_ACCOUNT_MAPPINGS', len(config.CARD_ACCOUNT_MAPPINGS) > 0, "Card mappings configured"),
            ]
            
            all_passed = True
            for name, result, description in tests:
                if result:
                    print(f"✓ {description}")
                else:
                    print(f"⚠️  {description} - may need attention")
                    all_passed = False
            
            if all_passed:
                print("\n✅ All configuration tests passed!")
            else:
                print("\n⚠️  Some tests failed - please review your configuration")
            
            # Remove from path
            sys.path.remove(str(self.config_dir))
            
        except Exception as e:
            print(f"❌ Configuration test failed: {e}")
            print("Please check your configuration file")

def main():
    """Main entry point"""
    wizard = SetupWizard()
    
    try:
        wizard.run()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()