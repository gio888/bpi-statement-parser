import pandas as pd
import re
from datetime import datetime
from typing import List, Dict, Any
import logging

class BPIStatementParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def extract_text_from_pdf(self) -> str:
        """Extract text from PDF file"""
        try:
            import PyPDF2
            with open(self.file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
            return text
        except ImportError:
            self.logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
            raise
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
        
        # Handle spaced out text like "B P I G O L D R E W A R D S C A R D"
        # Look for patterns with optional spaces between characters
        gold_pattern = r'(B\s*P\s*I\s*G\s*O\s*L\s*D\s*R\s*E\s*W\s*A\s*R\s*D\s*S\s*C\s*A\s*R\s*D.*?)(?=B\s*P\s*I\s*E\s*C\s*R\s*E\s*D\s*I\s*T|\Z)'
        ecredit_pattern = r'(B\s*P\s*I\s*E\s*C\s*R\s*E\s*D\s*I\s*T\s*C\s*A\s*R\s*D.*?)(?=B\s*P\s*I\s*G\s*O\s*L\s*D|\Z)'
        
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
        
        # Clean up the spaced text
        cleaned_section = re.sub(r'([A-Za-z])\s+([A-Za-z])', r'\1\2', section)
        cleaned_section = re.sub(r'\s+', ' ', cleaned_section)
        
        lines = cleaned_section.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
                
            # Skip non-transaction lines
            if self._should_skip_line(line):
                i += 1
                continue
            
            # Look for transaction pattern: "Month Day Month Day Description"
            trans_pattern = r'^([A-Za-z]{3,9})(\d{1,2})\s+([A-Za-z]{3,9})(\d{1,2})\s+(.+)

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
        # Remove currency information
        description = re.sub(r'U\.S\.\s+Dollar\s+[\d.]+', '', description)
        description = re.sub(r'Singapore\s*$', '', description)
        description = re.sub(r'U\s*S\s*$', '', description)
        description = re.sub(r'N\s*Z\s*$', '', description)
        
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
            # Handle "May 9" format
            date_obj = datetime.strptime(f"{date_str} {year}", "%b %d %Y")
            return date_obj
        except ValueError:
            self.logger.warning(f"Could not parse date: {date_str}")
            return None

    def save_to_csv(self, df: pd.DataFrame, output_path: str = None):
        """Save DataFrame to CSV"""
        if output_path is None:
            output_path = f"../data/output/bpi_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
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
    parser = BPIStatementParser("../data/Statement BPI Master 2025-05-12.pdf")
    
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
        
        if not df.empty:
            print(f"✓ Extracted {len(df)} transactions")
            print("\nFirst 5 transactions:")
            print(df.head())
            
            parser.save_to_csv(df)
            
            summary = parser.get_summary(df)
            print(f"\nSummary:")
            print(f"Total transactions: {summary['total_transactions']}")
            print(f"Total amount: ₱{summary['total_amount']:,.2f}")
            print(f"Transactions by card: {summary['transactions_by_card']}")
            
        else:
            print("No transactions found in the statement")
            
    except Exception as e:
        print(f"Error processing statement: {e}")
        logging.error(f"Error processing statement: {e}")


if __name__ == "__main__":
    main()
            match = re.match(trans_pattern, line)
            
            if match:
                trans_month = match.group(1)
                trans_day = match.group(2)
                post_month = match.group(3)
                post_day = match.group(4)
                description = match.group(5).strip()
                
                # Look for amount in the next line(s)
                amount_found = False
                j = i + 1
                
                while j < len(lines) and not amount_found:
                    next_line = lines[j].strip()
                    
                    # Look for amount pattern in next line
                    amount_pattern = r'(\d{1,3}(?:,\d{3})*\.\d{2})

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
        # Remove currency information
        description = re.sub(r'U\.S\.\s+Dollar\s+[\d.]+', '', description)
        description = re.sub(r'Singapore\s*$', '', description)
        description = re.sub(r'U\s*S\s*$', '', description)
        description = re.sub(r'N\s*Z\s*$', '', description)
        
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
            # Handle "May 9" format
            date_obj = datetime.strptime(f"{date_str} {year}", "%b %d %Y")
            return date_obj
        except ValueError:
            self.logger.warning(f"Could not parse date: {date_str}")
            return None

    def save_to_csv(self, df: pd.DataFrame, output_path: str = None):
        """Save DataFrame to CSV"""
        if output_path is None:
            output_path = f"../data/output/bpi_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
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
    # Updated to use your specific PDF filename
    parser = BPIStatementParser("../data/Statement BPI Master 2025-05-12.pdf")
    
    try:
        # Extract text from PDF
        print("Extracting text from PDF...")
        text = parser.extract_text_from_pdf()
        
        # DEBUG: Let's see what text was extracted
        print(f"Extracted text length: {len(text)} characters")
        print("First 500 characters of extracted text:")
        print("=" * 50)
        print(text[:500])
        print("=" * 50)
        
        # Parse transactions
        print("Parsing transactions...")
        df = parser.parse_transactions(text)
        
        # DEBUG: Check card sections
        card_sections = parser._split_by_cards(text)
        print(f"Found card sections: {list(card_sections.keys())}")
        for card_name, section in card_sections.items():
            print(f"\n{card_name} section length: {len(section)} characters")
            print(f"Full {card_name} section:")
            print("=" * 60)
            print(section)
            print("=" * 60)
        
        if not df.empty:
            # Display results
            print(f"✓ Extracted {len(df)} transactions")
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
            
        else:
            print("No transactions found in the statement")
            
    except Exception as e:
        print(f"Error processing statement: {e}")
        logging.error(f"Error processing statement: {e}")


if __name__ == "__main__":
    main()
                    amount_match = re.search(amount_pattern, next_line)
                    
                    if amount_match:
                        amount_str = amount_match.group(1)
                        amount_found = True
                        
                        # Also add any additional description from this line
                        desc_part = re.sub(amount_pattern, '', next_line).strip()
                        if desc_part and not re.match(r'U\.S\.Dollar', desc_part):
                            description += ' ' + desc_part
                        
                        break
                    else:
                        # Check if this line has additional description
                        if not self._should_skip_line(next_line) and len(next_line) > 2:
                            # Add to description if it's not a new transaction
                            if not re.match(r'^[A-Za-z]{3,9}\d{1,2}', next_line):
                                description += ' ' + next_line
                    
                    j += 1
                
                if amount_found:
                    # Reconstruct dates
                    transaction_date = f"{trans_month} {trans_day}"
                    post_date = f"{post_month} {post_day}"
                    
                    # Clean description
                    description = self._clean_description(description)
                    
                    # Skip if description is too short
                    if len(description) < 3:
                        i += 1
                        continue
                    
                    # Convert amount
                    try:
                        amount_float = float(amount_str.replace(',', ''))
                        if amount_float < 0.01:
                            i += 1
                            continue
                    except ValueError:
                        i += 1
                        continue
                    
                    transactions.append({
                        'Card_Type': card_name,
                        'Transaction_Date': transaction_date,
                        'Post_Date': post_date,
                        'Description': description,
                        'Amount': amount_float
                    })
                    
                    # Skip to after the amount line
                    i = j + 1
                else:
                    i += 1
            else:
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
        # Remove currency information
        description = re.sub(r'U\.S\.\s+Dollar\s+[\d.]+', '', description)
        description = re.sub(r'Singapore\s*$', '', description)
        description = re.sub(r'U\s*S\s*$', '', description)
        description = re.sub(r'N\s*Z\s*$', '', description)
        
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
            # Handle "May 9" format
            date_obj = datetime.strptime(f"{date_str} {year}", "%b %d %Y")
            return date_obj
        except ValueError:
            self.logger.warning(f"Could not parse date: {date_str}")
            return None

    def save_to_csv(self, df: pd.DataFrame, output_path: str = None):
        """Save DataFrame to CSV"""
        if output_path is None:
            output_path = f"../data/output/bpi_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
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
    # Updated to use your specific PDF filename
    parser = BPIStatementParser("../data/Statement BPI Master 2025-05-12.pdf")
    
    try:
        # Extract text from PDF
        print("Extracting text from PDF...")
        text = parser.extract_text_from_pdf()
        
        # DEBUG: Let's see what text was extracted
        print(f"Extracted text length: {len(text)} characters")
        print("First 500 characters of extracted text:")
        print("=" * 50)
        print(text[:500])
        print("=" * 50)
        
        # Parse transactions
        print("Parsing transactions...")
        df = parser.parse_transactions(text)
        
        # DEBUG: Check card sections
        card_sections = parser._split_by_cards(text)
        print(f"Found card sections: {list(card_sections.keys())}")
        for card_name, section in card_sections.items():
            print(f"\n{card_name} section length: {len(section)} characters")
            print(f"Full {card_name} section:")
            print("=" * 60)
            print(section)
            print("=" * 60)
        
        if not df.empty:
            # Display results
            print(f"✓ Extracted {len(df)} transactions")
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
            
        else:
            print("No transactions found in the statement")
            
    except Exception as e:
        print(f"Error processing statement: {e}")
        logging.error(f"Error processing statement: {e}")


if __name__ == "__main__":
    main()