"""
BPI Statement Parser - Personal Configuration Template

SETUP INSTRUCTIONS:
1. Copy this file to 'config/config.py'
2. Update all paths and settings for your personal setup
3. Ensure the config/ folder is in .gitignore (it should be by default)

IMPORTANT: Never commit your personal config.py to version control!
"""

import os
from pathlib import Path

# ===========================
# FILE PATHS
# ===========================

# Input Paths
PDF_INPUT_FOLDER = "/path/to/your/pdf/statements"  # Where your BPI PDF statements are stored
ACCOUNTS_CSV_PATH = "/path/to/your/accounts/list.csv"  # Your chart of accounts CSV

# Output Paths  
OUTPUT_FOLDER = "/path/to/your/output/folder"  # Where processed CSVs will be saved
# For cloud storage, use full path like:
# OUTPUT_FOLDER = "/Users/yourname/Library/CloudStorage/GoogleDrive-youremail/My Drive/Money/BPI/"

# ===========================
# PROCESSING OPTIONS
# ===========================

# Date Settings
DEFAULT_CUTOFF_DATE = "2024-01-01"  # Process statements from this date forward
CSV_DATE_FORMAT = "%Y-%m-%d"  # Output date format (YYYY-MM-DD)

# Batch Processing
MAX_BATCH_SIZE = 50  # Maximum PDFs to process in one batch
SORT_BY_DATE = True  # Sort transactions by date in output

# ===========================
# CARD TO ACCOUNT MAPPINGS
# ===========================
# Map your credit card names to your accounting system accounts

CARD_ACCOUNT_MAPPINGS = {
    "BPI ECREDIT CARD": "Liabilities:Credit Card:BPI Mastercard:e-credit",
    "BPI GOLD REWARDS CARD": "Liabilities:Credit Card:BPI Mastercard:Gold",
    # Add more cards as needed:
    # "CARD NAME": "Your:Account:Path",
}

# Default account for unknown cards
DEFAULT_CARD_ACCOUNT = "Liabilities:Credit Card:BPI Mastercard"

# ===========================
# CURRENCY SETTINGS
# ===========================

PRIMARY_CURRENCY = "PHP"
SUPPORTED_CURRENCIES = ["PHP", "USD", "SGD", "NZD", "EUR", "GBP", "JPY", "AUD", "CAD"]
INCLUDE_FOREIGN_AMOUNTS = True  # Include foreign currency columns in output

# ===========================
# TRANSACTION CATEGORIZATION
# ===========================

# Custom merchant to account mappings (overrides automatic detection)
# Add your frequently used merchants here for consistent categorization
CUSTOM_MERCHANT_MAPPINGS = {
    # Example entries - customize for your needs:
    # "Starbucks": "Expenses:Food:Coffee",
    # "Shell": "Expenses:Auto:Gas",
    # "Grab": "Expenses:Transportation",
}

# Keywords for automatic categorization
# These are checked if no exact merchant match is found
KEYWORD_CATEGORIES = {
    "grocery": "Expenses:Food:Groceries",
    "restaurant": "Expenses:Food:Dining",
    "gas": "Expenses:Auto:Gas",
    "electric": "Expenses:Utilities:Electric",
    "water": "Expenses:Utilities:Water",
    "internet": "Expenses:Utilities:Internet",
    # Add more keywords as needed
}

# Default category for unmatched transactions
DEFAULT_CATEGORY = "Manual Review"

# ===========================
# ADVANCED OPTIONS
# ===========================

# Logging
ENABLE_LOGGING = True
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "bpi_parser.log"

# Error Handling
SKIP_FAILED_PDFS = True  # Continue processing if one PDF fails
SHOW_DETAILED_ERRORS = False  # Show full stack traces

# Performance
PARALLEL_PROCESSING = False  # Use multiple cores (experimental)
CACHE_PARSED_DATA = True  # Cache parsing results for faster re-runs

# ===========================
# VALIDATION
# ===========================

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check if paths exist
    if not os.path.exists(PDF_INPUT_FOLDER):
        errors.append(f"PDF_INPUT_FOLDER does not exist: {PDF_INPUT_FOLDER}")
    
    if ACCOUNTS_CSV_PATH and not os.path.exists(ACCOUNTS_CSV_PATH):
        errors.append(f"ACCOUNTS_CSV_PATH does not exist: {ACCOUNTS_CSV_PATH}")
    
    # Check output folder is writable
    try:
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    except Exception as e:
        errors.append(f"Cannot create OUTPUT_FOLDER: {OUTPUT_FOLDER} - {e}")
    
    # Validate date format
    from datetime import datetime
    try:
        datetime.strptime(DEFAULT_CUTOFF_DATE, "%Y-%m-%d")
    except ValueError:
        errors.append(f"DEFAULT_CUTOFF_DATE must be in YYYY-MM-DD format: {DEFAULT_CUTOFF_DATE}")
    
    return errors

# Auto-validate on import (optional)
if __name__ == "__main__":
    errors = validate_config()
    if errors:
        print("Configuration errors found:")
        for error in errors:
            print(f"  ❌ {error}")
    else:
        print("✅ Configuration is valid!")