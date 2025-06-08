# batch_processor.py - Enhanced with automatic finalization
import os
import re
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Tuple
import logging

from pdf_extractor import PDFExtractor
from transaction_parser import TransactionParser
from currency_handler import CurrencyHandler
from statement_finalizer import finalize_statement_csv

class BatchStatementProcessor:
    def __init__(self, pdf_folder: str, output_folder: str):
        self.pdf_folder = pdf_folder
        self.output_folder = output_folder
        self.pdf_extractor = PDFExtractor("")  # Will set path per file
        self.transaction_parser = TransactionParser()
        self.currency_handler = CurrencyHandler()
        
        # Results tracking
        self.processed_files = []
        self.failed_files = []
        self.all_transactions = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def get_user_date_input(self) -> date:
        """Get cutoff date from user with validation"""
        while True:
            try:
                date_str = input("\nEnter cutoff date (YYYY-MM-DD) - will include this date and after: ").strip()
                
                # Parse and validate date
                cutoff_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                print(f"✓ Will process statements from {cutoff_date} onwards")
                return cutoff_date
                
            except ValueError:
                print("❌ Invalid date format. Please use YYYY-MM-DD (e.g., 2025-05-01)")
            except KeyboardInterrupt:
                print("\n\nOperation cancelled by user.")
                exit(0)
    
    def find_statement_pdfs(self, cutoff_date: date) -> Tuple[List[str], List[str]]:
        """Find PDFs matching pattern and date criteria"""
        if not os.path.exists(self.pdf_folder):
            raise FileNotFoundError(f"PDF folder not found: {self.pdf_folder}")
        
        matching_files = []
        skipped_files = []
        
        # Pattern: "Statement BPI Master YYYY-MM-DD.pdf"
        pattern = r'^Statement BPI Master (\d{4}-\d{2}-\d{2})\.pdf$'
        
        print(f"\n🔍 Scanning folder: {self.pdf_folder}")
        
        for filename in os.listdir(self.pdf_folder):
            match = re.match(pattern, filename, re.IGNORECASE)
            
            if match:
                file_date_str = match.group(1)
                try:
                    file_date = datetime.strptime(file_date_str, "%Y-%m-%d").date()
                    
                    if file_date >= cutoff_date:
                        matching_files.append({
                            'filename': filename,
                            'statement_date': file_date,
                            'full_path': os.path.join(self.pdf_folder, filename)
                        })
                    else:
                        skipped_files.append({
                            'filename': filename,
                            'statement_date': file_date,
                            'reason': 'Before cutoff date'
                        })
                        
                except ValueError:
                    skipped_files.append({
                        'filename': filename,
                        'statement_date': None,
                        'reason': 'Invalid date format'
                    })
        
        # Sort by date
        matching_files.sort(key=lambda x: x['statement_date'])
        
        return matching_files, skipped_files
    
    def show_preview(self, matching_files: List[Dict], skipped_files: List[Dict]) -> None:
        """Show dry-run preview of what will be processed"""
        print("\n" + "="*80)
        print("📋 PROCESSING PREVIEW")
        print("="*80)
        
        if matching_files:
            print(f"\n✅ Found {len(matching_files)} PDFs matching criteria:")
            for file_info in matching_files:
                print(f"  ✓ {file_info['filename']} ({file_info['statement_date']})")
        else:
            print("\n❌ No PDFs found matching criteria")
        
        if skipped_files:
            print(f"\n⏭️  Skipped {len(skipped_files)} PDFs:")
            for file_info in skipped_files:
                print(f"  - {file_info['filename']} ({file_info.get('statement_date', 'Unknown')}) - {file_info['reason']}")
        
        if matching_files:
            output_filename = self.generate_output_filename()
            print(f"\n📁 Main CSV will be: {output_filename}")
            print(f"📁 Card-specific CSVs will be auto-generated")
            print(f"📁 Output folder: {self.output_folder}")
        
        print("\n" + "="*80)
    
    def confirm_proceed(self) -> bool:
        """Ask user confirmation to proceed"""
        while True:
            try:
                response = input("\nProceed with processing? (y/n): ").strip().lower()
                if response in ['y', 'yes']:
                    return True
                elif response in ['n', 'no']:
                    print("Operation cancelled by user.")
                    return False
                else:
                    print("Please enter 'y' or 'n'")
            except KeyboardInterrupt:
                print("\n\nOperation cancelled by user.")
                return False
    
    def process_batch(self, pdf_files: List[Dict]) -> pd.DataFrame:
        """Process multiple PDF files"""
        if not pdf_files:
            print("❌ No files to process")
            return pd.DataFrame()
        
        print(f"\n🚀 Processing {len(pdf_files)} PDF files...")
        print("="*60)
        
        for i, file_info in enumerate(pdf_files, 1):
            filename = file_info['filename']
            file_path = file_info['full_path']
            statement_date = file_info['statement_date']
            
            print(f"\n📄 Processing {i}/{len(pdf_files)}: {filename}")
            
            try:
                # Extract and parse
                self.pdf_extractor.file_path = file_path
                text = self.pdf_extractor.extract_text()
                statement_year = statement_date.year
                print(f"DEBUG BATCH: statement_date = {statement_date}, statement_year = {statement_year}")
                transactions = self.transaction_parser.parse_transactions(text, statement_year)
                
                if transactions:
                    # Add statement date to each transaction
                    for transaction in transactions:
                        transaction['statement_date'] = statement_date
                    
                    self.all_transactions.extend(transactions)
                    self.processed_files.append(file_info)
                    
                    print(f"  ✅ Success: {len(transactions)} transactions")
                else:
                    print(f"  ⚠️  No transactions found")
                    self.failed_files.append({
                        **file_info,
                        'error': 'No transactions found'
                    })
                    
            except Exception as e:
                error_msg = str(e)
                print(f"  ❌ Error: {error_msg}")
                self.failed_files.append({
                    **file_info,
                    'error': error_msg
                })
                self.logger.error(f"Failed to process {filename}: {error_msg}")
        
        # Create final DataFrame
        if self.all_transactions:
            df = pd.DataFrame(self.all_transactions)
            df = self.currency_handler.clean_dataframe(df, statement_year)
            return df
        else:
            return pd.DataFrame()
    
    def generate_output_filename(self) -> str:
        """Generate output filename with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
        return f"For Import Statement BPI Master {timestamp}.csv"
    
    def save_combined_csv(self, df: pd.DataFrame) -> str:
        """Save combined transactions to CSV"""
        if df.empty:
            print("❌ No data to save")
            return ""
        
        # Ensure output folder exists
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Generate filename and path
        filename = self.generate_output_filename()
        output_path = os.path.join(self.output_folder, filename)
        
        # Save CSV
        df.to_csv(output_path, index=False)
        
        print(f"\n💾 Saved main CSV: {filename}")
        print(f"📁 Location: {output_path}")
        
        return output_path
    
    def show_summary_report(self, df: pd.DataFrame, finalization_result: dict) -> None:
        """Show final processing summary"""
        print("\n" + "="*80)
        print("📊 BATCH PROCESSING SUMMARY")
        print("="*80)
        
        # File processing summary
        total_files = len(self.processed_files) + len(self.failed_files)
        print(f"\n📁 PDF Processing:")
        print(f"  ✅ Successfully processed: {len(self.processed_files)}/{total_files}")
        print(f"  ❌ Failed: {len(self.failed_files)}/{total_files}")
        
        if self.failed_files:
            print(f"\n❌ Failed files:")
            for file_info in self.failed_files:
                print(f"  - {file_info['filename']}: {file_info['error']}")
        
        # Transaction summary
        if not df.empty:
            print(f"\n💳 Transactions:")
            print(f"  Total extracted: {len(df)}")
            print(f"  Total amount: ₱{df['Amount'].sum():,.2f}")
            
            # By card
            print(f"\n💳 By card:")
            for card in df['Card'].unique():
                card_data = df[df['Card'] == card]
                print(f"  {card}: {len(card_data)} transactions, ₱{card_data['Amount'].sum():,.2f}")
            
            # By currency
            print(f"\n💱 By currency:")
            for currency in df['Currency'].unique():
                curr_data = df[df['Currency'] == currency]
                print(f"  {currency}: {len(curr_data)} transactions, ₱{curr_data['Amount'].sum():,.2f}")
            
            # Date range
            if 'Statement Date' in df.columns:
                date_range = f"{df['Statement Date'].min()} to {df['Statement Date'].max()}"
                print(f"\n📅 Statement date range: {date_range}")
        
        # Finalization results
        card_csvs = finalization_result.get('card_csvs', [])
        if card_csvs:
            print(f"\n📁 Output files ready for import:")
            for csv_path in card_csvs:
                print(f"  ✅ {os.path.basename(csv_path)}")
        
        print("\n" + "="*80)
        print("🎉 Complete! Ready for accounting system import!")

def main():
    """Main function for batch processing"""
    print("="*80)
    print("BPI STATEMENT BATCH PROCESSOR")
    print("Process multiple PDF statements with automatic account mapping")
    print("="*80)
    
    # Configuration
    pdf_folder = "/home/user/Library/CloudStorage/GoogleDrive-user@example.com/My Drive/Money/BPI/"
    output_folder = "/home/user/Library/CloudStorage/GoogleDrive-user@example.com/My Drive/Money/BPI/"
    
    try:
        # Initialize processor
        processor = BatchStatementProcessor(pdf_folder, output_folder)
        
        # Get user input
        cutoff_date = processor.get_user_date_input()
        
        # Find matching files
        matching_files, skipped_files = processor.find_statement_pdfs(cutoff_date)
        
        # Show preview
        processor.show_preview(matching_files, skipped_files)
        
        # Get confirmation
        if not processor.confirm_proceed():
            return
        
        # Process files
        df = processor.process_batch(matching_files)
        
        # Save main CSV
        main_csv_path = ""
        if not df.empty:
            main_csv_path = processor.save_combined_csv(df)
        
        # Auto-finalize: add account mapping and create card CSVs
        finalization_result = {}
        if main_csv_path:
            print(f"\n🔄 Auto-finalizing statement...")
            statement_dates = [file_info['statement_date'] for file_info in processor.processed_files]
            finalization_result = finalize_statement_csv(main_csv_path, statement_dates)
        
        # Show summary
        processor.show_summary_report(df, finalization_result)
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logging.error(f"Batch processing failed: {e}")

if __name__ == "__main__":
    main()