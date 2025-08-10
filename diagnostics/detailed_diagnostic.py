# detailed_diagnostic.py - Check what's in each card section
import sys
sys.path.append('.')
from pdf_extractor import PDFExtractor
import re

def analyze_card_sections():
    """Analyze what's in each card section"""
    print("🔍 DETAILED CARD SECTION ANALYSIS")
    print("="*80)
    
    # Get PDF path from command line or use default
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "./data/input/Statement BPI Master 2023-10-12.pdf"
        print(f"Usage: python {sys.argv[0]} <pdf_path>")
        print(f"Using default: {pdf_path}")
    
    try:
        # Extract text
        extractor = PDFExtractor(pdf_path)
        text = extractor.extract_text()
        
        # Split by cards (same logic as parser)
        sections = {}
        lines = text.split('\n')
        current_card = None
        current_section = []
        
        for line in lines:
            line_upper = line.upper().strip()
            
            # Check for card headers
            if ('BPIGOLDREWARDS' in line_upper.replace(' ', '') or 
                'GOLD REWARDS' in line_upper):
                if current_card and current_section:
                    sections[current_card] = '\n'.join(current_section)
                current_card = 'BPI GOLD REWARDS CARD'
                current_section = [line]
            elif ('BPIECREDIT' in line_upper.replace(' ', '') or 
                  'ECREDIT CARD' in line_upper):
                if current_card and current_section:
                    sections[current_card] = '\n'.join(current_section)
                current_card = 'BPI ECREDIT CARD'
                current_section = [line]
            elif ('BPIEXPRESS CREDIT GOLDMASTERCARD' in line_upper or 
                  'BPI EXPRESS CREDIT GOLD MASTERCARD' in line_upper):
                if current_card and current_section:
                    sections[current_card] = '\n'.join(current_section)
                current_card = 'BPI GOLD REWARDS CARD'
                current_section = [line]
            elif ('BPIE-CREDIT' in line_upper or 
                  'BPI E-CREDIT' in line_upper) and 'MASTERCARD' not in line_upper:
                if current_card and current_section:
                    sections[current_card] = '\n'.join(current_section)
                current_card = 'BPI ECREDIT CARD'
                current_section = [line]
            elif current_card:
                current_section.append(line)
        
        # Add final section
        if current_card and current_section:
            sections[current_card] = '\n'.join(current_section)
        
        # Analyze each section
        for card_name, section_text in sections.items():
            print(f"\n{'='*60}")
            print(f"📋 CARD SECTION: {card_name}")
            print(f"{'='*60}")
            print(f"Section length: {len(section_text)} characters")
            print(f"\nFULL SECTION CONTENT:")
            print("-" * 40)
            print(section_text)
            print("-" * 40)
            
            # Look for transaction patterns
            print(f"\n🔍 TRANSACTION PATTERN ANALYSIS:")
            lines = section_text.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                print(f"\n  Line {i}: '{line}'")
                
                # Test against current patterns
                # Pattern 1: Single line
                pattern1 = r'^([A-Za-z]{3,9})(\d{1,2})\s+([A-Za-z]{3,9})(\d{1,2})\s+(.+?)\s+(-?\d{1,3}(?:,\d{3})*\.\d{2})$'
                if re.match(pattern1, line):
                    print(f"    ✓ Matches single-line pattern")
                else:
                    print(f"    ✗ No match for single-line pattern")
                
                # Pattern 2: Foreign currency first line
                pattern2 = r'^([A-Za-z]{3,9})(\d{1,2})\s+([A-Za-z]{3,9})(\d{1,2})\s+(.+?)\s+(US|SG|NZ)$'
                if re.match(pattern2, line):
                    print(f"    ✓ Matches foreign currency first line")
                
                # Look for date patterns
                if re.search(r'[A-Za-z]{3,9}\s*\d{1,2}', line):
                    print(f"    ✓ Contains date pattern")
                
                # Look for amounts
                if re.search(r'-?\d{1,3}(?:,\d{3})*\.\d{2}', line):
                    print(f"    ✓ Contains amount pattern")
                
                # Look for USD line
                if re.search(r'U\.S\.Dollar', line):
                    print(f"    ✓ USD line detected")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_card_sections()