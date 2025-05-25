import pandas as pd
import pdfplumber
import re
from datetime import datetime
from typing import List, Dict, Any
import logging
import time

class BPIHybridParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def extract_text_from_pdf(self) -> str:
        """Extract text from PDF using pdfplumber (better than PyPDF2)"""
        try:
            text = ""
            with pdfplumber.open(self.file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            self.logger.error(f"Error reading PDF: {e}")
            raise

    def parse_transactions(self, text: str) -> pd.DataFrame:
        """Parse transaction data from extracted text"""
        transactions = []
        
        # Split text into sections for each card
        card_sections = self._split_by_cards(text)
        
        for card_name, section in card_sections.items():
            card_transactions = self._extract_card_transactions(section, card_name)
            transactions.extend(card_transactions)
        
        # Create DataFrame
        df = pd.DataFrame(transactions)
        
        if not df.empty:
            # Clean and format data
            df = self._clean_dataframe(df)
            
        return df

    def _split_by_cards(self, text: str) -> Dict[str, str]:
        """Split text into sections for each card type"""
        sections = {}
        
        # Look for "BPI GOLD REWARDS CARD" and "BPI ECREDIT CARD" patterns
        gold_pattern = r'(BPI\s*GOLD\s*REWARDS\s*CARD.*?)(?=BPI\s*ECREDIT\s*CARD|\Z)'
        ecredit_pattern = r'(BPI\s*ECREDIT\s*CARD.*?)(?=BPI\s*GOLD\s*REWARDS\s*CARD|\Z)'
        
        gold_match = re.search(gold_pattern, text, re.DOTALL | re.IGNORECASE)
        ecredit_match = re.search(ecredit_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if gold_match:
            sections['BPI GOLD REWARDS CARD'] = gold_match.group(1)
        
        if ecredit_match:
            sections['BPI ECREDIT CARD'] = ecredit_match.group(1)
            
        return sections

    def _extract_card_transactions(self, section: str, card_name: str) -> List[Dict[str, Any]]:
        """Extract transactions from a card section"""
        transactions = []
        lines = section.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
                
            if self._should_skip_line(line):
                i += 1
                continue
            
            # PHP transaction pattern (single line)
            # "April 24 April 24 Apple.Com/Bill Itunes.Com 524.19"
            php_pattern = r'^([A-Za-z]{3,9})\s+(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{1,2})\s+(.+?)\s+(\d{1,3}(?:,\d{3})*\.\d{2})$'
            php_match = re.match(php_pattern, line)
            
            if php_match:
                trans_month = php_match.group(1)
                trans_day = php_match.group(2)
                post_month = php_match.group(3)
                post_day = php_match.group(4)
                description = php_match.group(5).strip()
                amount_str = php_match.group(6)
                
                transaction_date = f"{trans_month} {trans_day}"
                post_date = f"{post_month} {post_day}"
                description = self._clean_description(description)
                
                try:
                    amount_float = float(amount_str.replace(',', ''))
                    if amount_float >= 0.01 and len(description) >= 3:
                        transactions.append({
                            'Card_Type': card_name,
                            'Transaction_Date': transaction_date,
                            'Post_Date': post_date,
                            'Description': description,
                            'Amount': amount_float
                        })
                except ValueError:
                    pass
                
                i += 1
                continue
            
            # Foreign currency pattern (two lines)
            # Line 1: "April 22 April 24 Dnh*Godaddy#372157851 Tempe US"
            # Line 2: "U.S. Dollar 32.17 1,860.53"
            foreign_pattern = r'^([A-Za-z]{3,9})\s+(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{1,2})\s+(.+?)\s+(US|SG|NZ)$'
            foreign_match = re.match(foreign_pattern, line)
            
            if foreign_match and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                currency_pattern = r'U\.S\.\s+Dollar\s+[\d.,]+\s+(\d{1,3}(?:,\d{3})*\.\d{2})$'
                currency_match = re.search(currency_pattern, next_line)
                
                if currency_match:
                    trans_month = foreign_match.group(1)
                    trans_day = foreign_match.group(2)
                    post_month = foreign_match.group(3)
                    post_day = foreign_match.group(4)
                    description = foreign_match.group(5).strip()
                    amount_str = currency_match.group(1)
                    
                    transaction_date = f"{trans_month} {trans_day}"
                    post_date = f"{post_month} {post_day}"
                    description = self._clean_description(description)
                    
                    try:
                        amount_float = float(amount_str.replace(',', ''))
                        if amount_float >= 0.01 and len(description) >= 3:
                            transactions.append({
                                'Card_Type': card_name,
                                'Transaction_Date': transaction_date,
                                'Post_Date': post_date,
                                'Description': description,
                                'Amount': amount_float
                            })
                    except ValueError:
                        pass
                    
                    i += 2
                    continue
            
            i += 1
        
        return transactions

    def _should_skip_line(self, line: str) -> bool:
        """Check if line should be skipped"""
        skip_patterns = [
            r'Previous Balance',
            r'Past Due',
            r'Ending Balance',
            r'Unbilled Installment Amount',
            r'Finance Charge',
            r'Payment.*Thank You',
            r'Transaction\s+Post.*Date\s+Description\s+Amount',
            r'Date\s*$',
            r'^\s*$',
            r'BPI.*CARD',
            r'Statement of Account',
            r'Customer Number',
            r'^\d{6}-\d-\d{2}-\d{7}',
            r'GIOVANNI BACAREZA',
            r'^Transaction\s*$',
            r'^Post Date\s*$',
            r'^Description\s*$',
            r'^Amount\s*$'
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False

    def _clean_description(self, description: str) -> str:
        """Clean transaction description"""
        # Remove currency information and country codes
        description = re.sub(r'U\.S\.\s+Dollar\s+[\d.]+', '', description)
        description = re.sub(r'\s+(US|SG|NZ)\s*$', '', description)
        
        # Clean up extra spaces
        description = ' '.join(description.split())
        
        return description.strip()

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and format the DataFrame"""
        # Convert date columns to datetime
        current_year = datetime.now().year
        
        for date_col in ['Transaction_Date', 'Post_Date']:
            df[date_col] = df[date_col].apply(lambda x: self._parse_date(x, current_year))
        
        # Sort by transaction date
        df = df.sort_values('Transaction_Date').reset_index(drop=True)
        
        return df

    def _parse_date(self, date_str: str, year: int) -> datetime:
        """Parse date string to datetime object"""
        try:
            date_obj = datetime.strptime(f"{date_str} {year}", "%b %d %Y")
            return date_obj
        except ValueError:
            try:
                date_obj = datetime.strptime(f"{date_str} {year}", "%B %d %Y")
                return date_obj
            except ValueError:
                self.logger.warning(f"Could not parse date: {date_str}")
                return None

    def save_to_csv(self, df: pd.DataFrame, output_path: str = None):
        """Save DataFrame to CSV"""
        if output_path is None:
            output_path = f"../data/output/bpi_hybrid_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
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
    print("BPI STATEMENT PARSER - HYBRID METHOD")
    print("pdfplumber text extraction + regex parsing")
    print("=" * 60)
    
    parser = BPIHybridParser("../data/Statement BPI Master 2025-05-12.pdf")
    
    start_time = time.time()
    
    try:
        print("Extracting text from PDF...")
        text = parser.extract_text_from_pdf()
        
        print(f"Extracted text length: {len(text)} characters")
        print("First 500 characters of extracted text:")
        print("=" * 50)
        print(text[:500])
        print("=" * 50)
        
        print("Parsing transactions...")
        df = parser.parse_transactions(text)
        
        extraction_time = time.time() - start_time
        
        if not df.empty:
            print(f"✓ Extracted {len(df)} transactions in {extraction_time:.2f} seconds")
            print("\nFirst 5 transactions:")
            print(df.head())
            
            parser.save_to_csv(df)
            
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