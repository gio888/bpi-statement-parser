# pdf_normalizer.py - Universal PDF text normalization
import re

class PDFTextNormalizer:
    """
    Handles all PDF extraction inconsistencies in one place:
    - Random spacing issues
    - Missing/extra dots and punctuation
    - Inconsistent currency formatting
    - Date format variations
    """
    
    def __init__(self):
        # Known patterns that need normalization
        self.currency_patterns = [
            # U.S.Dollar variations
            (r'U\.?\s*S\.?\s*Dollar', 'U.S.Dollar'),
            (r'US\s*Dollar', 'U.S.Dollar'),
            (r'USD\s*ollar', 'U.S.Dollar'),
            
            # Other currencies
            (r'Singapore\s*Dollar', 'Singapore Dollar'),
            (r'Canadian\s*Dollar', 'Canadian Dollar'),
            (r'Australian\s*Dollar', 'Australian Dollar'),
            (r'British\s*Pound', 'British Pound'),
            (r'Euro\s*Dollar', 'Euro'),
        ]
        
        self.month_patterns = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
    
    def normalize_text(self, text: str) -> str:
        """Apply all normalizations to text"""
        if not text:
            return text
            
        # Step 1: Clean excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Step 2: Fix currency formatting
        text = self._normalize_currencies(text)
        
        # Step 3: Fix date formatting  
        text = self._normalize_dates(text)
        
        # Step 4: Fix amount formatting
        text = self._normalize_amounts(text)
        
        # Step 5: Fix punctuation spacing
        text = self._normalize_punctuation(text)
        
        return text
    
    def _normalize_currencies(self, text: str) -> str:
        """Fix currency name variations"""
        for pattern, replacement in self.currency_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text
    
    def _normalize_dates(self, text: str) -> str:
        """Fix date formatting issues"""
        # Fix month-day spacing: "October1" -> "October 1"
        for month in self.month_patterns:
            # Missing space between month and number
            pattern = rf'\b{month}(\d{{1,2}})\b'
            replacement = rf'{month} \1'
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            
            # Extra spaces: "October  1" -> "October 1"
            pattern = rf'\b{month}\s+(\d{{1,2}})\b'
            replacement = rf'{month} \1'
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _normalize_amounts(self, text: str) -> str:
        """Fix amount formatting"""
        # Fix missing spaces before amounts at end of line
        text = re.sub(r'([A-Za-z])(-?\d{1,3}(?:,\d{3})*\.\d{2})$', r'\1 \2', text)
        
        # Fix spaces around decimal points: "1 . 50" -> "1.50"
        text = re.sub(r'(\d+)\s*\.\s*(\d+)', r'\1.\2', text)
        
        # Fix spaces around commas: "1 , 000" -> "1,000"
        text = re.sub(r'(\d+)\s*,\s*(\d+)', r'\1,\2', text)
        
        return text
    
    def _normalize_punctuation(self, text: str) -> str:
        """Fix punctuation spacing"""
        # Fix dots: "U . S . Dollar" -> "U.S.Dollar"
        text = re.sub(r'([A-Z])\s*\.\s*([A-Z])', r'\1.\2', text)
        
        # Fix missing spaces after periods in sentences
        text = re.sub(r'\.([A-Z])', r'. \1', text)
        
        # Fix hyphens: "E - CREDIT" -> "E-CREDIT"
        text = re.sub(r'([A-Z])\s*-\s*([A-Z])', r'\1-\2', text)
        
        return text
    
    def normalize_transaction_pair(self, line1: str, line2: str) -> tuple:
        """Normalize a pair of transaction lines"""
        return (self.normalize_text(line1), self.normalize_text(line2))
    
    def is_currency_line(self, line: str) -> bool:
        """Check if line contains currency information"""
        normalized = self.normalize_text(line)
        currency_indicators = [
            'U.S.Dollar', 'Dollar', 'Euro', 'Pound', 'Yen', 'Won'
        ]
        return any(indicator in normalized for indicator in currency_indicators)
    
    def extract_currency_info(self, line: str) -> dict:
        """Extract currency information from normalized line"""
        normalized = self.normalize_text(line)
        
        # Standard pattern: "U.S.Dollar 40.42 2,337.48"
        pattern = r'(U\.S\.Dollar|[\w\s]+Dollar|Euro|Pound)\s+([\d.,]+)\s+(\d{1,3}(?:,\d{3})*\.\d{2})'
        match = re.search(pattern, normalized)
        
        if match:
            return {
                'currency_name': match.group(1).strip(),
                'foreign_amount': float(match.group(2).replace(',', '')),
                'php_amount': float(match.group(3).replace(',', ''))
            }
        
        return None


