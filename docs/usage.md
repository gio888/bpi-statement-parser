# BPI Statement Parser - Usage Guide

## Quick Start

1. **Single PDF Processing**
   ```bash
   python main.py
   # Choose option 1
   ```

2. **Batch Processing Multiple PDFs**
   ```bash
   python main.py  
   # Choose option 2
   ```

## Troubleshooting

If you encounter issues:

1. **Run diagnostics on failed PDFs**
   ```bash
   python diagnostics/check_failed.py
   ```

2. **Check batch processing issues**
   ```bash
   python diagnostics/batch_diagnostic.py
   ```

3. **Test parser on specific PDF**
   ```bash
   python tests/test_parser_fix.py
   ```

## Output

Processed transactions are saved as CSV files in `data/output/` folder.
