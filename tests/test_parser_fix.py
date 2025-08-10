# test_parser_fix.py - Test the parser fix on a failed PDF
import sys
sys.path.append('.')
from pdf_extractor import PDFExtractor
from transaction_parser import TransactionParser

def test_failed_pdf():
    """Test parser on previously failed PDF"""
    print("🧪 TESTING PARSER FIX ON FAILED PDF")
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
        
        # Parse transactions
        print("\n🔍 Parsing transactions...")
        parser = TransactionParser()
        transactions = parser.parse_transactions(text)
        
        print(f"\n✅ SUCCESS! Found {len(transactions)} transactions")
        
        if transactions:
            print(f"\n📊 TRANSACTION SUMMARY:")
            for transaction in transactions:
                print(f"  • {transaction['card']}")
                print(f"    {transaction['transaction_date']} -> {transaction['post_date']}")
                print(f"    {transaction['description'][:50]}...")
                print(f"    {transaction['currency']}: ₱{transaction['amount']}")
                if transaction['foreign_amount']:
                    print(f"    Foreign: {transaction['foreign_amount']}")
                print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_failed_pdf()