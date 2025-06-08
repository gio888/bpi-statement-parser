# main.py - Enhanced BPI Statement Parser with batch processing
import sys
import os

def show_menu():
    """Show main menu options"""
    print("="*60)
    print("BPI STATEMENT PARSER")
    print("="*60)
    print("1. Process single PDF")
    print("2. Process multiple PDFs (batch)")
    print("3. Exit")
    print("="*60)

def get_user_choice():
    """Get user menu choice"""
    while True:
        try:
            choice = input("Select option (1-3): ").strip()
            if choice in ['1', '2', '3']:
                return int(choice)
            else:
                print("Please enter 1, 2, or 3")
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            sys.exit(0)

def single_pdf_mode():
    """Process single PDF with proper year extraction"""
    print("\n📄 SINGLE PDF MODE")
    print("-" * 30)
    
    # Get PDF file path
    pdf_path = input("Enter PDF file path (or press Enter for default): ").strip()
    
    if not pdf_path:
        pdf_path = "/home/user/Library/CloudStorage/GoogleDrive-user@example.com/My Drive/Money/BPI/Statement BPI Master 2025-01-12.pdf"
        print(f"Using default: {pdf_path}")
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    try:
        # Import required components
        from pdf_extractor import PDFExtractor
        from transaction_parser import TransactionParser
        from currency_handler import CurrencyHandler
        from statement_finalizer import finalize_statement_csv
        import pandas as pd
        import re
        from datetime import datetime
        
        print(f"\n🚀 Processing: {os.path.basename(pdf_path)}")
        
        # Extract year from filename
        filename = os.path.basename(pdf_path)
        pattern = r'Statement BPI Master (\d{4}-\d{2}-\d{2})\.pdf'
        match = re.match(pattern, filename, re.IGNORECASE)
        
        statement_year = None
        if match:
            statement_date = datetime.strptime(match.group(1), "%Y-%m-%d").date()
            statement_year = statement_date.year
            print(f"📅 Statement year extracted: {statement_year}")
        else:
            print("⚠️  Could not extract year from filename, using current year")
            statement_year = datetime.now().year
        
        # Step 1: Extract text from PDF
        print("🔍 Extracting text from PDF...")
        pdf_extractor = PDFExtractor(pdf_path)
        text = pdf_extractor.extract_text()
        
        # Step 2: Parse transactions with year
        print("⚙️  Parsing transactions...")
        transaction_parser = TransactionParser()
        transactions = transaction_parser.parse_transactions(text, statement_year)
        
        if not transactions:
            print("❌ No transactions found in PDF")
            return
        
        print(f"✅ Found {len(transactions)} transactions")
        
        # Step 3: Create DataFrame and clean
        print("🧹 Processing data...")
        df = pd.DataFrame(transactions)
        currency_handler = CurrencyHandler()
        df_clean = currency_handler.clean_dataframe(df, statement_year)
        
        # Step 4: Save main CSV
        output_folder = "/home/user/Library/CloudStorage/GoogleDrive-user@example.com/My Drive/Money/BPI/"
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
        main_filename = f"For Import Statement BPI Master Single {timestamp}.csv"
        main_csv_path = os.path.join(output_folder, main_filename)
        
        os.makedirs(output_folder, exist_ok=True)
        df_clean.to_csv(main_csv_path, index=False)
        
        print(f"💾 Saved main CSV: {main_filename}")
        
        # Step 5: Auto-finalize (add account mapping and create card CSVs)
        print("🔧 Finalizing with account mapping...")
        finalization_result = finalize_statement_csv(main_csv_path, [statement_date])
        
        # Step 6: Show summary
        print("\n" + "="*60)
        print("📊 SINGLE PDF PROCESSING SUMMARY")
        print("="*60)
        print(f"📄 File: {filename}")
        print(f"📅 Statement year: {statement_year}")
        print(f"💳 Total transactions: {len(df_clean)}")
        print(f"💰 Total amount: ₱{df_clean['Amount'].sum():,.2f}")
        
        # Show by card
        if 'Card' in df_clean.columns:
            print(f"\n💳 By card:")
            for card in df_clean['Card'].unique():
                card_data = df_clean[df_clean['Card'] == card]
                print(f"  {card}: {len(card_data)} transactions, ₱{card_data['Amount'].sum():,.2f}")
        
        # Show output files
        card_csvs = finalization_result.get('card_csvs', [])
        if card_csvs:
            print(f"\n📁 Output files created:")
            for csv_path in card_csvs:
                print(f"  ✅ {os.path.basename(csv_path)}")
        
        print(f"\n🎉 Complete! Ready for accounting system import!")
        
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        import traceback
        traceback.print_exc()

def batch_pdf_mode():
    """Process multiple PDFs"""
    print("\n📁 BATCH PDF MODE")
    print("-" * 30)
    
    try:
        from batch_processor import main as process_batch
        process_batch()
    except Exception as e:
        print(f"❌ Error in batch processing: {e}")

def main():
    """Main application entry point"""
    while True:
        try:
            show_menu()
            choice = get_user_choice()
            
            if choice == 1:
                single_pdf_mode()
            elif choice == 2:
                batch_pdf_mode()
            elif choice == 3:
                print("\n👋 Goodbye!")
                break
            
            # Ask if user wants to continue
            if choice in [1, 2]:
                print("\n" + "="*60)
                continue_choice = input("Return to main menu? (y/n): ").strip().lower()
                if continue_choice not in ['y', 'yes']:
                    print("\n👋 Goodbye!")
                    break
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print("Returning to main menu...")

if __name__ == "__main__":
    main()