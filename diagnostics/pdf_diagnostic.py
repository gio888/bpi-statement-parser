# pdf_diagnostic.py - Simple PDF content inspector
import pdfplumber
import PyPDF2

def diagnose_pdf(file_path):
    print("=" * 80)
    print("PDF DIAGNOSTIC TOOL")
    print("=" * 80)
    
    # Method 1: PyPDF2 extraction
    print("\n📄 METHOD 1: PyPDF2 Extraction")
    print("-" * 50)
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f"Total pages: {len(pdf_reader.pages)}")
            
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                print(f"\nPAGE {page_num + 1} (PyPDF2):")
                print(f"Characters: {len(text)}")
                print("Content:")
                print(text)
                print("\n" + "="*60)
    except Exception as e:
        print(f"PyPDF2 failed: {e}")
    
    # Method 2: pdfplumber standard extraction
    print("\n📄 METHOD 2: pdfplumber Standard")
    print("-" * 50)
    try:
        with pdfplumber.open(file_path) as pdf:
            print(f"Total pages: {len(pdf.pages)}")
            
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                print(f"\nPAGE {page_num + 1} (pdfplumber):")
                print(f"Characters: {len(text) if text else 0}")
                if text:
                    print("Content:")
                    print(text)
                else:
                    print("No text extracted")
                print("\n" + "="*60)
    except Exception as e:
        print(f"pdfplumber failed: {e}")
    
    # Method 3: pdfplumber table extraction
    print("\n📊 METHOD 3: pdfplumber Tables")
    print("-" * 50)
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                print(f"\nPAGE {page_num + 1} Tables:")
                print(f"Found {len(tables)} table(s)")
                
                for table_num, table in enumerate(tables):
                    print(f"\nTable {table_num + 1}:")
                    print(f"Rows: {len(table)}")
                    print("Content:")
                    for row_num, row in enumerate(table):
                        print(f"  Row {row_num}: {row}")
                        if row_num > 10:  # Limit output
                            print(f"  ... ({len(table) - 10} more rows)")
                            break
                print("\n" + "="*60)
    except Exception as e:
        print(f"Table extraction failed: {e}")
    
    # Method 4: pdfplumber word extraction
    print("\n🔤 METHOD 4: pdfplumber Words")
    print("-" * 50)
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                words = page.extract_words()
                print(f"\nPAGE {page_num + 1} Words:")
                print(f"Found {len(words)} words")
                
                # Show first 50 words
                print("First 50 words:")
                for i, word in enumerate(words[:50]):
                    print(f"  {i+1}. '{word['text']}' at ({word['x0']:.1f}, {word['top']:.1f})")
                
                if len(words) > 50:
                    print(f"  ... ({len(words) - 50} more words)")
                
                # Look for specific keywords
                keywords = ['BPI', 'GOLD', 'REWARDS', 'ECREDIT', 'Payment', 'Thank', 'Sharesight']
                found_keywords = []
                for word in words:
                    if any(keyword.lower() in word['text'].lower() for keyword in keywords):
                        found_keywords.append(f"'{word['text']}' at ({word['x0']:.1f}, {word['top']:.1f})")
                
                if found_keywords:
                    print(f"\nKeywords found:")
                    for kw in found_keywords:
                        print(f"  {kw}")
                
                print("\n" + "="*60)
    except Exception as e:
        print(f"Word extraction failed: {e}")
    
    # Method 5: Raw text search
    print("\n🔍 METHOD 5: Keyword Search")
    print("-" * 50)
    keywords_to_find = [
        'BPI GOLD REWARDS',
        'BPI ECREDIT', 
        'Payment - Thank You',
        'Sharesight',
        'Wellington',
        '-13,544.89',
        '-39,886.77',
        '529.64'
    ]
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                
                print(f"\nPAGE {page_num + 1} Keyword Search:")
                for keyword in keywords_to_find:
                    if keyword.lower() in text.lower():
                        print(f"  ✓ Found: '{keyword}'")
                        # Show context
                        idx = text.lower().find(keyword.lower())
                        start = max(0, idx - 50)
                        end = min(len(text), idx + len(keyword) + 50)
                        context = text[start:end].replace('\n', ' ')
                        print(f"    Context: ...{context}...")
                    else:
                        print(f"  ✗ Missing: '{keyword}'")
    except Exception as e:
        print(f"Keyword search failed: {e}")

if __name__ == "__main__":
    file_path = "../data/Statement BPI Master 2025-05-12.pdf"
    diagnose_pdf(file_path)