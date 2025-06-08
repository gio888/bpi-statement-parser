# currency_handler.py - Clean enhanced version with flexible currency support
import pandas as pd
from datetime import datetime
from typing import Optional

class CurrencyHandler:
    def __init__(self):
        # Expanded currency symbols (no longer limiting)
        self.currency_symbols = {
            'PHP': '₱', 'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥',
            'SGD': 'S$', 'NZD': 'NZ$', 'CAD': 'CA$', 'AUD': 'A$', 
            'CHF': 'CHF', 'THB': '฿', 'HKD': 'HK$', 'KRW': '₩'
        }
    
    def get_currency_symbol(self, currency_code: str) -> str:
        """Get currency symbol - falls back to currency code if not found"""
        return self.currency_symbols.get(currency_code.upper(), currency_code)
    
    def enhance_with_currency(self, transactions):
        """Add currency information (already done in parser)"""
        return transactions
    
    def calculate_exchange_rate(self, amount: float, foreign_amount: float) -> Optional[float]:
        """Calculate exchange rate from PHP amount and foreign amount"""
        if foreign_amount and foreign_amount != 0:
            return round(amount / foreign_amount, 4)
        return None
    
    def clean_dataframe(self, df, statement_year=None):
        """Clean and format DataFrame with exchange rates"""
        year_to_use = statement_year or datetime.now().year
        
        # Convert dates
        for date_col in ['transaction_date', 'post_date']:
            if date_col in df.columns:
                df[date_col] = df[date_col].apply(lambda x: self._parse_date(x, year_to_use))
        
        # Add Exchange Rate column
        if 'amount' in df.columns and 'foreign_amount' in df.columns:
            df['exchange_rate'] = df.apply(
                lambda row: self.calculate_exchange_rate(row['amount'], row['foreign_amount']), 
                axis=1
            )
        
        # Sort by date
        if 'transaction_date' in df.columns:
            df = df.sort_values('transaction_date').reset_index(drop=True)
        
        # Capitalize column names for output
        df.columns = [col.replace('_', ' ').title() for col in df.columns]
        
        return df
    
    def _parse_date(self, date_str, year):
        """Parse date string - handles dates with or without year"""
        if not date_str:
            return None
    
        # First, try parsing as complete date (already has year)
        try:
            return datetime.strptime(date_str, "%B %d %Y")  # "May 1 2025"
        except ValueError:
            try:
                return datetime.strptime(date_str, "%b %d %Y")  # "May 1 2025" 
            except ValueError:
                pass
    
        # Fallback: try adding year (old format)
        try:
            return datetime.strptime(f"{date_str} {year}", "%b %d %Y")  # "May 1" + year
        except ValueError:
            try:
                return datetime.strptime(f"{date_str} {year}", "%B %d %Y")  # "May 1" + year
            except ValueError:
                return None
    
    def print_summary(self, df):
        """Print transaction summary"""
        print(f"\n📊 SUMMARY")
        print(f"Total transactions: {len(df)}")
        print(f"Total amount (PHP): ₱{df['Amount'].sum():,.2f}")
        
        print(f"\n💱 CURRENCY BREAKDOWN:")
        for currency in df['Currency'].unique():
            curr_data = df[df['Currency'] == currency]
            count = len(curr_data)
            php_total = curr_data['Amount'].sum()
            
            if currency == 'PHP':
                print(f"  {currency}: {count} transactions, ₱{php_total:,.2f}")
            else:
                if 'Foreign Amount' in curr_data.columns:
                    foreign_total = curr_data['Foreign Amount'].sum()
                    symbol = self.get_currency_symbol(currency)
                    print(f"  {currency}: {count} transactions, ₱{php_total:,.2f} ({symbol}{foreign_total:,.2f})")
        
        # Exchange rate summary
        if 'Exchange Rate' in df.columns:
            forex_transactions = df[df['Exchange Rate'].notna()]
            if len(forex_transactions) > 0:
                print(f"\n💹 EXCHANGE RATES:")
                for currency in forex_transactions['Currency'].unique():
                    if currency != 'PHP':
                        curr_rates = forex_transactions[forex_transactions['Currency'] == currency]['Exchange Rate']
                        if len(curr_rates) > 0:
                            avg_rate = curr_rates.mean()
                            min_rate = curr_rates.min()
                            max_rate = curr_rates.max()
                            print(f"  {currency}: Avg {avg_rate:.4f} (Range: {min_rate:.4f} - {max_rate:.4f})")
        
        print(f"\n📄 SAMPLE TRANSACTIONS:")
        display_cols = ['Transaction Date', 'Description', 'Amount', 'Currency']
        available_cols = [col for col in display_cols if col in df.columns]
        if len(df) > 0 and available_cols:
            sample_df = df[available_cols].head(3)
            print(sample_df.to_string(index=False))
    
    def get_currency_totals(self, df):
        """Get totals by currency"""
        currency_totals = {}
        
        for currency in df['Currency'].unique():
            curr_data = df[df['Currency'] == currency]
            php_total = curr_data['Amount'].sum()
            
            if currency == 'PHP':
                currency_totals[currency] = {
                    'count': len(curr_data),
                    'php_amount': php_total,
                    'foreign_amount': None,
                    'avg_exchange_rate': None
                }
            else:
                foreign_total = curr_data['Foreign Amount'].sum() if 'Foreign Amount' in curr_data.columns else 0
                avg_rate = None
                if 'Exchange Rate' in curr_data.columns:
                    rates = curr_data['Exchange Rate'].dropna()
                    avg_rate = rates.mean() if len(rates) > 0 else None
                
                currency_totals[currency] = {
                    'count': len(curr_data),
                    'php_amount': php_total,
                    'foreign_amount': foreign_total,
                    'avg_exchange_rate': avg_rate
                }
        
        return currency_totals
    
    def format_amount(self, amount, currency='PHP'):
        """Format amount with currency symbol"""
        symbol = self.get_currency_symbol(currency)
        return f"{symbol}{amount:,.2f}"
    
    def get_exchange_rate(self, transactions, from_currency, to_currency='PHP'):
        """Calculate average exchange rate from transactions"""
        if from_currency == to_currency:
            return 1.0
        
        rates = []
        for transaction in transactions:
            if (transaction['currency'] == from_currency and 
                transaction['foreign_amount'] and 
                transaction['amount']):
                rate = transaction['amount'] / transaction['foreign_amount']
                rates.append(rate)
        
        return sum(rates) / len(rates) if rates else None