# batch_diagnostic.py - Troubleshoot batch PDF extraction
import os
import re
from datetime import datetime, date
import sys
sys.path.append('src')

from pdf_extractor import PDFExtractor

def diagnose_batch_pdfs():
    """Diagnose PDF extraction issues in batch"""
    print("=" * 80)
    print("BATCH PDF DIAGNOSTIC TOOL")
    print("=" * 80)
    
    # Configuration - get from command line or use default
    if len(sys.argv) > 1:
        pdf_folder = sys.argv[1]
    else:
        pdf_folder = "./data/input/"
        print(f"Usage: python {sys.argv[0]} <pdf_folder>")
        print(f"Using default folder: {pdf_folder}")
    
    # Get cutoff date
    while True:
        try:
            date_str = input("\nEnter cutoff date (YYYY-MM-DD) for testing: ").strip()
            cutoff_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            break
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD")
    
    # Find PDFs
    pattern = r'^Statement BPI Master (\d{4}-\d{2}-\d{2})\.pdf$'
    matching_files = []
    
    for filename in os.listdir(pdf_folder):
        match = re.match(pattern, filename, re.IGNORECASE)
        if match:
            file_date = datetime.strptime(match.group(1), "%Y-%m-%d").date()
            if file_date >= cutoff_date:
                matching_files.append({
                    'filename': filename,
                    'statement_date': file_date,
                    'full_path': os.path.join(pdf_folder, filename)
                })
    
    matching_files.sort(key=lambda x: x['statement_date'])
    
    print(f"\nFound {len(matching_files)} PDFs to diagnose")
    
    # Ask which files to check
    print("\nOptions:")
    print("1. Check all files")
    print("2. Check first 3 files") 
    print("3. Check failed files from your batch run")
    print("4. Check specific file")
    
    choice = input("Select option (1-4): ").strip()
    
    files_to_check = []
    
    if choice == "1":
        files_to_check = matching_files
    elif choice == "2":
        files_to_check = matching_files[:3]
    elif choice == "3":
        # Failed files from the batch run
        failed_names = [
            "Statement BPI Master 2023-10-12.pdf",
            "Statement BPI Master 2023-11-12.pdf", 
            "Statement BPI Master 2023-12-12.pdf",
            "Statement BPI Master 2024-01-14.pdf",
            "Statement BPI Master 2024-02-12.pdf",
            "Statement BPI Master 2024-03-12.pdf"
        ]
        files_to_check = [f for f in matching_files if f['filename'] in failed_names]
    elif choice == "4":
        filename = input("Enter filename: ").strip()
        files_to_check = [f for f in matching_files if f['filename'] == filename]
        if not files_to_check:
            print("File not found in matching list")
            return
    
    # Process each file
    extractor = PDFExtractor("")
    
    for i, file_info in enumerate(files_to_check, 1):
        filename = file_info['filename']
        file_path = file_info['full_path']
        
        print(f"\n" + "="*80)
        print(f"DIAGNOSING {i}/{len(files_to_check)}: {filename}")
        print(f"Date: {file_info['statement_date']}")
        print("="*80)
        
        try:
            extractor.file_path = file_path
            text = extractor.extract_text()
            
            print(f"✓ Total extracted text: {len(text)} characters")
            
            # Show first 500 characters
            print(f"\nFirst 500 characters:")
            print("-" * 50)
            print(text[:500])
            print("-" * 50)
            
            # Look for card headers
            print(f"\nCard header search:")
            card_headers = ['BPIGOLDREWARDS', 'BPIECREDIT', 'BPI GOLD', 'BPI ECREDIT']
            for header in card_headers:
                if header in text.upper().replace(' ', ''):
                    print(f"  ✓ Found: {header}")
                else:
                    print(f"  ✗ Missing: {header}")
            
            # Look for transaction patterns
            print(f"\nTransaction pattern search:")
            
            # Look for date patterns
            date_patterns = [
                r'[A-Za-z]{3,9}\d{1,2}\s+[A-Za-z]{3,9}\d{1,2}',  # May1 May2
                r'[A-Za-z]{3,9}\s+\d{1,2}\s+[A-Za-z]{3,9}\s+\d{1,2}'  # May 1 May 2
            ]
            
            for i, pattern in enumerate(date_patterns, 1):
                matches = re.findall(pattern, text)
                print(f"  Pattern {i}: Found {len(matches)} date pairs")
                if matches:
                    print(f"    Examples: {matches[:3]}")
            
            # Look for amounts
            amount_pattern = r'\d{1,3}(?:,\d{3})*\.\d{2}'
            amounts = re.findall(amount_pattern, text)
            print(f"  Amounts: Found {len(amounts)} potential amounts")
            if amounts:
                print(f"    Examples: {amounts[:5]}")
            
            # Look for keywords that suggest transactions
            keywords = ['Payment', 'Apple', 'Google', 'Netflix', 'Thank You']
            found_keywords = []
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    found_keywords.append(keyword)
            
            print(f"  Keywords found: {found_keywords}")
            
            # Show page breakdown
            print(f"\nPage breakdown:")
            pages = text.split('=== PAGE')
            for j, page in enumerate(pages[1:], 1):  # Skip first empty split
                page_content = page.split('===')[0] if '===' in page else page
                print(f"  Page {j}: {len(page_content)} characters")
                
                # Show first line of each page
                first_line = page_content.split('\n')[0][:100] if page_content.strip() else "(empty)"
                print(f"    First line: {first_line}")
            
            # Ask if user wants to see full text
            if len(files_to_check) == 1:
                show_full = input(f"\nShow full extracted text? (y/n): ").strip().lower()
                if show_full == 'y':
                    print(f"\nFULL EXTRACTED TEXT:")
                    print("="*80)
                    print(text)
                    print("="*80)
        
        except Exception as e:
            print(f"❌ Error extracting from {filename}: {e}")
        
        # Pause between files if checking multiple
        if len(files_to_check) > 1 and i < len(files_to_check):
            input(f"\nPress Enter to continue to next file...")

if __name__ == "__main__":
    diagnose_batch_pdfs()