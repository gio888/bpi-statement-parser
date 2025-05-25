#!/bin/bash

# reorganize_project.sh - Clean up BPI Statement Parser project structure
set -e  # Exit on any error

echo "🔧 BPI Statement Parser - Project Reorganization"
echo "================================================="

# Check if we're in the right directory
if [ ! -d "src" ] || [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   (Should contain 'src' folder and 'main.py')"
    exit 1
fi

echo "📁 Creating new directory structure..."

# Create new directories
mkdir -p diagnostics
mkdir -p tests  
mkdir -p experimental
mkdir -p docs
mkdir -p data/input

echo "✓ Created directories: diagnostics, tests, experimental, docs"

echo ""
echo "📦 Moving diagnostic files..."

# Move diagnostic files to diagnostics/
diagnostic_files=(
    "batch_diagnostic.py"
    "enhanced_batch_diagnostic.py" 
    "pdf_diagnostic.py"
    "detailed_diagnostic.py"
    "simple_diagnostic.py"
    "check_failed.py"
    "debug_missing.py"
    "debug_two_line.py"
    "check_skip_patterns.py"
)

for file in "${diagnostic_files[@]}"; do
    if [ -f "src/$file" ]; then
        mv "src/$file" "diagnostics/"
        echo "  ✓ Moved $file"
    else
        echo "  ⚠️  $file not found (skipping)"
    fi
done

echo ""
echo "🧪 Moving test files..."

# Move test files to tests/
test_files=(
    "test_parser_fix.py"
    "test_reformatted.py" 
    "test_simple_parser.py"
)

for file in "${test_files[@]}"; do
    if [ -f "src/$file" ]; then
        mv "src/$file" "tests/"
        echo "  ✓ Moved $file"
    else
        echo "  ⚠️  $file not found (skipping)"
    fi
done

# Move test_setup.py from root if it exists
if [ -f "test_setup.py" ]; then
    mv "test_setup.py" "tests/"
    echo "  ✓ Moved test_setup.py"
fi

echo ""
echo "🔬 Moving experimental files..."

# Move experimental files to experimental/
experimental_files=(
    "pdf_normalizer.py"
    "simple_normalizer.py"
    "currency_detector.py"
    "utils.py"
)

for file in "${experimental_files[@]}"; do
    if [ -f "src/$file" ]; then
        mv "src/$file" "experimental/"
        echo "  ✓ Moved $file"
    else
        echo "  ⚠️  $file not found (skipping)"
    fi
done

echo ""
echo "📚 Moving old files to archive..."

# Move old files to archive/
old_files=(
    "transaction_parser_old.py"
    "main_modular.py"
)

for file in "${old_files[@]}"; do
    if [ -f "src/$file" ]; then
        mv "src/$file" "archive/"
        echo "  ✓ Moved $file to archive"
    else
        echo "  ⚠️  $file not found (skipping)"
    fi
done

echo ""
echo "📄 Creating __init__.py files..."

# Create __init__.py files
touch diagnostics/__init__.py
touch tests/__init__.py  
touch experimental/__init__.py
echo "  ✓ Created __init__.py files"

echo ""
echo "📁 Organizing data folder..."

# Move sample PDF to data/input if it exists
if [ -f "data/Statement BPI Master 2025-05-12.pdf" ]; then
    mv "data/Statement BPI Master 2025-05-12.pdf" "data/input/"
    echo "  ✓ Moved sample PDF to data/input/"
fi

# Move CSV files if they exist in wrong location
if [ -f "data/Statement BPI Master 2025-05-12.csv" ]; then
    mv "data/Statement BPI Master 2025-05-12.csv" "data/output/"
    echo "  ✓ Moved CSV to data/output/"
fi

echo ""
echo "🧹 Cleaning up src/ folder..."

# List remaining files in src/
echo "  📋 Core files remaining in src/:"
ls -la src/ | grep -v __pycache__ | grep "\.py$" | awk '{print "    ✓ " $9}'

echo ""
echo "📝 Creating quick reference files..."

# Create a quick reference for the new structure
cat > docs/project_structure.md << 'EOF'
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
EOF

# Create a simple usage guide
cat > docs/usage.md << 'EOF'
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
EOF

echo "  ✓ Created documentation files"

echo ""
echo "✅ REORGANIZATION COMPLETE!"
echo "=========================="
echo ""
echo "📁 New project structure:"
echo "   src/ - Core production code (5 files)"
echo "   diagnostics/ - Troubleshooting tools (9 files)"  
echo "   tests/ - Test scripts (3-4 files)"
echo "   experimental/ - Experimental code (4 files)"
echo "   archive/ - Old/unused code"
echo "   docs/ - Documentation"
echo ""
echo "🚀 Your project is now organized and ready for production!"
echo ""
echo "Next steps:"
echo "1. Test that main.py still works: python main.py"
echo "2. Check docs/usage.md for updated usage instructions"
echo "3. Use diagnostics/ folder when troubleshooting"
echo ""
echo "All import paths should still work correctly."