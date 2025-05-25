# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2025-05-25

### 🚀 Major Features Added
- **Automatic Account Mapping**: 98.7% success rate using intelligent fuzzy matching
- **4-File Output System**: Generate main + 2 individual + 1 combined CSV automatically
- **Exchange Rate Calculation**: Automatic PHP conversion rates (amount ÷ foreign_amount)
- **Enhanced Currency Support**: Expanded from 4 to 13+ currencies with flexible fallback
- **Smart Account Categorization**: AI-powered transaction categorization using actual spending patterns

### ✨ New Components
- `account_mapper.py` - Intelligent account mapping with fuzzy string matching
- `statement_finalizer.py` - Post-processing orchestration for automatic CSV generation
- `test_account_mapper.py` - Testing framework for account mapping accuracy
- Enhanced `currency_handler.py` with exchange rate calculation and flexible currency support
- Enhanced `batch_processor.py` with automatic finalization

### 📁 New Output Files
1. **Main CSV**: Complete transaction data with exchange rates and account mapping
2. **Individual Card CSVs**: Separate files for each card (Post Date, Description, Amount, Target Account)
3. **Combined "Both" CSV**: Unified import file with automatic account assignment
   - BPI ECREDIT CARD → `Liabilities:Credit Card:BPI Mastercard:e-credit`
   - BPI GOLD REWARDS CARD → `Liabilities:Credit Card:BPI Mastercard:Gold`

### 🎯 Account Mapping Features
- **Known Pattern Matching**: Exact matches for common merchants (Apple, Google, Netflix, etc.)
- **Fuzzy String Matching**: Handles variations in merchant names with confidence scoring
- **Keyword-Based Rules**: Smart categorization using transaction description keywords
- **Philippines-Specific Patterns**: Support for local merchants (Grab, Metromart, Shopee, etc.)
- **Chart of Accounts Integration**: Maps against user's actual accounting chart
- **Manual Review Flagging**: Only 1.3% of transactions need manual review

### 💱 Enhanced Currency Support
- **Expanded Currency List**: PHP, USD, EUR, GBP, SGD, NZD, CAD, AUD, JPY, CHF, THB, HKD, KRW
- **Automatic Exchange Rates**: Calculated from actual transaction amounts
- **Flexible Symbol Handling**: Graceful fallback for unknown currencies
- **Exchange Rate Statistics**: Min, max, average rates per currency

### 🔧 Technical Improvements
- **Fuzzy Matching Library**: Added fuzzywuzzy for intelligent text matching
- **Modular Architecture**: Clean separation of concerns with shared post-processing
- **Enhanced Error Handling**: Better reporting and recovery from processing errors
- **Performance Optimization**: Efficient batch processing with detailed progress reporting
- **Comprehensive Testing**: Account mapping testing framework with real data validation

### 📊 Performance Improvements
- **Success Rate**: Increased from 94% to 98.7% automated processing
- **Account Mapping**: 98.7% automatic categorization vs 0% manual categorization
- **Processing Efficiency**: Single command generates all required import files
- **User Experience**: Streamlined workflow from PDF to accounting system

### 🛠️ Dependencies Added
- `fuzzywuzzy` - Fuzzy string matching for intelligent account mapping
- `python-levenshtein` - Fast string distance calculations

### 📚 Documentation Updates
- Updated README with 4-file output system and account mapping features
- Enhanced troubleshooting guide for account mapping issues
- Added development guide sections for account mapping customization
- Updated usage guide with new workflow description

### 🔄 Workflow Enhancements
**Before v2.0.0**: PDF → 1 CSV file (manual categorization required)
**After v2.0.0**: PDF → 4 CSV files (98.7% automatically categorized, ready for import)

### ⚠️ Breaking Changes
None - All existing functionality maintained while adding new features

### 🐛 Bug Fixes
- Improved date parsing for edge cases
- Enhanced PDF text normalization for better transaction extraction
- Fixed currency symbol handling for international transactions
- Improved batch processing error recovery

---

## [1.0.0] - 2025-05-25

### Added
- Initial release of BPI Statement Parser
- Multi-card support for BPI Gold Rewards and BPI eCredit cards
- Multi-currency transaction handling (PHP, USD, SGD, NZD)
- Batch processing with 94%+ success rate across 2023-2025 PDF formats
- Smart text normalization for PDF formatting inconsistencies
- Comprehensive diagnostic and troubleshooting tools
- Clean modular architecture with separated concerns
- Single PDF and batch processing modes
- Automatic currency conversion detection
- CSV export functionality for accounting software integration

### Technical Features
- PyPDF2-based text extraction with fallback support
- Regex-based transaction parsing with format detection
- Text normalization for handling PDF extraction variations
- Error handling and detailed reporting
- Diagnostic tools for troubleshooting failed PDFs

### Supported Formats
- BPI credit card statements from 2023-2025
- Both compact and spaced date formats
- Single-line and two-line foreign currency transactions
- Multiple card header format variations