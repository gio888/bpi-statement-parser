# transaction_parser.py - Final version with normalizer (drop-in replacement)
import re
from datetime import datetime  

class SimplePDFNormalizer:
    """Simple, reliable PDF text normalizer"""
    
    def __init__(self):
        self.months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
    
    def normalize_line(self, line: str) -> str:
        """Normalize a single line with targeted fixes"""
        if not line:
            return line
        
        # Step 1: Basic whitespace cleanup
        text = re.sub(r'\s+', ' ', line.strip())
        
        # Step 2: Fix specific known issues in order
        text = self._fix_currency_dots(text)
        text = self._fix_month_spacing(text)
        text = self._fix_amount_spacing(text)
        
        return text
    
    def _fix_currency_dots(self, text: str) -> str:
        """Fix U.S.Dollar variations specifically"""
        variations = [
            r'U\s*\.\s*S\s*\.\s*Dollar',  # "U . S . Dollar"
            r'U\s*S\s*Dollar',            # "US Dollar"
            r'U\.S\s*Dollar',             # "U.S Dollar"
            r'U\s*\.\s*S\s*Dollar',       # "U . S Dollar"
        ]
        
        for pattern in variations:
            text = re.sub(pattern, 'U.S.Dollar', text, flags=re.IGNORECASE)
        
        return text
    
    def _fix_month_spacing(self, text: str) -> str:
        """Fix month-day spacing issues"""
        for month in self.months:
            # Fix "October1" -> "October 1"
            pattern = rf'\b{month}(\d{{1,2}})\b'
            text = re.sub(pattern, rf'{month} \1', text, flags=re.IGNORECASE)
            
            # Fix "15September" -> "15 September"
            pattern = rf'\b(\d{{1,2}}){month}\b'
            text = re.sub(pattern, rf'\1 {month}', text, flags=re.IGNORECASE)
        
        return text
    
    def _fix_amount_spacing(self, text: str) -> str:
        """Fix amount formatting"""
        # Fix "2 , 337 . 48" -> "2,337.48"
        text = re.sub(r'(\d+)\s*,\s*(\d+)', r'\1,\2', text)
        text = re.sub(r'(\d+)\s*\.\s*(\d+)', r'\1.\2', text)
        
        # Fix missing space before amounts at end
        text = re.sub(r'([A-Za-z])(-?\d{1,3}(?:,\d{3})*\.\d{2})$', r'\1 \2', text)
        
        return text


