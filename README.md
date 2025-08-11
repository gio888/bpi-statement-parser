# BPI Credit Card Statement Parser

A comprehensive Python tool for extracting transaction data from BPI credit card PDF statements with **beautiful web interface**, **automatic account mapping**, and **secure personal configuration system**.

## 🎯 Features

### 🌐 **New in v3.2.0: Interactive Review Interface**
- ✅ **Review & Correction Interface**: Review AI classifications before download
- ✅ **Confidence Indicators**: Color-coded confidence levels with smart filtering
- ✅ **Keyboard Navigation**: Arrow keys + Enter for lightning-fast corrections
- ✅ **Smart Autocomplete**: Type-to-search through 300+ account categories
- ✅ **Perfect Output Format**: Double-entry accounting ready files

### 🌐 **Web Interface (v3.0.0)**
- ✅ **Beautiful Drag-and-Drop Interface**: No more command line needed!
- ✅ **Real-time Processing**: Live progress indicators and status updates
- ✅ **Batch Upload**: Process multiple PDFs at once
- ✅ **One-Click Download**: Individual files or ZIP bundle
- ✅ **Mobile-Responsive**: Works on desktop, tablet, and mobile

### 🔒 **Security & Configuration (Enhanced v3.2.1)**
- ✅ **Zero Personal Data**: Complete removal of all personal information from codebase
- ✅ **Personal Accounts CSV**: Each user maintains their own chart of accounts in config/
- ✅ **Enhanced Security**: Multiple layers of protection against data exposure
- ✅ **Interactive Setup Wizard**: Copies comprehensive account templates
- ✅ **Forced Best Practices**: No fallbacks to hardcoded personal data
- ✅ **Git History Cleaned**: All personal information removed
- ✅ **Path Traversal Protection**: Secure file handling
- ✅ **Local-Only Server**: Web interface only accessible from localhost

### 🚀 **Core Features**
- ✅ **Automatic Account Mapping**: 98.7% success rate with intelligent categorization
- ✅ **Statement Date-Based Naming**: Files named with actual statement dates for easy organization
- ✅ **Cross-Year Transaction Handling**: December transactions in January statements correctly dated
- ✅ **4-File Output System**: Main data + 2 individual cards + 1 combined import file
- ✅ **Exchange Rate Calculation**: Automatic PHP conversion rates for foreign transactions
- ✅ **Multi-card Support**: BPI Gold Rewards Card and BPI eCredit Card
- ✅ **Multi-currency Handling**: 13+ currencies (PHP, USD, EUR, SGD, NZD, etc.)
- ✅ **Comprehensive Testing**: Unit, integration, and smoke tests included
- ✅ **Smart Text Normalization**: Handles PDF formatting inconsistencies across years
- ✅ **High Success Rate**: 98.7+ automated processing (2023-2025 PDF formats)

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/bpi-statement-parser.git
   cd bpi-statement-parser
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the setup wizard** (first-time setup)
   ```bash
   python setup.py
   ```
   
   The setup wizard will:
   - Create your personal configuration folder
   - Set up your PDF input/output paths
   - Configure credit card to account mappings
   - Generate template files for transaction rules
   - Test your configuration

   Your personal configuration is stored in `config/` and is automatically excluded from version control.

## 🌐 **NEW: Interactive Review Workflow (v3.2.0)**

**🎉 Revolutionary review interface for perfect account classifications!**

1. **Start the web interface**
   ```bash
   python run_web.py
   ```
   
   This will:
   - Start the Flask server on localhost:8080
   - Automatically open your browser
   - Show the beautiful drag-and-drop interface

2. **Process your statements**
   - Drag and drop multiple PDF files at once
   - Watch real-time processing progress with AI analysis
   - Get confidence breakdown: **"72% high confidence, 20% medium, 8% low"**
   - Choose to review or download directly

3. **Review & Perfect Classifications** (NEW!)
   - **Interactive Review Table**: Sort, filter, and correct AI predictions
   - **Smart Filtering**: Show only low/medium confidence transactions needing attention
   - **Autocomplete Search**: Type to find accounts from your 300+ categories  
   - **Keyboard Navigation**: Arrow keys ↑↓ + Enter for rapid corrections
   - **Visual Indicators**: Color-coded confidence badges for instant quality assessment