# Enhanced transaction parser using normalizer
class EnhancedTransactionParser:
    def __init__(self):
        self.normalizer = PDFTextNormalizer()
        self.currency_detector = None  # Will be set if available
        
        # Simplified skip patterns
        self.skip_patterns = [
            r'Statement of Account', r'Customer Number', r'Previous Balance',
            r'Past Due', r'Ending Balance', r'Unbilled Installment',
            r'^Finance Charge\s+\d', r'GIOVANNI BACAREZA',
            r'Transaction\s+Post.*Date', r'^\d{6}-\d-\d{2}-\d{7}',
            r'^(Date|Transaction|Post Date|Description|Amount)\s*$'
        ]
    
    def set_currency_detector(self, detector):
        """Set currency detector if available"""
        self.currency_detector = detector
    
    def parse_transaction_line(self, line: str, next_line: str = "") -> dict:
        """Parse a single transaction with intelligent normalization"""
        # Normalize both lines
        norm_line = self.normalizer.normalize_text(line)
        norm_next = self.normalizer.normalize_text(next_line) if next_line else ""
        
        # Try single-line transaction first
        result = self._try_single_line(norm_line)
        if result:
            return result
        
        # Try two-line foreign currency
        if norm_next and self.normalizer.is_currency_line(norm_next):
            result = self._try_two_line(norm_line, norm_next)
            if result:
                result['lines_consumed'] = 2
                return result
        
        return None
    
    def _try_single_line(self, line: str) -> dict:
        """Try to parse as single-line transaction"""
        # Universal pattern works for both "October 1" and "May1" after normalization
        pattern = r'^([A-Za-z]+)\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{1,2})\s+(.+?)\s+(-?\d{1,3}(?:,\d{3})*\.\d{2})$'
        match = re.match(pattern, line)
        
        if match:
            return {
                'transaction_date': f"{match.group(1)} {match.group(2)}",
                'post_date': f"{match.group(3)} {match.group(4)}",
                'description': match.group(5).strip(),
                'amount': float(match.group(6).replace(',', '')),
                'currency': 'PHP',  # Default for single-line
                'foreign_amount': None,
                'lines_consumed': 1
            }
        return None
    
    def _try_two_line(self, line1: str, line2: str) -> dict:
        """Try to parse as two-line foreign currency transaction"""
        # First line: transaction with country code
        pattern1 = r'^([A-Za-z]+)\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{1,2})\s+(.+?)(?:\s+([A-Z]{2,3}))?$'
        match1 = re.match(pattern1, line1)
        
        if match1:
            # Extract currency info from second line
            currency_info = self.normalizer.extract_currency_info(line2)
            
            if currency_info:
                # Determine currency from name or use detector
                currency = self._map_currency_name(currency_info['currency_name'])
                
                return {
                    'transaction_date': f"{match1.group(1)} {match1.group(2)}",
                    'post_date': f"{match1.group(3)} {match1.group(4)}",
                    'description': match1.group(5).strip(),
                    'amount': currency_info['php_amount'],
                    'currency': currency,
                    'foreign_amount': currency_info['foreign_amount']
                }
        
        return None
    
    def _map_currency_name(self, currency_name: str) -> str:
        """Map currency name to code"""
        mapping = {
            'U.S.Dollar': 'USD',
            'US Dollar': 'USD', 
            'Singapore Dollar': 'SGD',
            'Canadian Dollar': 'CAD',
            'Australian Dollar': 'AUD',
            'Euro': 'EUR',
            'British Pound': 'GBP'
        }
        return mapping.get(currency_name, 'USD')  # Default to USD for "Dollar"


# Usage example
if __name__ == "__main__":
    normalizer = PDFTextNormalizer()
    
    # Test problematic lines
    test_lines = [
        "U.S.Dollar 40.42 2,337.48",
        "U . S . Dollar 40 . 42 2 , 337 . 48", 
        "US Dollar 40.42 2,337.48",
        "October1 October2 Payment -Thank You -905.60",
        "September 15September 18 Backblaze.Com SanMateo US"
    ]
    
    print("🔧 PDF TEXT NORMALIZATION TEST")
    print("="*50)
    
    for line in test_lines:
        normalized = normalizer.normalize_text(line)
        print(f"Original:   '{line}'")
        print(f"Normalized: '{normalized}'")
        print()