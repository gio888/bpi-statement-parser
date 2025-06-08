# statement_finalizer.py - Final version for /src/ folder
import pandas as pd
import os
import sys
from datetime import datetime

# Add parent directory to path so we can import account_mapper from main folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from account_mapper import AccountMapper

class StatementFinalizer:
    def __init__(self, accounts_csv_path: str = None):
        # Default accounts CSV path
        if not accounts_csv_path:
            accounts_csv_path = "/path/to/project/data/input/Accounts List 2024-07.csv"
        
        self.account_mapper = AccountMapper(accounts_csv_path)
        
        # Default output folder (same as PDFs)
        self.output_folder = "/home/user/Library/CloudStorage/GoogleDrive-user@example.com/My Drive/Money/BPI/"
    
    def finalize_statement(self, main_csv_path: str, statement_dates: list = None) -> dict:
        """
        Complete post-processing: add account mapping and create card-specific CSVs
        
        Args:
            main_csv_path: Path to the main CSV file
            statement_dates: List of statement dates for filename generation
        
        Returns:
            dict: Paths of created files
        """
        print(f"\n🔧 FINALIZING STATEMENT")
        print(f"Input: {os.path.basename(main_csv_path)}")
        
        # Load the main CSV
        try:
            df = pd.read_csv(main_csv_path)
            print(f"   ✅ Loaded {len(df)} transactions")
        except Exception as e:
            print(f"   ❌ Error loading CSV: {e}")
            return {}
        
        # Add account mapping
        df_enhanced = self._add_account_mapping(df)
        
        # Create card-specific CSVs with custom naming
        card_csvs = self._create_card_csvs(df_enhanced, statement_dates)
        
        # Print summary
        self._print_summary(df_enhanced, card_csvs)
        
        return {
            'enhanced_csv': main_csv_path,
            'card_csvs': card_csvs
        }
    
    def _add_account_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Target Account column to DataFrame"""
        print(f"🎯 Adding account mapping...")
        
        df_copy = df.copy()
        
        if 'Description' in df_copy.columns:
            # Apply account mapping
            df_copy['Target Account'] = df_copy['Description'].apply(
                self.account_mapper.map_description_to_account
            )
            
            # Calculate success rate
            total_transactions = len(df_copy)
            manual_review_count = (df_copy['Target Account'] == 'Manual Review').sum()
            auto_mapped_count = total_transactions - manual_review_count
            success_rate = (auto_mapped_count / total_transactions) * 100
            
            print(f"   ✅ Account mapping complete: {success_rate:.1f}% auto-mapped ({auto_mapped_count}/{total_transactions})")
            if manual_review_count > 0:
                print(f"   ⚠️  {manual_review_count} transactions need manual review")
        else:
            print(f"   ❌ 'Description' column not found")
            df_copy['Target Account'] = 'Manual Review'
        
        return df_copy
    
    def _create_card_csvs(self, df: pd.DataFrame, statement_dates: list = None) -> list:
        """Create separate CSV files for each card + combined file with date-based naming"""
        print(f"📁 Creating card-specific CSVs...")
        
        created_files = []
        
        # Check required columns
        required_cols = ['Card', 'Post Date', 'Description', 'Amount', 'Target Account']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"   ❌ Missing columns: {missing_cols}")
            return created_files
        
        # Generate date suffix for filenames
        date_suffix = self._generate_date_suffix(statement_dates)
        
        # Group by card
        cards = df['Card'].unique()
        print(f"   🔍 Found {len(cards)} cards: {', '.join(cards)}")
        
        # 1. Create individual card CSVs
        for card in cards:
            card_data = df[df['Card'] == card]
            
            # Select required columns: Post Date, Description, Amount, Target Account
            card_df = card_data[['Post Date', 'Description', 'Amount', 'Target Account']].copy()
            
            # Generate filename with date suffix
            safe_card_name = card.replace(' ', '_').replace(':', '').replace('/', '')
            filename = f"For Import Statement BPI Master {safe_card_name} {date_suffix}.csv"
            filepath = os.path.join(self.output_folder, filename)
            
            # Ensure output folder exists
            os.makedirs(self.output_folder, exist_ok=True)
            
            # Save CSV
            try:
                card_df.to_csv(filepath, index=False)
                created_files.append(filepath)
                print(f"   ✅ {filename} ({len(card_df)} transactions)")
            except Exception as e:
                print(f"   ❌ Error saving {filename}: {e}")
        
        # 2. Create combined "Both" CSV with Account column
        combined_df = self._create_combined_csv(df, date_suffix)
        if combined_df is not None:
            created_files.append(combined_df)
        
        return created_files
    
    def _generate_date_suffix(self, statement_dates: list) -> str:
        """Generate date suffix for filenames based on statement dates"""
        if not statement_dates:
            # Fallback to timestamp if no dates provided
            return datetime.now().strftime("%Y-%m-%d %H%M")
        
        # Convert to date objects if they're strings
        dates = []
        for date_item in statement_dates:
            if isinstance(date_item, str):
                try:
                    # Try parsing YYYY-MM-DD format
                    parsed_date = datetime.strptime(date_item, "%Y-%m-%d").date()
                    dates.append(parsed_date)
                except ValueError:
                    print(f"   ⚠️  Could not parse date: {date_item}")
                    continue
            else:
                dates.append(date_item)
        
        if not dates:
            # Fallback to timestamp
            return datetime.now().strftime("%Y-%m-%d %H%M")
        
        # Sort dates
        dates.sort()
        
        if len(dates) == 1:
            # Single PDF: use statement date
            return dates[0].strftime("%Y-%m-%d")
        else:
            # Batch: use date range
            earliest = dates[0].strftime("%Y-%m-%d")
            latest = dates[-1].strftime("%Y-%m-%d")
            return f"{earliest} to {latest}"
    
    def _create_combined_csv(self, df: pd.DataFrame, date_suffix: str) -> str:
        """Create combined CSV with Account column based on card"""
        print(f"   🔗 Creating combined 'Both' CSV...")
        
        try:
            # Create combined dataframe
            combined_data = []
            
            for _, row in df.iterrows():
                # Map card to account
                if 'BPI ECREDIT CARD' in str(row['Card']).upper():
                    account = "Liabilities:Credit Card:BPI Mastercard:e-credit"
                elif 'BPI GOLD REWARDS CARD' in str(row['Card']).upper():
                    account = "Liabilities:Credit Card:BPI Mastercard:Gold"
                else:
                    account = "Liabilities:Credit Card:BPI Mastercard"  # fallback
                
                combined_data.append({
                    'Date': row['Post Date'],
                    'Description': row['Description'],
                    'Amount': row['Amount'],
                    'Account': account,
                    'Target Account': row['Target Account']
                })
            
            # Create DataFrame
            combined_df = pd.DataFrame(combined_data)
            
            # Generate filename with date suffix
            filename = f"For Import Statement BPI Master Both {date_suffix}.csv"
            filepath = os.path.join(self.output_folder, filename)
            
            # Save CSV
            combined_df.to_csv(filepath, index=False)
            print(f"   ✅ {filename} ({len(combined_df)} transactions)")
            
            return filepath
            
        except Exception as e:
            print(f"   ❌ Error creating combined CSV: {e}")
            return None
    
    def _print_summary(self, df: pd.DataFrame, card_csvs: list):
        """Print processing summary"""
        print(f"\n📊 FINALIZATION SUMMARY")
        print(f"="*60)
        
        # Transaction summary
        total_transactions = len(df)
        print(f"💳 Total transactions processed: {total_transactions}")
        
        if 'Amount' in df.columns:
            total_amount = df['Amount'].sum()
            print(f"💰 Total amount: ₱{total_amount:,.2f}")
        
        # Card breakdown
        if 'Card' in df.columns:
            print(f"\n💳 By card:")
            for card in df['Card'].unique():
                card_data = df[df['Card'] == card]
                count = len(card_data)
                amount = card_data['Amount'].sum() if 'Amount' in card_data.columns else 0
                print(f"   {card}: {count} transactions, ₱{amount:,.2f}")
        
        # Account mapping summary
        if 'Target Account' in df.columns:
            manual_review = (df['Target Account'] == 'Manual Review').sum()
            auto_mapped = total_transactions - manual_review
            print(f"\n🎯 Account mapping:")
            print(f"   Auto-mapped: {auto_mapped}/{total_transactions} ({auto_mapped/total_transactions*100:.1f}%)")
            if manual_review > 0:
                print(f"   Manual review: {manual_review} transactions")
        
        # Files created
        print(f"\n📁 Files created:")
        print(f"   ✅ Individual card CSVs: {len([f for f in card_csvs if 'Both' not in f])} files")
        print(f"   ✅ Combined 'Both' CSV: 1 file")
        for csv_path in card_csvs:
            print(f"      - {os.path.basename(csv_path)}")
        
        print(f"\n🎉 Ready for import to accounting system!")

def finalize_statement_csv(csv_path: str, statement_dates: list = None, accounts_csv_path: str = None) -> dict:
    """
    Convenience function for finalizing a statement CSV with custom date naming
    
    Args:
        csv_path: Path to the main CSV file
        statement_dates: List of statement dates (datetime.date objects or strings)
        accounts_csv_path: Path to accounts mapping CSV
    """
    finalizer = StatementFinalizer(accounts_csv_path)
    return finalizer.finalize_statement(csv_path, statement_dates)