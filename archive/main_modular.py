# main_modular.py - Simple orchestrator
import pandas as pd
from datetime import datetime
import time
import os

# Import our modules
from pdf_extractor import PDFExtractor
from transaction_parser import TransactionParser
from currency_handler import CurrencyHandler

def main():
    print("=" * 60)
    print("BPI STATEMENT PARSER - MODULAR VERSION")
    print("Clean, maintainable architecture")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Ensure output directory exists
        os.makedirs("../data/output", exist_ok=True)
        
        # Step 1: Extract text (we know this works)
        print("📄 Extracting text from PDF...")
        extractor = PDFExtractor("../data/Statement BPI Master 2025-05-12.pdf")
        text = extractor.extract_text()
        print(f"✓ Extracted {len(text)} characters from {extractor.get_page_count()} pages")
        
        # DEBUG: Show full extracted text
        print(f"\n🔍 FULL EXTRACTED TEXT:")
        print("=" * 80)
        print(text)
        print("=" * 80)
        
        # Step 2: Parse transactions (we know this works)
        print("\n🔍 Parsing transactions...")
        parser = TransactionParser()
        transactions = parser.parse_transactions(text)
        print(f"✓ Found {len(transactions)} transactions")
        
        if not transactions:
            print("❌ No transactions found. Check PDF format or parsing logic.")
            return
        
        # Step 3: Process currency and create DataFrame
        print("\n💱 Processing currency information...")
        currency_handler = CurrencyHandler()
        enhanced_transactions = currency_handler.enhance_with_currency(transactions)
        
        # Step 4: Create DataFrame and clean
        df = pd.DataFrame(enhanced_transactions)
        df = currency_handler.clean_dataframe(df)
        
        # Step 5: Save results
        output_path = f"../data/output/bpi_modular_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_path, index=False)
        
        processing_time = time.time() - start_time
        
        # Display results
        print(f"\n✅ PROCESSING COMPLETE")
        print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        print(f"💾 Saved to: {output_path}")
        
        # Show summary
        currency_handler.print_summary(df)
        
        # Show exchange rates
        print(f"\n💹 EXCHANGE RATES (from transactions):")
        for currency in ['USD', 'SGD', 'NZD']:
            rate = currency_handler.get_exchange_rate(transactions, currency)
            if rate:
                print(f"  1 {currency} = ₱{rate:.2f}")
        
        print(f"\n🎉 Success! All transactions extracted and processed.")
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        print("Make sure the PDF file exists in the correct location.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_modules():
    """Test individual modules"""
    print("🧪 Testing individual modules...")
    
    try:
        # Test PDF extraction
        extractor = PDFExtractor("../data/Statement BPI Master 2025-05-12.pdf")
        text = extractor.extract_text()
        print(f"✓ PDF Extractor: {len(text)} characters")
        
        # Test transaction parsing
        parser = TransactionParser()
        transactions = parser.parse_transactions(text[:500])  # Test with sample
        print(f"✓ Transaction Parser: Found {len(transactions)} transactions in sample")
        
        # Test currency handler
        currency_handler = CurrencyHandler()
        if transactions:
            sample_df = pd.DataFrame(transactions)
            cleaned_df = currency_handler.clean_dataframe(sample_df)
            print(f"✓ Currency Handler: Processed {len(cleaned_df)} transactions")
        
        print("✅ All modules working correctly!")
        
    except Exception as e:
        print(f"❌ Module test failed: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_modules()
    else:
        main()