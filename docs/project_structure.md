# Project Structure

## Core Production Code (`src/`)
- `pdf_extractor.py` - PDF text extraction
- `transaction_parser.py` - Transaction parsing logic  
- `currency_handler.py` - Currency processing
- `batch_processor.py` - Batch processing
- `main_enhanced.py` - Menu system

## Diagnostic Tools (`diagnostics/`)
- `batch_diagnostic.py` - Batch processing diagnostics
- `pdf_diagnostic.py` - PDF content inspection
- `check_failed.py` - Failed PDF analysis
- `debug_*.py` - Various debugging utilities

## Tests (`tests/`)
- `test_parser_fix.py` - Parser testing
- `test_reformatted.py` - Reformatted PDF testing
- `test_simple_parser.py` - Simple parser testing

## Experimental (`experimental/`)
- `pdf_normalizer.py` - Text normalization experiments
- `currency_detector.py` - Generic currency detection
- `simple_normalizer.py` - Simple normalizer prototype

## Usage
```bash
# Run main application
python main.py

# Run diagnostics
python diagnostics/batch_diagnostic.py

# Run tests  
python tests/test_parser_fix.py
```
