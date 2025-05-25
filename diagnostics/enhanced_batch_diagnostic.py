# enhanced_batch_diagnostic.py - Comprehensive PDF format analysis
import os
import re
from datetime import datetime, date
import sys
sys.path.append('src')

from pdf_extractor import PDFExtractor

def analyze_pdf_structure(file_path, filename):
    """Deep analysis of PDF structure and content patterns"""
    print(f"\n{'='*100}")
    print(f"🔍 ANALYZING: {filename}")
    print(f"{'='*100}")
    
    extractor = PDFExtractor(file_path)
    
    try:
        # Extract text
        text = extractor.extract_text()
        print(f"✓ Extracted {len(text)} characters from {extractor.get_page_count()} pages")
        
        # 1. CARD HEADER ANALYSIS
        print(f"\n📋 CARD HEADER ANALYSIS")
        print("-" * 50)
        
        # Known patterns
        known_patterns = [
            'BPIGOLDREWARDS',
            'BPI GOLD REWARDS', 
            'BPIECREDIT',
            'BPI ECREDIT',
            'GOLD REWARDS CARD',
            'ECREDIT CARD'
        ]
        
        found_headers = []
        for pattern in known_patterns:
            if pattern in text.upper().replace(' ', ''):
                found_headers.append(pattern)
                print(f"  ✓ Found: {pattern}")
        
        if not found_headers:
            print(f"  ❌ No known card headers found")
            # Look for potential new patterns
            print(f"\n  🔍 Searching for potential card identifiers...")
            
            # Look for lines with "CARD" or "BPI"
            lines = text.split('\n')
            potential_headers = []
            for line in lines:
                line_upper = line.upper().strip()
                if ('CARD' in line_upper or 'BPI' in line_upper) and len(line_upper) < 50:
                    potential_headers.append(line.strip())
            
            if potential_headers:
                print(f"  Potential headers found:")
                for header in set(potential_headers)[:10]:  # Unique, max 10
                    print(f"    - '{header}'")
            else:
                print(f"  No potential headers found")
        
        # 2. TRANSACTION PATTERN ANALYSIS  
        print(f"\n💳 TRANSACTION PATTERN ANALYSIS")
        print("-" * 50)
        
        # Test known transaction patterns
        patterns_to_test = [
            (r'([A-Za-z]{3,9})(\d{1,2})\s+([A-Za-z]{3,9})(\d{1,2})\s+(.+?)\s+(-?\d{1,3}(?:,\d{3})*\.\d{2})$', 'Single line PHP'),
            (r'([A-Za-z]{3,9})(\d{1,2})\s+([A-Za-z]{3,9})(\d{1,2})\s+(.+?)\s+(US|SG|NZ)$', 'First line foreign currency'),
            (r'U\.S\.Dollar\s+([\d.,]+)\s+(\d{1,3}(?:,\d{3})*\.\d{2})$', 'Second line foreign currency'),
            (r'Payment.*Thank.*You.*(-\d{1,3}(?:,\d{3})*\.\d{2})', 'Payment transactions'),
            (r'[A-Za-z]{3}\s*\d{1,2}\s+[A-Za-z]{3}\s*\d{1,2}', 'Date patterns (spaced)')
        ]
        
        lines = text.split('\n')
        for pattern, description in patterns_to_test:
            matches = []
            for line in lines:
                if re.search(pattern, line.strip()):
                    matches.append(line.strip())
            
            print(f"  {description}: {len(matches)} matches")
            if matches:
                print(f"    Examples:")
                for match in matches[:3]:  # Show first 3
                    print(f"      '{match}'")
        
        # 3. CONTENT STRUCTURE ANALYSIS
        print(f"\n📄 CONTENT STRUCTURE ANALYSIS")
        print("-" * 50)
        
        # Look for structural indicators
        structure_indicators = [
            'Statement of Account',
            'Customer Number',
            'Previous Balance', 
            'Transaction Date',
            'Post Date',
            'Description',
            'Amount',
            'Total Amount Due',
            'Minimum Amount Due'
        ]
        
        found_indicators = []
        for indicator in structure_indicators:
            if indicator.lower() in text.lower():
                found_indicators.append(indicator)
        
        print(f"  Found {len(found_indicators)}/{len(structure_indicators)} structure indicators:")
        for indicator in found_indicators:
            print(f"    ✓ {indicator}")
        
        # 4. PAGE-BY-PAGE ANALYSIS
        print(f"\n📖 PAGE-BY-PAGE ANALYSIS")
        print("-" * 50)
        
        pages = text.split('=== PAGE')
        for i, page_content in enumerate(pages[1:], 1):  # Skip first empty split
            page_text = page_content.split('===')[0] if '===' in page_content else page_content
            
            print(f"\n  PAGE {i}:")
            print(f"    Characters: {len(page_text)}")
            
            # Check for card headers on this page
            page_headers = []
            for pattern in known_patterns:
                if pattern in page_text.upper().replace(' ', ''):
                    page_headers.append(pattern)
            
            if page_headers:
                print(f"    Card headers: {page_headers}")
            
            # Count potential transactions on this page
            transaction_lines = 0
            for line in page_text.split('\n'):
                line = line.strip()
                if re.search(r'([A-Za-z]{3,9})(\d{1,2})\s+([A-Za-z]{3,9})(\d{1,2})', line):
                    transaction_lines += 1
            
            print(f"    Potential transactions: {transaction_lines}")
            
            # Show first few meaningful lines
            meaningful_lines = []
            for line in page_text.split('\n'):
                line = line.strip()
                if line and len(line) > 10 and not line.isspace():
                    meaningful_lines.append(line)
            
            if meaningful_lines:
                print(f"    First meaningful lines:")
                for line in meaningful_lines[:3]:
                    print(f"      '{line[:80]}{'...' if len(line) > 80 else ''}'")
        
        # 5. COMPARISON WITH WORKING FORMAT
        print(f"\n🔧 COMPARISON WITH WORKING FORMAT")
        print("-" * 50)
        
        # Check for specific elements that work in successful PDFs
        working_elements = [
            ('BPI GOLD REWARDS payment', 'Payment.*Thank.*You.*-13,544.89'),
            ('BPI ECREDIT payment', 'Payment.*Thank.*You.*-39,886.77'),
            ('Sharesight transaction', 'Sharesight'),
            ('Apple transaction', 'Apple'),
            ('Netflix transaction', 'Netflix'),
            ('Foreign currency format', 'U\.S\.Dollar.*\d+\.\d+.*\d+\.\d+')
        ]
        
        for element_name, pattern in working_elements:
            if re.search(pattern, text, re.IGNORECASE):
                print(f"    ✓ Found: {element_name}")
            else:
                print(f"    ✗ Missing: {element_name}")
        
        # 6. RECOMMENDED ACTIONS
        print(f"\n💡 RECOMMENDED ACTIONS")
        print("-" * 50)
        
        if not found_headers:
            print("  1. CRITICAL: No card headers found - investigate header format variations")
            print("  2. Check if this PDF uses different card naming conventions")
            
        if len([p for p in patterns_to_test if len(re.findall(p[0], text)) > 0]) < 2:
            print("  3. CRITICAL: Few transaction patterns match - investigate date/amount formats")
            
        if len(found_indicators) < len(structure_indicators) * 0.7:
            print("  4. WARNING: Missing many structure indicators - may be different PDF format")
            
        print("\n")
        return {
            'filename': filename,
            'total_chars': len(text),
            'pages': len(pages) - 1,
            'headers_found': found_headers,
            'structure_score': len(found_indicators) / len(structure_indicators),
            'has_transactions': any(len(re.findall(p[0], text)) > 0 for p, _ in patterns_to_test[:3])
        }
        
    except Exception as e:
        print(f"❌ Error analyzing {filename}: {e}")
        return {'filename': filename, 'error': str(e)}

