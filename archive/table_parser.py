import pandas as pd
import pdfplumber
from datetime import datetime
from typing import List, Dict, Any
import logging
import time

class BPITableParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def extract_tables_from_pdf(self) -> List[List[List[str]]]:
        """Extract tables from PDF using pdfplumber"""
        try:
            tables = []
            with pdfplumber.open(self.file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    print(f"Processing page {i+1}...")
                    
                    # Extract tables from this page
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
                        print(f"Found {len(page_tables)} table(s) on page {i+1}")
                    
                    # Also extract text to show what pdfplumber sees
                    if i == 0:  # Just show first page text for debugging
                        text = page.extract_text()
                        print(f"First 500 chars of page {i+1} text:")
                        print("=" * 50)
                        print(text[:500] if text else "No text extracted")
                        print("=" * 50)
            
            return tables
        except Exception as e:
            self.logger.error(f"Error extracting tables: {e}")
            raise

    def parse_transactions_from_tables(self, tables: List[List[List[str]]]) -> pd.DataFrame:
        """Parse transaction data from extracted tables"""
        all_transactions = []
        
        for table_idx, table in enumerate(tables):
            print(f"\nTable {table_idx + 1}:")
            print(f"Rows: {len(table)}")
            
            # Show first few rows for debugging
            for row_idx, row in enumerate(table[:5]):
                print(f"Row {row_idx}: {row}")
            
            transactions = self._process_table(table, table_idx)
            all_transactions.extend(transactions)
        
        # Create DataFrame
        df = pd.DataFrame(all_transactions)
        
        if not df.empty:
            df = self._clean_dataframe(df)
            
        return df

    def _process_table(self, table: List[List[str]], table_idx: int) -> List[Dict[str, Any]]:
        """Process a single table to extract transactions"""
        transactions = []
        
        if not table:
            return transactions
        
        # Try to identify card type from table content
        card_type = self._identify_card_type(table)
        
        # Look for header row patterns
        header_found = False
        data_start_row = 0
        
        for i, row in enumerate(table):
            if row and len(row) >= 4:
                # Check if this looks like a header row
                row_str = ' '.join([cell or '' for cell in row]).lower()
                if 'transaction' in row_str and 'date' in row_str and 'description' in row_str:
                    header_found = True
                    data_start_row = i + 1
                    print(f"Found header at row {i}: {row}")
                    break
        
        # Process data rows
        for i in range(data_start_row, len(table)):
            row = table[i]
            if not row or len(row) < 4:
                continue
            
            # Skip empty or non-data rows
            if not any(cell and cell.strip() for cell in row):
                continue
            
            transaction = self._parse_table_row(row, card_type)
            if transaction:
                transactions.append(transaction)
        
        return transactions

    def _identify_card_type(self, table: List[List[str]]) -> str:
        """Identify which card type this table represents"""
        table_text = ' '.join([' '.join([cell or '' for cell in row]) for row in table[:5]])
        
        if 'GOLD' in table_text.upper() or 'REWARDS' in table_text.upper():
            return 'BPI GOLD REWARDS CARD'
        elif 'ECREDIT' in table_text.upper() or 'E-CREDIT' in table_text.upper():
            return 'BPI ECREDIT CARD'
        else:
            return 'UNKNOWN CARD'

    def _parse_table_row(self, row: List[str], card_type: str) -> Dict[str, Any]:
        """Parse a single table row into transaction data"""
        # Clean up the row
        clean_row = [cell.strip() if cell else '' for cell in row]
        
        # Skip rows that don't look like transactions
        if len(clean_row) < 4:
            return None
        
        # Skip balance/summary rows
        skip_patterns = [
            'previous balance', 'past due', 'ending balance', 
            'payment', 'finance charge', 'unbilled'
        ]
        
        row_text = ' '.join(clean_row).lower()
        if any(pattern in row_text for pattern in skip_patterns):
            return None
        
        # Try to parse transaction pattern
        # Expected: [Transaction Date, Post Date, Description, Amount]
        # Or: [Transaction Date, Post Date, Description, ..., Amount]
        
        if len(clean_row) >= 4:
            # Look for date patterns in first two cells
            trans_date = clean_row[0]
            post_date = clean_row[1]
            
            # Check if these look like dates
            if not self._looks_like_date(trans_date) or not self._looks_like_date(post_date):
                return None
            
            # Find the amount (should be last numeric cell)
            amount_str = None
            amount_idx = -1
            
            for i in range(len(clean_row) - 1, -1, -1):
                if self._looks_like_amount(clean_row[i]):
                    amount_str = clean_row[i]
                    amount_idx = i
                    break
            
            if not amount_str:
                return None
            
            # Description is everything between post_date and amount
            description_parts = clean_row[2:amount_idx]
            description = ' '.join([part for part in description_parts if part]).strip()
            
            if len(description) < 2:
                return None
            
            try:
                amount_float = float(amount_str.replace(',', '').replace('₱', ''))
                
                return {
                    'Card_Type': card_type,
                    'Transaction_Date': trans_date,
                    'Post_Date': post_date,
                    'Description': description,
                    'Amount': amount_float
                }
            except ValueError:
                return None
        
        return None

    def _looks_like_date(self, text: str) -> bool:
        """Check if text looks like a date"""
        if not text:
            return False
        
        # Check for patterns like "May 1", "Apr 16", etc.
        import re
        date_pattern = r'^[A-Za-z]{3,9}\s*\d{1,2}$'
        return bool(re.match(date_pattern, text.strip()))

    def _looks_like_amount(self, text: str) -> bool:
        """Check if text looks like a monetary amount"""
        if not text:
            return False
        
        import re
        # Pattern for amounts like "1,234.56" or "123.45"
        amount_pattern = r'^\d{1,3}(?:,\d{3})*\.\d{2}$'
        clean_text = text.replace('₱', '').strip()
        return bool(re.match(amount_pattern, clean_text))

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and format the DataFrame"""
        if df.empty:
            return df
        
        # Convert date columns to datetime
        current_year = datetime.now().year
        
        for date_col in ['Transaction_Date', 'Post_Date']:
            if date_col in df.columns:
                df[date_col] = df[date_col].apply(lambda x: self._parse_date(x, current_year))
        
        # Sort by transaction date
        if 'Transaction_Date' in df.columns:
            df = df.sort_values('Transaction_Date').reset_index(drop=True)
        
        return df

    def _parse_date(self, date_str: str, year: int) -> datetime:
        """Parse date string to datetime object"""
        try:
            date_obj = datetime.strptime(f"{date_str} {year}", "%b %d %Y")
            return date_obj
        except ValueError:
            try:
                # Try different format
                date_obj = datetime.strptime(f"{date_str} {year}", "%B %d %Y")
                return date_obj
            except ValueError:
                self.logger.warning(f"Could not parse date: {date_str}")
                return None

    def save_to_csv(self, df: pd.DataFrame, output_path: str = None):
        """Save DataFrame to CSV"""
        if output_path is None:
            output_path = f"../data/output/bpi_table_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        df.to_csv(output_path, index=False)
        self.logger.info(f"Transactions saved to: {output_path}")

    def get_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary statistics"""
        if df.empty:
            return {"message": "No transactions found"}
        
        summary = {
            "total_transactions": len(df),
            "total_amount": df['Amount'].sum(),
            "transactions_by_card": df['Card_Type'].value_counts().to_dict(),
            "date_range": {
                "start": df['Transaction_Date'].min(),
                "end": df['Transaction_Date'].max()
            },
            "top_merchants": df['Description'].value_counts().head(5).to_dict()
        }
        
        return summary


def main():
    print("=" * 60)
    print("BPI STATEMENT PARSER - TABLE EXTRACTION METHOD")
    print("=" * 60)
    
    parser = BPITableParser("../data/Statement BPI Master 2025-05-12.pdf")
    
    start_time = time.time()
    
    try:
        # Extract tables from PDF
        print("Extracting tables from PDF...")
        tables = parser.extract_tables_from_pdf()
        
        print(f"Found {len(tables)} table(s) total")
        
        # Parse transactions from tables
        print("\nParsing transactions from tables...")
        df = parser.parse_transactions_from_tables(tables)
        
        extraction_time = time.time() - start_time
        
        if not df.empty:
            # Display results
            print(f"\n✓ Extracted {len(df)} transactions in {extraction_time:.2f} seconds")
            print("\nFirst 5 transactions:")
            print(df.head())
            
            # Save to CSV
            parser.save_to_csv(df)
            
            # Get summary
            summary = parser.get_summary(df)
            print(f"\nSummary:")
            print(f"Total transactions: {summary['total_transactions']}")
            print(f"Total amount: ₱{summary['total_amount']:,.2f}")
            print(f"Transactions by card: {summary['transactions_by_card']}")
            print(f"Processing time: {extraction_time:.2f} seconds")
            
        else:
            print("No transactions found in the statement")
            print(f"Processing time: {extraction_time:.2f} seconds")
            
    except Exception as e:
        print(f"Error processing statement: {e}")
        logging.error(f"Error processing statement: {e}")


if __name__ == "__main__":
    main()