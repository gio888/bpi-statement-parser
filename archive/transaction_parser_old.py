# transaction_parser.py - Complete version with generic currency detector
import re
from currency_detector import GenericCurrencyDetector  # Import your currency detector

class TransactionParser:
    def __init__(self):
        self.skip_patterns = [
            r'Statement of Account', 
            r'Customer Number', 
            r'Previous Balance',
            r'Past Due', 
            r'Ending Balance', 
            r'Unbilled Installment',
            r'^Finance Charge\s+\d',  # Only skip standalone finance charge lines
            r'GIOVANNI BACAREZA',
            r'Transaction\s+Post.*Date',
            r'^\d{6}-\d-\d{2}-\d{7}',
            r'^Date\s*$',
            r'^Transaction\s*$',
            r'^Post Date\s*$',
            r'^Description\s*$',
            r'^Amount\s*$'
        ]
        
        # Initialize generic currency detector
        self.currency_detector = GenericCurrencyDetector()
    
    def parse_transactions(self, text):
        """Parse transactions from text with card detection"""
        transactions = []
        
        # Split text into card sections
        card_sections = self._split_by_cards(text)
        
        for card_name, section_text in card_sections.items():
            print(f"\n🔍 Processing {card_name}...")
            card_transactions = self._parse_card_section(section_text, card_name)
            transactions.extend(card_transactions)
            print(f"   Found {len(card_transactions)} transactions")
        
        # Remove duplicates
        unique_transactions = self._remove_duplicates(transactions)
        print(f"\n🔄 After deduplication: {len(unique_transactions)} transactions")
        
        # Print currency learning summary
        self.currency_detector.print_knowledge_summary()
        
        return unique_transactions
    
    def _split_by_cards(self, text):
        """Split text into card sections"""
        sections = {}
        lines = text.split('\n')
        current_card = None
        current_section = []
        
        for line in lines:
            line_upper = line.upper().strip()
            
            # Check for card headers - 2025 format
            if ('BPIGOLDREWARDS' in line_upper.replace(' ', '') or 
                'GOLD REWARDS' in line_upper):
                if current_card and current_section:
                    sections[current_card] = '\n'.join(current_section)
                current_card = 'BPI GOLD REWARDS CARD'
                current_section = [line]
            elif ('BPIECREDIT' in line_upper.replace(' ', '') or 
                  'ECREDIT CARD' in line_upper):
                if current_card and current_section:
                    sections[current_card] = '\n'.join(current_section)
                current_card = 'BPI ECREDIT CARD'
                current_section = [line]
            
            # Check for card headers - 2023 format
            elif ('BPIEXPRESS CREDIT GOLDMASTERCARD' in line_upper or 
                  'BPI EXPRESS CREDIT GOLD MASTERCARD' in line_upper):
                if current_card and current_section:
                    sections[current_card] = '\n'.join(current_section)
                current_card = 'BPI GOLD REWARDS CARD'
                current_section = [line]
            elif (('BPIE-CREDIT' in line_upper or 'BPI E-CREDIT' in line_upper) and 
                  'MASTERCARD' not in line_upper):
                if current_card and current_section:
                    sections[current_card] = '\n'.join(current_section)
                current_card = 'BPI ECREDIT CARD'
                current_section = [line]
            
            elif current_card:
                current_section.append(line)
        
        # Add final section
        if current_card and current_section:
            sections[current_card] = '\n'.join(current_section)
        
        if not sections:
            print("⚠️  No card headers found")
            sections['UNKNOWN_CARD'] = text
        
        return sections
    
    def _parse_card_section(self, section_text, card_name):
        """Parse transactions from a card section"""
        transactions = []
        lines = section_text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line or self._should_skip(line):
                i += 1
                continue
            
            # Try single-line transaction
            transaction = self._parse_single_line(line, card_name)
            if transaction:
                transactions.append(transaction)
                print(f"   ✓ {transaction['currency']}: {transaction['description'][:30]}... - ₱{transaction['amount']}")
                i += 1
                continue
            
            # Try two-line foreign currency
            if i + 1 < len(lines):
                transaction = self._parse_two_lines(line, lines[i + 1], card_name)
                if transaction:
                    transactions.append(transaction)
                    print(f"   ✓ {transaction['currency']}: {transaction['description'][:30]}... - ₱{transaction['amount']}")
                    i += 2
                    continue
            
            i += 1
        
        return transactions
    
    def _parse_single_line(self, line, card_name):
        """Parse single-line transaction - handles both 2023 and 2025 formats"""
        # Universal pattern: handles both "October 1" and "May1" formats
        pattern = r'^([A-Za-z]{3,9})\s*(\d{1,2})\s+([A-Za-z]{3,9})\s*(\d{1,2})\s+(.+?)\s+(-?\d{1,3}(?:,\d{3})*\.\d{2})$'
        match = re.match(pattern, line)
        
        if match:
            description = match.group(5).strip()
            
            # Use generic currency detector
            currency_info = self.currency_detector.detect_currency(line)
            
            # Clean description if currency detector found embedded currency
            clean_description = description
            if currency_info.get('source', '').startswith('pattern_match'):
                # Remove currency info from description if it was embedded
                clean_description = re.sub(r'\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+[\d.,]+\s*$', '', description).strip()
            
            return {
                'card': card_name,
                'transaction_date': f"{match.group(1)} {match.group(2)}",
                'post_date': f"{match.group(3)} {match.group(4)}",
                'description': clean_description,
                'amount': float(match.group(6).replace(',', '')),
                'currency': currency_info['currency'],
                'foreign_amount': currency_info.get('foreign_amount')
            }
        
        return None
    
    def _parse_two_lines(self, line1, line2, card_name):
        """Parse two-line foreign currency transaction"""
        # Line 1: Foreign transaction ending with country code
        pattern1 = r'^([A-Za-z]{3,9})\s*(\d{1,2})\s+([A-Za-z]{3,9})\s*(\d{1,2})\s+(.+?)\s+(US|SG|NZ|[A-Z]{2,3})$'
        # Line 2: Currency conversion (more flexible pattern)
        pattern2 = r'^([A-Z][a-z]*(?:\s*[A-Z][a-z]*)*)\s*Dollar\s+([\d.,]+)\s+(\d{1,3}(?:,\d{3})*\.\d{2})$'
        
        match1 = re.match(pattern1, line1)
        match2 = re.match(pattern2, line2.strip())
        
        if match1 and match2:
            # Use generic currency detector to determine currency
            currency_info = self.currency_detector.detect_currency(line1, line2)
            
            return {
                'card': card_name,
                'transaction_date': f"{match1.group(1)} {match1.group(2)}",
                'post_date': f"{match1.group(3)} {match1.group(4)}",
                'description': match1.group(5).strip(),
                'amount': float(match2.group(3).replace(',', '')),
                'currency': currency_info['currency'],
                'foreign_amount': currency_info.get('foreign_amount', float(match2.group(2).replace(',', '')))
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