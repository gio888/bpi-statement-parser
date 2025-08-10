#!/usr/bin/env python3
"""
Pre-flight Check Script for BPI Statement Parser
Runs before starting the web interface to catch common errors
"""

import sys
import os
from pathlib import Path

# Track errors and warnings
errors = []
warnings = []
info = []

def check_python_version():
    """Check Python version is 3.8+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        errors.append(f"Python 3.8+ required, found {version.major}.{version.minor}.{version.micro}")
    else:
        info.append(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")

def check_virtual_environment():
    """Check if running in virtual environment"""
    if not hasattr(sys, 'prefix'):
        warnings.append("Not running in virtual environment (recommended: source venv/bin/activate)")
    else:
        info.append(f"✓ Virtual environment: {sys.prefix}")

def check_dependencies():
    """Check all required dependencies are installed"""
    required_packages = [
        ('pandas', 'pandas'),
        ('PyPDF2', 'PyPDF2'),
        ('pdfplumber', 'pdfplumber'),
        ('flask', 'Flask'),
        ('flask_cors', 'Flask-CORS'),
        ('fuzzywuzzy', 'fuzzywuzzy'),
        ('openpyxl', 'openpyxl')
    ]
    
    missing = []
    for import_name, display_name in required_packages:
        try:
            __import__(import_name)
            info.append(f"✓ {display_name} installed")
        except ImportError:
            missing.append(display_name)
    
    if missing:
        errors.append(f"Missing dependencies: {', '.join(missing)}")
        errors.append("Run: pip install -r requirements.txt")

def check_project_structure():
    """Check required files and folders exist"""
    project_root = Path(__file__).parent
    
    required_files = [
        'src/web_app.py',
        'src/pdf_extractor.py',
        'src/transaction_parser.py',
        'src/currency_handler.py',
        'src/statement_finalizer.py',
        'src/config_loader.py',
        'static/index.html',
        'static/style.css',
        'static/app.js',
        'account_mapper.py'
    ]
    
    required_dirs = [
        'src',
        'static',
        'config_templates',
        'data/input',
        'data/output'
    ]
    
    # Check files
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            errors.append(f"Missing required file: {file_path}")
    
    # Check directories
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            if 'data' in dir_path:
                # Create data directories if missing
                full_path.mkdir(parents=True, exist_ok=True)
                warnings.append(f"Created missing directory: {dir_path}")
            else:
                errors.append(f"Missing required directory: {dir_path}")
    
    if not errors:
        info.append("✓ Project structure intact")

def check_configuration():
    """Check if configuration exists or needs setup"""
    project_root = Path(__file__).parent
    config_dir = project_root / "config"
    config_file = config_dir / "config.py"
    
    if not config_dir.exists():
        warnings.append("Personal configuration not found. Run 'python setup.py' to configure")
    elif not config_file.exists():
        warnings.append("config/config.py not found. Run 'python setup.py' to configure")
    else:
        info.append("✓ Personal configuration found")
        
        # Try to load config
        try:
            sys.path.insert(0, str(project_root / "src"))
            from config_loader import get_config
            config = get_config()
            
            # Check key configuration values
            pdf_folder = config.get('PDF_INPUT_FOLDER')
            if pdf_folder and not Path(pdf_folder).exists():
                warnings.append(f"PDF input folder doesn't exist: {pdf_folder}")
            
            info.append("✓ Configuration loads successfully")
        except Exception as e:
            errors.append(f"Configuration error: {e}")

def check_sample_pdf():
    """Check if there's a sample PDF for testing"""
    project_root = Path(__file__).parent
    input_dir = project_root / "data" / "input"
    
    pdf_files = list(input_dir.glob("*.pdf")) if input_dir.exists() else []
    
    if pdf_files:
        info.append(f"✓ Found {len(pdf_files)} PDF file(s) in data/input/")
    else:
        warnings.append("No PDF files found in data/input/ for testing")

def check_port_availability():
    """Check if port 8080 is available"""
    import socket
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8080))
    sock.close()
    
    if result == 0:
        errors.append("Port 8080 is already in use. Close other applications using this port")
    else:
        info.append("✓ Port 8080 is available")

def run_basic_import_test():
    """Try to import all main modules"""
    try:
        # Add src to path
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        # Try imports
        from pdf_extractor import PDFExtractor
        from transaction_parser import TransactionParser
        from currency_handler import CurrencyHandler
        from statement_finalizer import StatementFinalizer
        from config_loader import get_config
        
        info.append("✓ All core modules import successfully")
    except ImportError as e:
        errors.append(f"Module import failed: {e}")
    except Exception as e:
        errors.append(f"Unexpected import error: {e}")

def print_results():
    """Print all check results"""
    print("\n" + "="*60)
    print("🔍 BPI STATEMENT PARSER - PRE-FLIGHT CHECK")
    print("="*60)
    
    if info:
        print("\n✅ CHECKS PASSED:")
        for msg in info:
            print(f"  {msg}")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for msg in warnings:
            print(f"  {msg}")
    
    if errors:
        print("\n❌ ERRORS FOUND:")
        for msg in errors:
            print(f"  {msg}")
        print("\n🛑 Please fix errors before running the application")
    else:
        print("\n🎉 All critical checks passed!")
        print("You can now run: python run_web.py")
    
    print("="*60 + "\n")
    
    return len(errors) == 0

def main():
    """Run all pre-flight checks"""
    print("\nRunning pre-flight checks...")
    
    check_python_version()
    check_virtual_environment()
    check_dependencies()
    check_project_structure()
    check_configuration()
    check_sample_pdf()
    check_port_availability()
    run_basic_import_test()
    
    success = print_results()
    
    # Return appropriate exit code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()