def main():
    """Enhanced batch diagnostic with detailed analysis"""
    print("=" * 100)
    print("🔍 ENHANCED BPI PDF BATCH DIAGNOSTIC")
    print("Detailed analysis of PDF format variations")
    print("=" * 100)
    
    # Configuration
    pdf_folder = "/home/user/Library/CloudStorage/GoogleDrive-user@example.com/My Drive/Money/BPI/"
    
    # Get cutoff date
    while True:
        try:
            date_str = input("\nEnter cutoff date (YYYY-MM-DD) for analysis: ").strip()
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
    
    print(f"\nFound {len(matching_files)} PDFs to analyze")
    
    # Analysis options
    print("\nAnalysis options:")
    print("1. Analyze all files")
    print("2. Analyze failed files only") 
    print("3. Analyze specific files")
    print("4. Compare working vs failed files")
    
    choice = input("Select option (1-4): ").strip()
    
    files_to_analyze = []
    
    if choice == "1":
        files_to_analyze = matching_files
    elif choice == "2":
        # Known failed files
        failed_names = [
            "Statement BPI Master 2023-10-12.pdf",
            "Statement BPI Master 2023-11-12.pdf", 
            "Statement BPI Master 2023-12-12.pdf",
            "Statement BPI Master 2024-01-14.pdf",
            "Statement BPI Master 2024-02-12.pdf",
            "Statement BPI Master 2024-03-12.pdf"
        ]
        files_to_analyze = [f for f in matching_files if f['filename'] in failed_names]
    elif choice == "3":
        print("\nAvailable files:")
        for i, f in enumerate(matching_files, 1):
            print(f"  {i}. {f['filename']}")
        
        try:
            indices = input("Enter file numbers (comma-separated): ").strip()
            selected_indices = [int(x.strip()) - 1 for x in indices.split(',')]
            files_to_analyze = [matching_files[i] for i in selected_indices if 0 <= i < len(matching_files)]
        except (ValueError, IndexError):
            print("Invalid selection")
            return
    elif choice == "4":
        # Compare one working vs one failed
        working_file = "Statement BPI Master 2025-05-12.pdf"  # Known working
        failed_file = "Statement BPI Master 2023-10-12.pdf"   # Known failed
        
        files_to_analyze = [f for f in matching_files if f['filename'] in [working_file, failed_file]]
        
        if len(files_to_analyze) < 2:
            print("Could not find both working and failed files for comparison")
            return
    
    if not files_to_analyze:
        print("No files selected for analysis")
        return
    
    # Analyze each file
    results = []
    for i, file_info in enumerate(files_to_analyze, 1):
        print(f"\n{'='*20} ANALYZING {i}/{len(files_to_analyze)} {'='*20}")
        result = analyze_pdf_structure(file_info['full_path'], file_info['filename'])
        results.append(result)
        
        if i < len(files_to_analyze):
            input("Press Enter to continue to next file...")
    
    # Summary report
    print(f"\n{'='*100}")
    print("📊 BATCH ANALYSIS SUMMARY")
    print(f"{'='*100}")
    
    successful_files = [r for r in results if 'error' not in r and r.get('has_transactions', False)]
    failed_files = [r for r in results if 'error' in r or not r.get('has_transactions', False)]
    
    print(f"\n✅ Files with transaction patterns: {len(successful_files)}")
    print(f"❌ Files without transaction patterns: {len(failed_files)}")
    
    if successful_files:
        print(f"\n✅ SUCCESSFUL FILES:")
        for result in successful_files:
            headers = ', '.join(result.get('headers_found', ['None']))
            print(f"  • {result['filename']}: {headers}")
    
    if failed_files:
        print(f"\n❌ PROBLEMATIC FILES:")
        for result in failed_files:
            issue = result.get('error', 'No transaction patterns detected')
            print(f"  • {result['filename']}: {issue}")
    
    # Pattern analysis
    all_headers = []
    for result in results:
        if 'headers_found' in result:
            all_headers.extend(result['headers_found'])
    
    if all_headers:
        from collections import Counter
        header_counts = Counter(all_headers)
        print(f"\n📋 CARD HEADER FREQUENCY:")
        for header, count in header_counts.most_common():
            print(f"  • {header}: {count} files")
    
    print(f"\n🎯 NEXT STEPS:")
    if failed_files:
        print("1. Update transaction_parser.py to handle format variations found")
        print("2. Add new card header patterns to parser")
        print("3. Test updated parser with failed files")
        print("4. Re-run batch processing")
    else:
        print("1. All files show transaction patterns - check parser logic")
        print("2. May be parsing logic issue rather than format issue")

if __name__ == "__main__":
    main()