# simple_diagnostic.py - Check actual extracted text
import sys
sys.path.append('.')
from pdf_extractor import PDFExtractor

def show_extracted_text(pdf_path, max_chars=2000):
    """Show exactly what text is being extracted"""
    print(f"🔍 EXTRACTING TEXT FROM: {pdf_path}")
    print("="*80)
    
    try:
        extractor = PDFExtractor(pdf_path)
        text = extractor.extract_text()
        
        print(f"Total characters extracted: {len(text)}")
        print(f"Total pages: {extractor.get_page_count()}")
        print("\n" + "="*80)
        print("FULL EXTRACTED TEXT:")
        print("="*80)
        print(text[:max_chars])
        if len(text) > max_chars:
            print(f"\n... (showing first {max_chars} of {len(text)} characters)")
        print("="*80)
        
        # Look for card headers manually
        print("\nMANUAL CARD HEADER SEARCH:")
        headers_to_find = [
            'BPI EXPRESS CREDIT GOLD MASTERCARD',
            'BPI E-CREDIT',
            'BPIGOLDREWARDS',
            'BPIECREDIT'
        ]
        
        text_upper = text.upper()
        for header in headers_to_find:
            if header in text_upper:
                print(f"  ✓ Found: {header}")
            else:
                print(f"  ✗ Missing: {header}")
        
        # Look for any lines with "BPI"
        print("\nALL LINES CONTAINING 'BPI':")
        lines = text.split('\n')
        bpi_lines = [line.strip() for line in lines if 'BPI' in line.upper()]
        for line in bpi_lines[:10]:  # Show first 10
            print(f"  '{line}'")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Get PDF paths from command line or use defaults
    if len(sys.argv) > 2:
        failed_pdf = sys.argv[1]
        working_pdf = sys.argv[2]
    else:
        failed_pdf = "./data/input/Statement BPI Master 2023-10-12.pdf"
        working_pdf = "./data/input/Statement BPI Master 2025-05-12.pdf"
        print(f"Usage: python {sys.argv[0]} <failed_pdf> <working_pdf>")
        print(f"Using defaults: {failed_pdf} and {working_pdf}")
    
    show_extracted_text(failed_pdf)
    
    print("\n" + "="*100)
    print("COMPARISON WITH WORKING FILE:")
    print("="*100)
    
    show_extracted_text(working_pdf, max_chars=1000)  # Shorter for comparison