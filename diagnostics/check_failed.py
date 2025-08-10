# check_failed.py - Quick diagnostic for the failed PDF
import sys
sys.path.append('.')
from pdf_extractor import PDFExtractor

def check_failed_pdf():
    """Check what's in the failed 2024-08-12 PDF"""
    print("🔍 CHECKING FAILED PDF: 2024-08-12")
    print("="*60)
    
    # Get PDF path from command line or use default
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "./data/input/Statement BPI Master 2024-08-12.pdf"
        print(f"Usage: python {sys.argv[0]} <pdf_path>")
        print(f"Using default: {pdf_path}")
    
    try:
        extractor = PDFExtractor(pdf_path)
        text = extractor.extract_text()
        
        print(f"📄 Basic Info:")
        print(f"  Total characters: {len(text)}")
        print(f"  Total pages: {extractor.get_page_count()}")
        
        print(f"\n📋 First 1000 characters:")
        print("-" * 50)
        print(text[:1000])
        print("-" * 50)
        
        print(f"\n🔍 Looking for card headers:")
        headers_to_check = [
            'BPI', 'GOLD', 'REWARDS', 'ECREDIT', 'MASTERCARD', 'CREDIT'
        ]
        
        for header in headers_to_check:
            if header.upper() in text.upper():
                print(f"  ✓ Found: {header}")
            else:
                print(f"  ✗ Missing: {header}")
        
        print(f"\n📝 All lines containing 'BPI':")
        lines = text.split('\n')
        bpi_lines = [line.strip() for line in lines if 'BPI' in line.upper()]
        for i, line in enumerate(bpi_lines[:10], 1):
            print(f"  {i}. '{line}'")
        
        print(f"\n🔍 Looking for transaction patterns:")
        transaction_indicators = [
            'Payment', 'Apple', 'Google', 'Netflix', 'Transaction', 'Amount'
        ]
        
        for indicator in transaction_indicators:
            count = text.upper().count(indicator.upper())
            print(f"  {indicator}: {count} occurrences")
        
        # Check if it's a different format entirely
        print(f"\n🤔 Format analysis:")
        if len(text) > 40000:
            print("  📄 Very large file - might be a different format")
        if 'STATEMENT' not in text.upper():
            print("  ⚠️  No 'STATEMENT' found - might not be a statement")
        if text.count('\n') < 50:
            print("  ⚠️  Very few line breaks - might be malformed extraction")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_failed_pdf()