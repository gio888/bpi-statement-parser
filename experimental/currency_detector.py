# currency_detector.py - Generic currency detection
import re
import json
import os
from typing import Optional, Dict

class GenericCurrencyDetector:
    def __init__(self):
        # Load or create currency knowledge base
        self.currency_db_file = "currency_knowledge.json"
        self.currency_knowledge = self._load_currency_knowledge()
        
        # Generic patterns for detecting currencies
        self.currency_patterns = [
            # Pattern 1: "Currency Name" + amount + peso amount
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*Dollar\s+([\d.,]+)\s+(\d{1,3}(?:,\d{3})*\.\d{2})',
            
            # Pattern 2: Country code patterns  
            r'\b([A-Z]{2,3})\s*$',  # US, SG, NZ, GBP, etc.
            
            # Pattern 3: Currency symbols or codes
            r'\b([A-Z]{3})\b',  # USD, EUR, GBP, etc.
            
            # Pattern 4: Currency names
            r'\b(Dollar|Pound|Euro|Yen|Won|Franc|Peso)\b',
        ]
    
    def _load_currency_knowledge(self) -> Dict:
        """Load existing currency knowledge or create new"""
        if os.path.exists(self.currency_db_file):
            try:
                with open(self.currency_db_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default knowledge base (minimal starter set)
        return {
            "country_codes": {
                "US": "USD", "SG": "SGD", "NZ": "NZD", "PH": "PHP"
            },
            "currency_names": {
                "U.S.Dollar": "USD", "US Dollar": "USD",
                "Singapore Dollar": "SGD",
                "New Zealand Dollar": "NZD", 
                "Philippine Peso": "PHP"
            },
            "discovered_patterns": {}
        }
    
    def _save_currency_knowledge(self):
        """Save learned currency patterns"""
        try:
            with open(self.currency_db_file, 'w') as f:
                json.dump(self.currency_knowledge, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save currency knowledge: {e}")
    
    def detect_currency(self, transaction_line: str, next_line: str = "") -> Dict:
        """
        Detect currency from transaction lines
        Returns: {currency: str, foreign_amount: float or None, confidence: str}
        """
        combined_text = f"{transaction_line} {next_line}".strip()
        
        # Method 1: Check known currency names
        for name, currency in self.currency_knowledge["currency_names"].items():
            if name in combined_text:
                amount = self._extract_amount_after_currency(combined_text, name)
                return {
                    "currency": currency,
                    "foreign_amount": amount,
                    "confidence": "high",
                    "source": f"known_name:{name}"
                }
        
        # Method 2: Check known country codes
        for pattern in [r'\b([A-Z]{2})\s*$', r'\b([A-Z]{3})\s*$']:
            match = re.search(pattern, transaction_line)
            if match:
                code = match.group(1)
                if code in self.currency_knowledge["country_codes"]:
                    return {
                        "currency": self.currency_knowledge["country_codes"][code],
                        "foreign_amount": None,
                        "confidence": "high",
                        "source": f"country_code:{code}"
                    }
                else:
                    # Unknown country code - learn it!
                    currency = self._learn_new_currency(code, combined_text)
                    return {
                        "currency": currency,
                        "foreign_amount": None,
                        "confidence": "learned",
                        "source": f"learned_country:{code}"
                    }
        
        # Method 3: Generic currency pattern detection
        currency_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+([\d.,]+)\s+(\d{1,3}(?:,\d{3})*\.\d{2})', combined_text)
        if currency_match:
            currency_name = currency_match.group(1)
            foreign_amount = float(currency_match.group(2).replace(',', ''))
            
            # Try to map to known currency or learn new one
            currency_code = self._map_currency_name_to_code(currency_name)
            
            return {
                "currency": currency_code,
                "foreign_amount": foreign_amount,
                "confidence": "medium",
                "source": f"pattern_match:{currency_name}"
            }
        
        # Default: PHP for domestic transactions
        return {
            "currency": "PHP",
            "foreign_amount": None,
            "confidence": "default",
            "source": "default_domestic"
        }
    
    def _extract_amount_after_currency(self, text: str, currency_name: str) -> Optional[float]:
        """Extract foreign amount after currency name"""
        pattern = rf'{re.escape(currency_name)}\s+([\d.,]+)'
        match = re.search(pattern, text)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except ValueError:
                pass
        return None
    
    def _learn_new_currency(self, code: str, context: str) -> str:
        """Learn new currency from context"""
        print(f"🔍 Learning new currency code: {code}")
        print(f"   Context: {context[:100]}...")
        
        # Try to infer currency from common patterns
        if len(code) == 2:
            # Country code - generate likely currency code
            inferred_currency = f"{code}D"  # USD, SGD, etc.
        else:
            # Already looks like currency code
            inferred_currency = code
        
        # Save to knowledge base
        self.currency_knowledge["country_codes"][code] = inferred_currency
        self.currency_knowledge["discovered_patterns"][code] = {
            "inferred_currency": inferred_currency,
            "first_seen": context[:200],
            "confidence": "auto_learned"
        }
        
        # Save immediately
        self._save_currency_knowledge()
        
        print(f"   💡 Learned: {code} → {inferred_currency}")
        return inferred_currency
    
    def _map_currency_name_to_code(self, currency_name: str) -> str:
        """Map currency name to standard code"""
        # Common mappings
        name_mappings = {
            "Dollar": "USD",  # Default dollar to USD
            "Pound": "GBP",
            "Euro": "EUR", 
            "Yen": "JPY",
            "Won": "KRW",
            "Franc": "CHF",
            "Peso": "PHP"
        }
        
        for name, code in name_mappings.items():
            if name.lower() in currency_name.lower():
                # Learn this specific mapping
                self.currency_knowledge["currency_names"][currency_name] = code
                self._save_currency_knowledge()
                return code
        
        # If unknown, create a code from the name
        words = currency_name.split()
        if len(words) >= 2:
            # "Canadian Dollar" → "CAD"
            code = f"{words[0][:2].upper()}{words[1][0].upper()}"
        else:
            # "Euro" → "EUR"
            code = currency_name[:3].upper()
        
        # Learn it
        self.currency_knowledge["currency_names"][currency_name] = code
        self._save_currency_knowledge()
        
        print(f"🔍 New currency learned: {currency_name} → {code}")
        return code
    
    def get_currency_symbol(self, currency_code: str) -> str:
        """Get currency symbol with fallback"""
        symbols = {
            'PHP': '₱', 'USD': '$', 'EUR': '€', 'GBP': '£', 
            'JPY': '¥', 'SGD': 'S$', 'NZD': 'NZ$', 'CAD': 'C$',
            'AUD': 'A$', 'CHF': 'Fr', 'KRW': '₩'
        }
        return symbols.get(currency_code, currency_code)
    
    def print_knowledge_summary(self):
        """Print what the system has learned"""
        print(f"\n🧠 CURRENCY KNOWLEDGE SUMMARY:")
        print(f"Known country codes: {len(self.currency_knowledge['country_codes'])}")
        print(f"Known currency names: {len(self.currency_knowledge['currency_names'])}")
        print(f"Discovered patterns: {len(self.currency_knowledge['discovered_patterns'])}")
        
        if self.currency_knowledge['discovered_patterns']:
            print(f"\n🆕 Recently discovered:")
            for code, info in self.currency_knowledge['discovered_patterns'].items():
                print(f"  {code} → {info['inferred_currency']}")