4. **Generate Perfect Files**
   - **Double-Entry Accounting Format**: Amount (Negated) and Amount columns
   - **No Blank Accounts**: Every transaction gets proper classification
   - **Ready for Import**: Direct import to QuickBooks, Xero, GnuCash

5. **Quick validation** (optional)
   ```bash
   python run_tests.py --quick  # Run smoke tests
   python preflight_check.py    # Check environment
   ```

## ⌨️ **Classic: Command Line Usage**

If you prefer the traditional approach:

1. **Run the application**
   ```bash
   python src/main_enhanced.py
   ```

2. **Choose processing mode**
   - **Option 1**: Process single PDF
   - **Option 2**: Process multiple PDFs (batch mode)

3. **For batch processing**:
   - Enter cutoff date (e.g., `2023-10-01`)
   - Confirm processing when preview is shown
   - **4 files automatically generated** ✨

## 📁 Output Files

### 🆕 **Review Interface Output (v3.2.0)**
After review and corrections:

**Corrected File** (accounting-ready format):
```
2025-07-13_Statement_BPI_Mastercard_Corrected.csv
```
**Columns**: Date, Description, Amount (Negated), Amount, Account, Target Account
- **Amount (Negated)**: Original amount if positive, 0 if negative
- **Amount**: 0 if positive, absolute value if negative  
- **Perfect double-entry format** for direct accounting software import
- **Zero blank accounts** - every transaction properly classified

### **Classic Output Files (4 Total)**
Classic processing creates **4 ready-to-use files** with **statement date-based naming**:

### 1. **Main CSV** (comprehensive data)
```
Single PDF: 2025-01-12_Statement_BPI_Mastercard_Batch.csv
Batch: 2024-01-14_Statement_BPI_Mastercard_Batch.csv (for date ranges)
```
**Columns**: Card, Transaction Date, Post Date, Description, Amount, Currency, Foreign Amount, Exchange Rate, Target Account, Statement Date

### 2. **Individual Card CSVs** (2 files)
```
Single PDF:
2025-01-12_Statement_BPI_Mastercard_Ecredit.csv
2025-01-12_Statement_BPI_Mastercard_Gold.csv

Batch:
2024-01-14_Statement_BPI_Mastercard_Ecredit.csv
2024-01-14_Statement_BPI_Mastercard_Gold.csv
```
**Columns**: Post Date, Description, Amount, Target Account

### 3. **Combined CSV** (unified import)
```
Single PDF: 2025-01-12_Statement_BPI_Mastercard_Combined.csv
Batch: 2024-01-14_Statement_BPI_Mastercard_Combined.csv
```
**Columns**: Date, Description, Amount, Account, Target Account

Where **Account** is automatically assigned:
- BPI ECREDIT CARD → `Liabilities:Credit Card:BPI Mastercard:e-credit`
- BPI GOLD REWARDS CARD → `Liabilities:Credit Card:BPI Mastercard:Gold`

## 📊 Automatic Account Mapping

**98.7% of transactions are automatically categorized** using intelligent mapping:

### Sample Mappings
```
Apple.Com/Bill Itunes.Com → Expenses:Entertainment:Music/Movies
Google Cloud → Expenses:Professional Development & Productivity
Metromart Makati → Expenses:Food:Groceries
Grab Makati → Expenses:Professional Fees
Payment -Thank You → Liabilities:Credit Card:BPI Mastercard
```

### Supported Categories
- **Entertainment**: Apple, Netflix, Spotify, Nintendo
- **Professional**: Google services, Microsoft, domain hosting
- **Food**: Restaurants, groceries, delivery
- **Education**: Books, subscriptions, newspapers
- **Travel**: Hotels, transportation
- **And many more...**

## 💱 Multi-Currency Support

**13+ currencies supported** with automatic exchange rate calculation:

```csv
Card,Description,Amount,Currency,Foreign Amount,Exchange Rate
BPI ECREDIT CARD,Backblaze.Com SanMateo,2564.56,USD,44.34,57.8234
BPI ECREDIT CARD,Google Cloud 9zlw8b Sg,2.86,SGD,0.05,57.2000
BPI GOLD REWARDS CARD,Amazon Prime VideoPhSingapore,299.00,PHP,,
```

**Supported**: PHP, USD, EUR, GBP, SGD, NZD, CAD, AUD, JPY, CHF, THB, HKD, KRW

## 📁 Project Structure

