# Configuration Guide

This guide explains how to configure the BPI Statement Parser for your personal use.

## Table of Contents
- [Quick Setup](#quick-setup)
- [Configuration Structure](#configuration-structure)
- [Manual Configuration](#manual-configuration)
- [Advanced Configuration](#advanced-configuration)
- [Security Best Practices](#security-best-practices)

## Quick Setup

The easiest way to configure the parser is using the interactive setup wizard:

```bash
python setup.py
```

This will guide you through all configuration options and create your personal config files.

## Configuration Structure

After running the setup wizard, your configuration is stored in the `config/` folder:

```
config/
├── config.py                 # Main configuration file
├── accounts_mapping.csv      # Chart of accounts for categorization
└── transaction_rules.json    # Custom transaction matching rules
```

**Important**: The `config/` folder is automatically excluded from version control to protect your personal data.

## Manual Configuration

If you prefer to configure manually:

1. **Create the config directory**:
   ```bash
   mkdir config
   ```

2. **Copy templates**:
   ```bash
   cp config_templates/config_template.py config/config.py
   cp config_templates/accounts_mapping_template.csv config/accounts_mapping.csv
   cp config_templates/transaction_rules_template.json config/transaction_rules.json
   ```

3. **Edit `config/config.py`** with your personal settings:

### File Paths

```python
# Where your BPI PDF statements are stored
PDF_INPUT_FOLDER = "/path/to/your/pdf/statements"

# Where processed CSV files will be saved
OUTPUT_FOLDER = "/path/to/output/folder"

# Your chart of accounts CSV (optional)
ACCOUNTS_CSV_PATH = "/path/to/accounts.csv"
```

### Card Mappings

Map your credit cards to accounting system accounts:

```python
CARD_ACCOUNT_MAPPINGS = {
    "BPI ECREDIT CARD": "Liabilities:Credit Card:BPI Mastercard:e-credit",
    "BPI GOLD REWARDS CARD": "Liabilities:Credit Card:BPI Mastercard:Gold",
    # Add more cards as needed
}

DEFAULT_CARD_ACCOUNT = "Liabilities:Credit Card:BPI Mastercard"
```

### Processing Options

```python
# Process statements from this date forward
DEFAULT_CUTOFF_DATE = "2024-01-01"

# Maximum PDFs to process in batch mode
MAX_BATCH_SIZE = 50

# Sort transactions by date in output
SORT_BY_DATE = True
```

## Advanced Configuration

### Custom Transaction Rules

Edit `config/transaction_rules.json` to customize transaction categorization:

```json
{
  "rules": {
    "exact_matches": {
      "mappings": {
        "Netflix.Com": "Expenses:Entertainment:Music/Movies",
        "Grab": "Expenses:Transportation"
      }
    },
    "partial_matches": {
      "mappings": {
        "Amazon": "Expenses:Household Supplies",
        "Restaurant": "Expenses:Food:Dining"
      }
    },
    "regex_patterns": {
      "patterns": [
        {
          "pattern": "^ATM.*Withdrawal",
          "category": "Assets:Bank:Cash"
        }
      ]
    }
  }
}
```

### Accounts Mapping CSV

The `config/accounts_mapping.csv` file should contain your chart of accounts:

```csv
Account Name,Account Type,Description,Keywords
Expenses:Food:Groceries,Expense,Grocery shopping,grocery store market
Expenses:Transportation,Expense,Transportation costs,grab taxi uber
```

Keywords are used for automatic transaction matching.

### Environment Variables

You can override any configuration using environment variables:

```bash
export BPI_PDF_INPUT_FOLDER="/custom/path/to/pdfs"
export BPI_OUTPUT_FOLDER="/custom/output"
python src/main_enhanced.py
```

Environment variables take precedence over config file settings.

## Security Best Practices

1. **Never commit personal configuration**
   - The `config/` folder is gitignored by default
   - Don't add personal paths to source code

2. **Use absolute paths**
   - Avoid relative paths that might expose your directory structure
   - Use full paths like `/Users/yourname/Documents/...`

3. **Protect sensitive files**
   - Keep your PDFs and CSVs in folders with appropriate permissions
   - Don't store files in publicly accessible locations

4. **Regular backups**
   - Back up your `config/` folder separately
   - Keep copies of your transaction rules and account mappings

5. **Review before sharing**
   - If sharing logs or error messages, check for personal information
   - Use the diagnostic tools with command-line arguments instead of hardcoded paths

## Troubleshooting

### Configuration not loading

1. Check that `config/config.py` exists
2. Verify Python syntax in the config file
3. Run the validation:
   ```python
   from src.config_loader import get_config
   config = get_config()
   ```

### Path errors

- Ensure all paths in config use forward slashes or raw strings
- On Windows, use raw strings: `r"C:\Users\..."`
- Verify folders exist and have read/write permissions

### Missing transactions

- Check `config/transaction_rules.json` for conflicting rules
- Review regex patterns for accuracy
- Verify account mappings in CSV file

## Migration from Hardcoded Paths

If you're upgrading from an older version with hardcoded paths:

1. Run the setup wizard: `python setup.py`
2. Enter your existing paths when prompted
3. The wizard will migrate your settings automatically
4. Delete any old config files with personal data

## Need Help?

- Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
- Review example configurations in `config_templates/`
- Open an issue on GitHub (remove personal data first)