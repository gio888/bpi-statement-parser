#!/usr/bin/env python3
"""
Test Runner for BPI Statement Parser
Runs all tests and provides a summary report
"""

import sys
import os
import unittest
from pathlib import Path
import time

def run_tests():
    """Run all test suites"""
    print("\n" + "="*70)
    print("🧪 BPI STATEMENT PARSER - TEST SUITE")
    print("="*70)
    
    # Add project to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Create test loader
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Test categories
    test_categories = [
        ('Unit Tests - Config Loader', 'tests.test_config_loader'),
        ('Unit Tests - Web Application', 'tests.test_web_app'),
        ('Integration Tests - Pipeline', 'tests.test_integration'),
    ]
    
    # Track results
    total_tests = 0
    failed_modules = []
    
    # Run each test category
    for category_name, module_name in test_categories:
        print(f"\n📋 Running: {category_name}")
        print("-" * 50)
        
        try:
            # Load tests from module
            module_tests = loader.loadTestsFromName(module_name)
            
            # Run tests
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(module_tests)
            
            # Track results
            total_tests += result.testsRun
            
            if not result.wasSuccessful():
                failed_modules.append(category_name)
                
            # Print summary for this category
            print(f"\n  Tests run: {result.testsRun}")
            print(f"  Failures: {len(result.failures)}")
            print(f"  Errors: {len(result.errors)}")
            print(f"  Skipped: {len(result.skipped)}")
            
        except Exception as e:
            print(f"  ❌ Failed to run: {e}")
            failed_modules.append(category_name)
    
    # Print overall summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    print(f"\nTotal tests run: {total_tests}")
    
    if failed_modules:
        print(f"\n❌ Failed test categories:")
        for module in failed_modules:
            print(f"  - {module}")
        return False
    else:
        print("\n✅ All tests passed successfully!")
        return True

def run_quick_smoke_test():
    """Run a quick smoke test of critical functionality"""
    print("\n" + "="*70)
    print("💨 QUICK SMOKE TEST")
    print("="*70)
    
    errors = []
    
    # Test 1: Can we import core modules?
    print("\n1. Testing core module imports...")
    try:
        from src.pdf_extractor import PDFExtractor
        from src.transaction_parser import TransactionParser
        from src.currency_handler import CurrencyHandler
        from src.config_loader import get_config
        print("   ✓ Core modules import successfully")
    except ImportError as e:
        errors.append(f"Module import failed: {e}")
        print(f"   ✗ {e}")
    
    # Test 2: Can we initialize key components?
    print("\n2. Testing component initialization...")
    try:
        from src.transaction_parser import TransactionParser
        from src.currency_handler import CurrencyHandler
        
        parser = TransactionParser()
        handler = CurrencyHandler()
        print("   ✓ Components initialize successfully")
    except Exception as e:
        errors.append(f"Component initialization failed: {e}")
        print(f"   ✗ {e}")
    
    # Test 3: Can Flask app be created?
    print("\n3. Testing Flask app creation...")
    try:
        from src.web_app import app
        test_client = app.test_client()
        response = test_client.get('/api/health')
        if response.status_code == 200:
            print("   ✓ Flask app responds to health check")
        else:
            errors.append(f"Health check returned {response.status_code}")
            print(f"   ✗ Health check failed")
    except Exception as e:
        errors.append(f"Flask app creation failed: {e}")
        print(f"   ✗ {e}")
    
    # Test 4: Check configuration system
    print("\n4. Testing configuration system...")
    try:
        from src.config_loader import get_config
        config = get_config()
        if config.get('PRIMARY_CURRENCY') == 'PHP':
            print("   ✓ Configuration loads with correct defaults")
        else:
            errors.append("Configuration has unexpected values")
            print("   ✗ Configuration values incorrect")
    except Exception as e:
        errors.append(f"Configuration system failed: {e}")
        print(f"   ✗ {e}")
    
    # Print smoke test results
    print("\n" + "-"*50)
    if errors:
        print("❌ Smoke test failed with errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ Smoke test passed - basic functionality working!")
        return True

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run tests for BPI Statement Parser')
    parser.add_argument('--quick', action='store_true', 
                       help='Run quick smoke test only')
    parser.add_argument('--full', action='store_true', 
                       help='Run full test suite (default)')
    
    args = parser.parse_args()
    
    # Default to full if nothing specified
    if not args.quick and not args.full:
        args.full = True
    
    success = True
    
    # Run requested tests
    if args.quick:
        success = run_quick_smoke_test()
    
    if args.full:
        # Run pre-flight check first
        print("\n🔍 Running pre-flight check first...")
        try:
            from preflight_check import main as preflight_main
            # Capture the preflight check but don't exit
            try:
                preflight_main()
            except SystemExit:
                pass
        except:
            print("Skipping pre-flight check")
        
        # Run full test suite
        success = run_tests() and success
    
    # Final message
    print("\n" + "="*70)
    if success:
        print("🎉 All tests passed! The application is ready to use.")
        print("\nTo start the web interface, run:")
        print("  python run_web.py")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        print("\nFor quick debugging, run:")
        print("  python run_tests.py --quick")
    print("="*70 + "\n")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()