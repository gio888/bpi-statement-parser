# Development Guide

## Architecture Overview

The BPI Statement Parser uses a modular architecture designed for maintainability and extensibility.

### Core Components

#### 1. PDF Extractor (`src/pdf_extractor.py`)
- **Purpose**: Extract raw text from PDF files
- **Method**: Uses PyPDF2 for reliable text extraction
- **Handles**: Multiple page PDFs, different encodings
- **Fallback**: Supports pdfplumber for problematic PDFs

```python
extractor = PDFExtractor("path/to/statement.pdf")
text = extractor.extract_text()
```

#### 2. Transaction Parser (`src/transaction_parser.py`)
- **Purpose**: Parse transactions from extracted text
- **Features**: 
  - Text normalization for PDF inconsistencies
  - Multi-format support (2023-2025 PDF variations)
  - Card header detection
  - Single-line and two-line transaction parsing

```python
parser = TransactionParser()
transactions = parser.parse_transactions(text)
```

#### 3. Currency Handler (`src/currency_handler.py`)
- **Purpose**: Process currency information and format output
- **Features**:
  - Date conversion and formatting
  - Multi-currency support
  - CSV output formatting
  - Exchange rate calculation

#### 4. Batch Processor (`src/batch_processor.py`)
- **Purpose**: Process multiple PDFs in batch
- **Features**:
  - Date filtering
  - Progress tracking
  - Error handling and reporting
  - Combined CSV output

## Key Design Decisions

### 1. Text Normalization Approach
Instead of complex regex patterns for every PDF variation, we normalize text first:

```python
def normalize_line(self, line: str) -> str:
    # Fix spacing issues
    text = re.sub(r'\s+', ' ', line.strip())
    # Fix currency formatting
    text = self._fix_currency_dots(text)
    # Fix date formatting  
    text = self._fix_month_spacing(text)
    return text
```

**Benefits**:
- Handles PDF extraction inconsistencies
- Simpler parsing logic
- More reliable across different PDF formats

### 2. Modular Architecture
Each component has a single responsibility:
- **PDFExtractor**: Only text extraction
- **TransactionParser**: Only transaction parsing
- **CurrencyHandler**: Only currency processing
- **BatchProcessor**: Only batch orchestration

### 3. Error Handling Strategy
- **Continue on failure**: Process other files even if one fails
- **Detailed reporting**: Show exactly what failed and why
- **Diagnostic tools**: Separate tools for troubleshooting

## Transaction Parsing Logic

### Format Detection
The parser handles two main PDF formats:

#### 2025 Format (Single-line)
```
May1 May2 Payment -Thank You -13,544.89
```

#### 2023 Format (Spaced dates)
```
October 1 October 2 Payment -Thank You -905.60
```

#### Foreign Currency (Two-line)
```
September 15 September 18 Backblaze.Com SanMateo US
U.S.Dollar 40.42 2,337.48
```

### Card Header Detection
Flexible detection handles variations:
- `BPIGOLDREWARDS CARD`
- `BPI GOLD REWARDS CARD` 
- `BPIEXPRESS CREDIT GOLDMASTERCARD`
- `BPI E-CREDIT`
- `BPIE-CREDIT`

### Text Normalization Rules
1. **Currency names**: `U . S . Dollar` → `U.S.Dollar`
2. **Date spacing**: `October1` → `October 1`
3. **Amount formatting**: `2 , 337 . 48` → `2,337.48`

## Adding New Features

### Supporting New Currency
1. Add currency code to known patterns
2. Update country code mapping
3. Add currency symbol for display

### Supporting New PDF Format
1. Analyze format with diagnostic tools
2. Add normalization rules if needed
3. Update card header detection
4. Test with sample PDFs

### Adding New Transaction Type
1. Identify transaction pattern
2. Add regex pattern to parser
3. Test with sample data
4. Update skip patterns if needed

## Testing Strategy

### Unit Tests
```bash
python tests/test_parser_fix.py        # Test parser on known PDF
python tests/test_reformatted.py       # Test reformatted PDFs
python tests/test_simple_parser.py     # Test simple parser logic
```

### Diagnostic Tools
```bash
python diagnostics/batch_diagnostic.py      # Batch processing issues
python diagnostics/check_failed.py          # Failed PDF analysis
python diagnostics/pdf_diagnostic.py        # PDF content inspection
```

### Performance Testing
- Test with large batch of PDFs
- Measure processing time per PDF
- Monitor memory usage with large files

## Code Style Guidelines

### Naming Conventions
- **Classes**: PascalCase (`TransactionParser`)
- **Functions**: snake_case (`parse_transactions`)
- **Variables**: snake_case (`transaction_date`)
- **Constants**: UPPER_CASE (`SKIP_PATTERNS`)

### Documentation
- Docstrings for all public methods
- Inline comments for complex logic
- README updates for new features

### Error Handling
```python
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    return default_value
```

## Performance Considerations

### Memory Usage
- Process PDFs one at a time
- Don't keep all transactions in memory for large batches
- Stream CSV output for large datasets

### Processing Speed
- PyPDF2 is faster than pdfplumber for most PDFs
- Text normalization is lightweight
- Regex compilation is cached

### Scalability
- Batch size limits prevent memory issues
- Progress reporting for user feedback
- Parallel processing potential for future enhancement

## Debugging Tips

### Common Issues
1. **No transactions found**: Check card header detection
2. **Wrong currency**: Check currency patterns
3. **Malformed dates**: Check date normalization
4. **Missing amounts**: Check amount regex patterns

### Debug Process
1. Use `pdf_diagnostic.py` to see raw text
2. Check if card headers are detected
3. Verify transaction patterns match
4. Test normalization on problematic lines

### Logging
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Features
- [ ] OCR support for scanned PDFs
- [ ] More currency support
- [ ] PDF validation before processing
- [ ] Configuration file support
- [ ] GUI interface
- [ ] API endpoint for integration

### Technical Debt
- [ ] Add comprehensive unit tests
- [ ] Improve error messages
- [ ] Add configuration validation
- [ ] Performance profiling
- [ ] Memory usage optimization

## Release Process

1. **Testing**: Run full test suite
2. **Documentation**: Update README and docs
3. **Version**: Update version numbers
4. **Git**: Create release tag
5. **GitHub**: Create release with changelog