class TransactionParser:
    """Final transaction parser with PDF normalization - drop-in replacement"""
    
    def __init__(self):
        self.normalizer = SimplePDFNormalizer()
        self.skip_patterns = [
            r'Statement of Account', r'Customer Number', r'Previous Balance',
            r'Past Due', r'Ending Balance', r'Unbilled Installment', 
            r'^Finance Charge\s+\d', r'GIOVANNI BACAREZA',
            r'Transaction\s+Post.*Date', r'^\d{6}-\d-\d{2}-\d{7}',
            r'^(Date|Transaction|Post Date|Description|Amount)\s*$'
        ]
    
    def parse_transactions(self, text, statement_year=None):
        """Parse transactions with normalization"""
        transactions = []
        
        # Split into card sections first
        card_sections = self._split_by_cards(text)
        
        for card_name, section_text in card_sections.items():
            print(f"\n🔍 Processing {card_name}...")
            card_transactions = self._parse_card_section(section_text, card_name, statement_year)
            transactions.extend(card_transactions)
            print(f"   Found {len(card_transactions)} transactions")
        
        # Remove duplicates
        unique_transactions = self._remove_duplicates(transactions)
        print(f"\n🔄 After deduplication: {len(unique_transactions)} transactions")
        
        return unique_transactions
    
    def _split_by_cards(self, text):
        """Split by card headers - flexible detection"""
        sections = {}
        lines = text.split('\n')
        current_card = None
        current_section = []
        
        for line in lines:
            # Normalize line for header detection
            norm_line = self.normalizer.normalize_line(line).upper()
            
            # Check for any BPI Gold card variations
            if any(pattern in norm_line.replace(' ', '') for pattern in 
                   ['BPIGOLDREWARDS', 'GOLDREWARDS', 'BPIEXPRESSCREDITGOLDMASTERCARD']):
                if current_card and current_section:
                    sections[current_card] = '\n'.join(current_section)
                current_card = 'BPI GOLD REWARDS CARD'
                current_section = [line]
                
            # Check for any BPI E-Credit variations
            elif any(pattern in norm_line.replace(' ', '').replace('-', '') for pattern in 
                     ['BPIECREDIT', 'BPIECREDIT', 'ECREDITCARD']) and 'GOLD' not in norm_line:
                if current_card and current_section:
                    sections[current_card] = '\n'.join(current_section)
                current_card = 'BPI ECREDIT CARD'
                current_section = [line]
                
            elif current_card:
                current_section.append(line)
        
        if current_card and current_section:
            sections[current_card] = '\n'.join(current_section)
        
        if not sections:
            print("⚠️  No card headers found")
            sections['UNKNOWN_CARD'] = text
            
        return sections
    
    def _parse_card_section(self, section_text, card_name, statement_year=None):
        """Parse transactions from card section"""
        transactions = []
        lines = section_text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line or self._should_skip(line):
                i += 1
                continue
            
            # Normalize the line
            norm_line = self.normalizer.normalize_line(line)
            
            # Try single-line transaction
            transaction = self._parse_single_line(norm_line, card_name, statement_year)
            if transaction:
                transactions.append(transaction)
                print(f"   ✓ {transaction['currency']}: {transaction['description'][:30]}... - ₱{transaction['amount']}")
                i += 1
                continue
            
            # Try two-line foreign currency
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                norm_next = self.normalizer.normalize_line(next_line)
                
                transaction = self._parse_two_lines(norm_line, norm_next, card_name, statement_year)
                if transaction:
                    transactions.append(transaction)
                    print(f"   ✓ {transaction['currency']}: {transaction['description'][:30]}... - ₱{transaction['amount']}")
                    i += 2
                    continue
            
            i += 1
        
        return transactions


    def _determine_transaction_year(self, month_name, statement_year, statement_month=None):
        """
        Determine correct year for transaction based on month and statement context
        """
        if not month_name or not statement_year:
            return statement_year
        
        try:
            # Convert month name to number
            month_num = datetime.strptime(month_name, "%B").month
        except ValueError:
            try:
                month_num = datetime.strptime(month_name, "%b").month
            except ValueError:
                return statement_year
        
        # Rule: December transactions get previous year ONLY if statement is January
        if month_num == 12 and statement_month == 1:
            return statement_year - 1
        
        return statement_year
        
    def _parse_single_line(self, line, card_name, statement_year=None):
        """Parse normalized single-line transaction with smart year assignment"""
        # Simple pattern that works after normalization
        pattern = r'^([A-Za-z]+)\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{1,2})\s+(.+?)\s+(-?\d{1,3}(?:,\d{3})*\.\d{2})$'
        match = re.match(pattern, line)
        
        if match:
            transaction_month = match.group(1)  # e.g., "December"
            post_month = match.group(3)         # e.g., "December" 
            
            # Determine correct years for both dates
            transaction_year = self._determine_transaction_year(transaction_month, statement_year)
            post_year = self._determine_transaction_year(post_month, statement_year)
            
            transaction = {
                'card': card_name,
                'transaction_date': f"{transaction_month} {match.group(2)} {transaction_year}",
                'post_date': f"{post_month} {match.group(4)} {post_year}",
                'description': match.group(5).strip(),
                'amount': float(match.group(6).replace(',', '')),
                'currency': 'PHP',
                'foreign_amount': None
            }
            
            # Debug output (you can remove this later)
            print(f"DEBUG: Created transaction_date: '{transaction['transaction_date']}' (month: {transaction_month}, year: {transaction_year})")
            print(f"DEBUG: statement_year passed: {statement_year}")
            
            return transaction
        return None
    
    def _parse_two_lines(self, line1, line2, card_name, statement_year=None):
        """Parse normalized two-line foreign currency with smart year assignment"""
        # After normalization, this should be reliable
        pattern1 = r'^([A-Za-z]+)\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{1,2})\s+(.+?)\s+([A-Z]{2,3})$'
        pattern2 = r'^U\.S\.Dollar\s+([\d.,]+)\s+(\d{1,3}(?:,\d{3})*\.\d{2})$'
        
        match1 = re.match(pattern1, line1)
        match2 = re.match(pattern2, line2)
        
        if match1 and match2:
            transaction_month = match1.group(1)  # e.g., "December"
            post_month = match1.group(3)         # e.g., "December"
            
            # Determine correct years for both dates
            transaction_year = self._determine_transaction_year(transaction_month, statement_year)
            post_year = self._determine_transaction_year(post_month, statement_year)
            
            country_code = match1.group(6)
            currency = 'USD' if country_code == 'US' else ('SGD' if country_code == 'SG' else 'NZD')
            
            return {
                'card': card_name,
                'transaction_date': f"{transaction_month} {match1.group(2)} {transaction_year}",
                'post_date': f"{post_month} {match1.group(4)} {post_year}",
                'description': match1.group(5).strip(),
                'amount': float(match2.group(2).replace(',', '')),
                'currency': currency,
                'foreign_amount': float(match2.group(1).replace(',', ''))
            }
        return None    
    
    def _should_skip(self, line):
        """Check if line should be skipped"""
        for pattern in self.skip_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False
    
    def _remove_duplicates(self, transactions):
        """Remove duplicate transactions"""
        seen = set()
        unique = []
        
        for transaction in transactions:
            key = (
                transaction['transaction_date'],
                transaction['post_date'], 
                transaction['description'],
                transaction['amount'],
                transaction['currency']
            )
            
            if key not in seen:
                seen.add(key)
                unique.append(transaction)
        
        return unique