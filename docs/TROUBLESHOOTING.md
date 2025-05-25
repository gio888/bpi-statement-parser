# Troubleshooting Guide

## Common Issues and Solutions

### 1. "No transactions found" Error

**Symptoms**: Parser runs but extracts 0 transactions from a PDF

**Causes & Solutions**:

#### A. PDF Encoding Issues
```bash
# Check what text is being extracted
python diagnostics/check_failed.py
```

If you see garbled text like `/Cf1/Cf0/Cf2`:
- **Solution**: Reformat the PDF using Preview (Export as PDF) or online PDF tools
- **Alternative**: Try `python diagnostics/try_pdfplumber.py`

#### B. Card Header Not Detected
```bash
# Check card header detection
python diagnostics/detailed_diagnostic.py
```

If card headers are missing:
- **2023 Format**: Look for `BPI EXPRESS CREDIT GOLD MASTERCARD` or `BPI E-CREDIT`
- **2025 Format**: Look for `BPIGOLDREWARDS CARD` or `BPIECREDIT CARD`
- **Solution**: Update card header patterns in `transaction_parser.py`

#### C. Transaction Format Variations
```bash
# Analyze transaction patterns
python diagnostics/debug_two_line.py
```

Common format issues:
- **Different date spacing**: `October1` vs `October 1`
- **Currency line variations**: `U.S.Dollar` vs `US Dollar`
- **Amount formatting**: `2,337.48` vs `2 , 337 . 48`

**Solution**: The text normalizer should handle these automatically

### 2. Batch Processing Failures

**Symptoms**: Some PDFs process successfully, others fail

**Diagnosis**:
```bash
python diagnostics/batch_diagnostic.py
```

**Common Issues**:

#### A. Mixed PDF Formats
- **Problem**: Different years have different formats
- **Solution**: Parser already handles 2023-2025 formats
- **Check**: Verify normalization is working

#### B. File Access Issues
- **Problem**: PDF files are locked or corrupted
- **Solution**: Check file permissions, try opening manually

#### C. Large File Issues
- **Problem**: Very large PDFs cause memory issues
- **Solution**: Process in smaller batches

### 3. Currency Detection Issues

**Symptoms**: Foreign transactions showing as PHP

**Diagnosis**:
```bash
# Check currency detection patterns
python diagnostics/debug_missing.py
```

**Solutions**:

#### A. Missing Country Codes
- **Add new country codes** to parser
- **Update currency mappings**

#### B. Currency Line Format Changes
- **Check for**: `U.S. Dollar`, `Singapore Dollar`, etc.
- **Update patterns** in currency detection

### 4. Date Conversion Issues

**Symptoms**: Dates showing as "October 1" instead of "2023-10-01"

**Cause**: Currency handler not detecting correct year

**Solution**:
```python
# In currency_handler.py, update year detection logic
def _detect_statement_year(self, df):
    # Add logic to detect year from PDF content
    # or use filename date
```

### 5. Performance Issues

**Symptoms**: Very slow processing or high memory usage

**Solutions**:

#### A. Large Batch Processing
```bash
# Process in smaller batches
# Set cutoff date to limit files
```

#### B. Memory Usage
- **Monitor**: Use Activity Monitor / Task Manager
- **Solution**: Process PDFs individually instead of loading all

### 6. Import Issues into Accounting Software

**Symptoms**: CSV doesn't import correctly

**Common Issues**:

#### A. Date Format
- **Problem**: Software expects different date format
- **Solution**: Update date formatting in `currency_handler.py`

#### B. Currency Columns
- **Problem**: Software expects different currency format
- **Solution**: Modify CSV output format

#### C. Encoding Issues
- **Problem**: Special characters not displaying correctly
- **Solution**: Save CSV with UTF-8 encoding

## Diagnostic Workflow

### Step 1: Initial Diagnosis
```bash
# Start with basic PDF check
python diagnostics/check_failed.py
```

### Step 2: Detailed Analysis
```bash
# If Step 1 shows readable text
python diagnostics/detailed_diagnostic.py
```

### Step 3: Pattern Testing
```bash
# If card headers found but no transactions
python diagnostics/debug_two_line.py
python diagnostics/debug_missing.py
```

### Step 4: Batch Analysis
```bash
# For batch processing issues
python diagnostics/batch_diagnostic.py
```

## Prevention Tips

### 1. PDF Quality
- **Use high-quality PDFs** from BPI online banking
- **Avoid scanned copies** when possible
- **Keep original PDFs** as backup

### 2. Regular Testing
- **Test new PDFs** individually before batch processing
- **Keep sample PDFs** for different time periods
- **Monitor success rates** over time

### 3. Backup Strategy
- **Keep original PDFs** separate from processed ones
- **Version control** your parser modifications
- **Export CSV files** regularly

## Advanced Troubleshooting

### Custom Diagnostic Script
Create custom diagnostic for specific issues:

```python
# custom_diagnostic.py
import sys
sys.path.append('src')
from pdf_extractor import PDFExtractor

def custom_debug(pdf_path):
    extractor = PDFExtractor(pdf_path)
    text = extractor.extract_text()
    
    # Add your specific checks here
    print("Custom analysis:")
    # Check for specific patterns, text, etc.
    
if __name__ == "__main__":
    custom_debug("path/to/problematic.pdf")
```

### Manual Text Inspection
For very problematic PDFs:

1. **Extract text manually**:
   ```bash
   python -c "
   from src.pdf_extractor import PDFExtractor
   text = PDFExtractor('problem.pdf').extract_text()
   print(text)
   " > extracted_text.txt
   ```

2. **Analyze patterns manually**
3. **Create specific regex patterns**
4. **Test with sample data**

### Performance Profiling
For performance issues:

```python
import cProfile
import pstats

# Profile the parser
cProfile.run('parser.parse_transactions(text)', 'profile_stats')
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative').print_stats(10)
```

## Getting Help

### 1. Check Existing Issues
- Review GitHub issues for similar problems
- Search documentation for keywords

### 2. Provide Detailed Information
When reporting issues:
- **PDF format/year**: Which statement format
- **Error messages**: Full error text
- **Diagnostic output**: Results from diagnostic tools
- **Sample data**: Anonymized transaction examples

### 3. Create Minimal Reproduction
- **Isolate the problem**: Single PDF, specific transaction
- **Share diagnostic output**: From relevant tools
- **Include context**: What was expected vs actual result

## Emergency Recovery

### If Parser Completely Breaks
1. **Revert to working version**: Use git to go back
2. **Use backup data**: Process with known working setup
3. **Manual processing**: Extract data manually if needed

### If Data Loss Occurs
1. **Check backup folders**: Look for auto-generated backups
2. **Recover from source**: Re-process original PDFs
3. **Version control**: Use git history to recover code