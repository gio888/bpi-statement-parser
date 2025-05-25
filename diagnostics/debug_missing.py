# debug_missing.py - Check why foreign currency and payment transactions are missing
import sys
sys.path.append('.')
from pdf_extractor import PDFExtractor
import re

def debug_missing_transactions():
    """Debug why some transactions are not being parsed"""
    print("🔍 DEBUGGING MISSING TRANSACTIONS")
    print("="*60)
    
    pdf_path = "/home/user/Library/CloudStorage/GoogleDrive-user@example.com/My Drive/Money/BPI/Statement BPI Master 2023-10-12.pdf"
    
    try:
        # Extract text
        extractor = PDFExtractor(pdf_path)
        text = extractor.extract_text()
        
        # Get the e-credit section (where we know there are foreign transactions)
        lines = text.split('\n')
        in_ecredit = False
        ecredit_lines = []
        
        for line in lines:
            line_upper = line.upper().strip()
            if 'BPIE-CREDIT' in line_upper:
                in_ecredit = True
                continue
            elif in_ecredit and ('BPI' in line_upper or '=== PAGE' in line):
                # End of section
                break
            elif in_ecredit:
                ecredit_lines.append(line.strip())
        
        print(f"Found {len(ecredit_lines)} lines in e-credit section")
        
        # Test specific problematic lines
        test_lines = [
            "October 1 October 2 Payment -Thank You -21,401.07",  # Payment - should work
            "September 15 September 18 Backblaze.Com SanMateo US",  # Foreign line 1
            "U.S.Dollar 40.42 2,337.48",  # Foreign line 2
            "September 14 September 14 Reversal-Finance Charges -699.18"  # Regular transaction
        ]
        
        print(f"\n🧪 TESTING SPECIFIC LINES:")
        print("-" * 40)
        
        for line in test_lines:
            print(f"\nTesting: '{line}'")
            
            # Test single line pattern
            pattern = r'^([A-Za-z]{3,9})\s+(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{1,2})\s+(.+?)\s+(-?\d{1,3}(?:,\d{3})*\.\d{2})$'
            if re.match(pattern, line):
                print("  ✓ Matches single-line pattern")
            else:
                print("  ✗ No match for single-line pattern")
            
            # Test foreign currency first line
            foreign_pattern = r'^([A-Za-z]{3,9})\s+(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{1,2})\s+(.+?)\s+(US|SG|NZ)$'
            if re.match(foreign_pattern, line):
                print("  ✓ Matches foreign currency first line")
            
            # Test USD second line
            usd_pattern = r'^U\.S\.?\s*Dollar\s+([\d.,]+)\s+(\d{1,3}(?:,\d{3})*\.\d{2})$'
            if re.match(usd_pattern, line):
                print("  ✓ Matches USD second line")
        
        print(f"\n🔍 SCANNING ALL E-CREDIT LINES:")
        print("-" * 40)
        
        for i, line in enumerate(ecredit_lines):
            if not line:
                continue
                
            print(f"\nLine {i}: '{line}'")
            
            # Check what patterns match
            patterns = [
                (r'^([A-Za-z]{3,9})\s+(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{1,2})\s+(.+?)\s+(-?\d{1,3}(?:,\d{3})*\.\d{2})$', 'Single line'),
                (r'^([A-Za-z]{3,9})\s+(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{1,2})\s+(.+?)\s+(US|SG|NZ)$', 'Foreign first'),
                (r'^U\.S\.?\s*Dollar\s+([\d.,]+)\s+(\d{1,3}(?:,\d{3})*\.\d{2})$', 'USD second')
            ]
            
            matched = False
            for pattern, name in patterns:
                if re.match(pattern, line):
                    print(f"  ✓ Matches: {name}")
                    matched = True
            
            if not matched and ('September' in line or 'October' in line or 'Dollar' in line):
                print(f"  ❌ UNMATCHED transaction-like line!")
                
                # Try to understand why it doesn't match
                if re.search(r'[A-Za-z]{3,9}\s+\d{1,2}', line):
                    print(f"    - Has date pattern")
                if re.search(r'-?\d{1,3}(?:,\d{3})*\.\d{2}', line):
                    print(f"    - Has amount pattern")
                if 'US' in line or 'SG' in line or 'NZ' in line:
                    print(f"    - Has country code")
                if 'Dollar' in line:
                    print(f"    - Has Dollar keyword")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_missing_transactions()