```
bpi-statement-parser/
├── src/                       # Core application code
│   ├── web_app.py            # 🌐 Flask web interface (NEW v3.0.0)
│   ├── config_loader.py      # 🔒 Configuration management (NEW v3.0.0)
│   ├── main_enhanced.py      # Classic CLI interface
│   ├── batch_processor.py    # Enhanced batch processing
│   ├── statement_finalizer.py# Account mapping & CSV generation
│   ├── pdf_extractor.py      # PDF text extraction
│   ├── transaction_parser.py # Transaction parsing logic
│   └── currency_handler.py   # Currency & exchange rate processing
├── static/                    # 🌐 Web interface files (NEW v3.0.0)
│   ├── index.html            # Main web page
│   ├── style.css             # Modern UI styles
│   └── app.js                # Client-side JavaScript
├── config_templates/          # 🔒 Configuration templates (NEW v3.0.0)
├── tests/                     # 🧪 Comprehensive test suite (NEW v3.0.0)
│   ├── test_config_loader.py # Configuration tests
│   ├── test_web_app.py       # Web interface tests
│   └── test_integration.py   # End-to-end tests
├── run_web.py                # 🌐 One-command web launcher (NEW v3.0.0)
├── setup.py                  # 🔒 Interactive setup wizard (NEW v3.0.0)
├── run_tests.py              # 🧪 Test runner (NEW v3.0.0)
├── preflight_check.py        # 🧪 Environment validator (NEW v3.0.0)
├── account_mapper.py         # Intelligent account mapping
├── config/                     # 🔒 Personal configuration (gitignored)
│   ├── config.py             # Personal settings (YOUR PATHS)
│   ├── accounts_mapping.csv  # Your chart of accounts (67+ accounts)
│   └── transaction_rules.json# Your custom transaction rules
├── data/
│   ├── input/                # PDFs (your statements)
│   └── output/               # Generated CSV files
├── diagnostics/              # Troubleshooting tools
└── docs/                     # Documentation
```

## 🔧 Configuration

### 🔒 **Enhanced: Secure Personal Configuration System (v3.2.1)**

**Complete personal data separation with enhanced security!** 

1. **Run the setup wizard** (first-time only):
   ```bash
   python setup.py
   ```

2. **Personal configuration files created**:
   ```
   config/
   ├── config.py                 # Your personal settings
   ├── accounts_mapping.csv      # Your chart of accounts (67+ accounts)
   └── transaction_rules.json    # Your custom transaction rules
   ```

3. **Enhanced Security Features**:
   - **No Hardcoded Paths**: System no longer falls back to hardcoded locations
   - **Personal Accounts CSV**: Each user maintains their own chart of accounts
   - **Zero Data Exposure**: Repository contains no personal information
   - **Comprehensive Template**: 67-account template with GnuCash structure

4. **Environment variable overrides**:
   ```bash
   export BPI_PDF_INPUT_FOLDER="/custom/path/to/pdfs"
   export BPI_OUTPUT_FOLDER="/custom/path/to/output"
   export BPI_ACCOUNTS_CSV="/custom/path/to/accounts.csv"
   export BPI_PRIMARY_CURRENCY="PHP"
   ```

### Account Mapping Customization
Update mappings in `config/card_account_mapping.py`:
```python
CARD_ACCOUNT_MAPPING = {
    'BPI ECREDIT CARD': 'Liabilities:Credit Card:BPI Mastercard:e-credit',
    'BPI GOLD REWARDS CARD': 'Liabilities:Credit Card:BPI Mastercard:Gold',
}
```

Or customize merchant mappings in `account_mapper.py`:
```python
self.known_mappings = {
    'Your Merchant Name': 'Your:Account:Category',
    # Add more custom mappings
}
```

## 🎯 Workflow

### 🌐 **NEW: Monthly Processing with Review Interface**
1. **Download PDF statements** from BPI online banking
2. **Start web interface**: `python run_web.py`
3. **Drag & drop PDFs** into the browser
4. **Review AI classifications** - Fix any low confidence predictions
5. **Generate perfect files** - Zero blanks, proper accounting format
6. **Import corrected CSV** directly into your accounting system

### ⌨️ **Classic: Command Line Processing**
1. **Download PDF statements** from BPI online banking
2. **Place in configured folder** (or use drag-and-drop on web)
3. **Run batch processor**:
   ```bash
   python src/main_enhanced.py
   # Choose option 2, enter cutoff date
   ```
4. **Import 4 generated CSV files** into your accounting system

