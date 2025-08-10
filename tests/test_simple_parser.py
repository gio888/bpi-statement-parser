# test_simple_parser.py - Test the simple parser with normalizer
import sys
sys.path.append('.')
from pdf_extractor import PDFExtractor
from simple_normalizer import SimpleTransactionParser

def test_simple_parser():
    """Test the simple parser on the failed PDF"""
    print("🧪 TESTING SIMPLE PARSER WITH NORMALIZER")
    print("="*60)
    
    # Get PDF path from command line or use default
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "./data/input/Statement BPI Master 2023-10-12.pdf"
        print(f"Usage: python {sys.argv[0]} <pdf_path>")
        print(f"Using default: {pdf_path}")
    
    try:
        # Extract text
        print("📄 Extracting text...")
        extractor = PDFExtractor(pdf_path)
        text = extractor.extract_text()
        print(f"✓ Extracted {len(text)} characters")
        
        # Parse with simple parser
        print("\n🔍 Parsing with simple parser...")
        parser = SimpleTransactionParser()
        transactions = parser.parse_transactions(text)
        
        print(f"\n✅ SUCCESS! Found {len(transactions)} transactions")
        
        # Show summary by currency
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
            
            if currency != 'PHP':
                foreign_total = sum(t.get('foreign_amount', 0) for t in trans_list if t.get('foreign_amount'))
                if foreign_total > 0:
                    print(f"    Foreign amount: {foreign_total:,.2f}")
        
        # Show first few transactions
        print(f"\n📄 SAMPLE TRANSACTIONS:")
        for i, t in enumerate(transactions[:5], 1):
            print(f"  {i}. {t['card']}")
            print(f"     {t['transaction_date']} -> {t['post_date']}")
            print(f"     {t['description'][:50]}...")
            print(f"     {t['currency']}: ₱{t['amount']}")
            if t.get('foreign_amount'):
                print(f"     Foreign: {t['foreign_amount']}")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_parser()