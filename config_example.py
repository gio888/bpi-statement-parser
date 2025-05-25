"""
Configuration Example for BPI Statement Parser

Copy this file to config.py and update the paths for your setup.
"""

# PDF Processing Paths
PDF_FOLDER = "/Users/yourname/Documents/BPI_Statements/"
OUTPUT_FOLDER = "/Users/yourname/Documents/BPI_Statements/Processed/"

# Processing Options
DEFAULT_CUTOFF_DATE = "2023-01-01"  # Process statements from this date forward
MAX_BATCH_SIZE = 50  # Maximum number of PDFs to process in one batch

# Currency Settings
PRIMARY_CURRENCY = "PHP"
SUPPORTED_CURRENCIES = ["PHP", "USD", "SGD", "NZD"]

# Output Settings
CSV_DATE_FORMAT = "%Y-%m-%d"  # YYYY-MM-DD format
INCLUDE_FOREIGN_AMOUNTS = True
SORT_BY_DATE = True
