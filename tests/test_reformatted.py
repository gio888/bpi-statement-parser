# test_reformatted.py - Test the parser on reformatted PDF
import sys
sys.path.append('.')
from pdf_extractor import PDFExtractor
from transaction_parser import TransactionParser

def test_reformatted_pdf():
    """Test the parser on the reformatted 2024-08-12 PDF"""
    print("🧪 TESTING REFORMATTED 2024-08-12 PDF")
    print("="*60)
    
    # Get PDF path from command line or use default
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "./data/input/Statement BPI Master 2024-08-12.pdf"
        print(f"Usage: python {sys.argv[0]} <pdf_path>")
        print(f"Using default: {pdf_path}")
    
    try:
        # Extract text
        print("📄 Extracting text...")
        extractor = PDFExtractor(pdf_path)
        text = extractor.extract_text()
        print(f"✓ Extracted {len(text)} characters")
        
        # Parse transactions
        print("\n🔍 Parsing transactions...")
        parser = TransactionParser()
        transactions = parser.parse_transactions(text)
        
        print(f"\n✅ Result: Found {len(transactions)} transactions")
        
        if transactions:
            # Show currency breakdown
            currencies = {}
            for t in transactions:
                curr = t['currency']
                if curr not in currencies:
                    currencies[curr] = []
                currencies[curr].append(t)
            
            print(f"\n📊 CURRENCY BREAKDOWN:")
            for currency, trans_list in currencies.items():
                total = sum(t['amount'] for t in trans_list)
                print(f"  {currency}: {len(trans_list)} transactions, ₱{total:,.2f}")
            
            # Show sample transactions
            print(f"\n📄 SAMPLE TRANSACTIONS:")
            for i, t in enumerate(transactions[:5], 1):
                print(f"  {i}. {t['card']}")
                print(f"     {t['transaction_date']} -> {t['post_date']}")
                print(f"     {t['description'][:50]}...")
                print(f"     {t['currency']}: ₱{t['amount']}")
                if t.get('foreign_amount'):
                    print(f"     Foreign: {t['foreign_amount']}")
                print()
        else:
            print("❌ No transactions found - need to debug parser logic")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reformatted_pdf()