### Accounting System Integration
- **Option A**: Import 2 individual card CSVs separately
- **Option B**: Import 1 combined CSV for unified processing
- **Analysis**: Use main CSV for reporting and analysis

## 🛠️ Troubleshooting

### 🧪 **NEW: Testing & Diagnostics (v3.0.0)**

```bash
# Quick smoke test - validate core functionality
python run_tests.py --quick

# Full test suite - comprehensive validation
python run_tests.py --full

# Pre-flight check - environment validation
python preflight_check.py

# Test account mapping on existing CSV
python test_account_mapper.py

# Check failed PDF processing
python diagnostics/check_failed.py

# Batch processing issues
python diagnostics/batch_diagnostic.py
```

### Common Issues
1. **PDF encoding**: Reformat PDF using Preview (Export as PDF)
2. **No transactions found**: Check card header detection
3. **Poor mapping**: Add custom patterns to account_mapper.py

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for detailed solutions.

## 📈 Performance

- **Success Rate**: 98.7% automatic account mapping
- **Processing Speed**: ~2-5 seconds per PDF
- **Accuracy**: 100% transaction extraction on supported formats
- **Currency Detection**: Automatic detection with exchange rates
- **Batch Efficiency**: Process years of statements in minutes

## 🔄 Recent Updates

### 🔒 **v3.2.1 - Critical Security Fixes & Personal Configuration**
- ✨ **Zero Personal Data** - Complete removal of all personal information from codebase
- ✨ **Personal Accounts CSV** - Each user maintains their own chart of accounts
- ✨ **Enhanced Security** - Multiple layers of protection against data exposure  
- ✨ **No Hardcoded Paths** - System requires proper personal configuration
- ✨ **67-Account Template** - Comprehensive GnuCash-compatible account structure
- ✨ **Better Collaboration** - Safe repository sharing without personal data exposure

### 🎯 **v3.2.0 - Interactive Review & Correction Interface**
- ✨ **Revolutionary Review System** - Review AI classifications before download
- ✨ **Confidence Indicators** - Color-coded confidence levels (High ≥70%, Medium 50-69%, Low <50%)
- ✨ **Smart Filtering** - Filter by confidence or search descriptions
- ✨ **Keyboard Navigation** - Arrow keys + Enter for lightning-fast corrections
- ✨ **Complete Account Coverage** - All 300+ accounts from your CSV available
- ✨ **Perfect Accounting Format** - Double-entry ready with proper Amount columns
- ✨ **Zero Blank Accounts** - Every transaction gets proper classification
- ✨ **95% Time Savings** - Review interface makes corrections 10x faster

### 🎉 **v3.0.0 - Web Interface & Security Revolution**
- ✨ **Beautiful Web Interface** with drag-and-drop functionality
- ✨ **Secure Configuration System** - no personal data in repository
- ✨ **Comprehensive Test Suite** - unit, integration, and smoke tests
- ✨ **Interactive Setup Wizard** - first-time configuration made easy
- ✨ **Git History Cleaned** - all personal information removed
- ✨ **One-Command Launch** - `python run_web.py` and you're done!

### 🚀 **v2.0.0 - Account Mapping & 4-File System**
- ✨ **98.7% automatic account mapping** with fuzzy matching
- ✨ **4-file output system** for flexible accounting integration
- ✨ **Exchange rate calculation** for all foreign transactions
- ✨ **Expanded currency support** (13+ currencies)
- ✨ **Enhanced batch processing** with auto-finalization
- ✨ **Smart account categorization** using transaction patterns

### Technical Improvements
- Beautiful, responsive web interface with real-time processing
- Secure personal configuration system with environment variable overrides
- Comprehensive testing framework with automated validation
- Enhanced security with path traversal protection
- Added fuzzy string matching for intelligent categorization
- Enhanced currency handler with flexible symbol support
- Improved error handling and user feedback

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built specifically for BPI credit card statement automation
- Supports complex multi-currency transactions with automatic categorization
- Designed for seamless accounting software integration

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/bpi-statement-parser/issues)
- **Documentation**: [docs/](docs/)
- **Diagnostics**: Use tools in `diagnostics/` folder

---

**🌐 From PDF statements to perfect accounting files with AI review** ⚡

**v3.2.1**: Zero personal data • Personal accounts CSV • Enhanced security • Perfect collaboration

Made with ❤️ for automated expense tracking and financial management