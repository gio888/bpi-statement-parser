# Changelog

All notable changes to this project will be documented in this file.

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
- Automatic currency conversion and exchange rate detection
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
