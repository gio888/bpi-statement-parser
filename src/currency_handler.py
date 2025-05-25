# currency_handler.py - Handles currency processing and output
import pandas as pd
from datetime import datetime

class CurrencyHandler:
    def __init__(self):
        self.currency_symbols = {
            'PHP': '₱',
            'USD': '$',
            'SGD': 'S$',
            'NZD': 'NZ$'
        }
    
    def enhance_with_currency(self, transactions):
        """Add currency information (already done in parser)"""
        return transactions
    
    def clean_dataframe(self, df):
        """Clean and format DataFrame"""
        current_year = datetime.now().year
        
        # Convert dates
        for date_col in ['transaction_date', 'post_date']:
            if date_col in df.columns:
                df[date_col] = df[date_col].apply(lambda x: self._parse_date(x, current_year))
        
        # Sort by date
        if 'transaction_date' in df.columns:
            df = df.sort_values('transaction_date').reset_index(drop=True)
        
        # Capitalize column names for output
        df.columns = [col.replace('_', ' ').title() for col in df.columns]
        
        return df
    
    def _parse_date(self, date_str, year):
        """Parse date string"""
        if not date_str:
            return None
            
        try:
            return datetime.strptime(f"{date_str} {year}", "%b %d %Y")
        except ValueError:
            try:
                return datetime.strptime(f"{date_str} {year}", "%B %d %Y")
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
                foreign_total = curr_data['Foreign Amount'].sum()
                symbol = self.currency_symbols.get(currency, currency)
                print(f"  {currency}: {count} transactions, ₱{php_total:,.2f} ({symbol}{foreign_total:,.2f})")
        
        print(f"\n📄 SAMPLE TRANSACTIONS:")
        display_cols = ['Transaction Date', 'Description', 'Amount', 'Currency']
        if len(df) > 0:
            sample_df = df[display_cols].head(3)
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
                    'foreign_amount': None
                }
            else:
                foreign_total = curr_data['Foreign Amount'].sum()
                currency_totals[currency] = {
                    'count': len(curr_data),
                    'php_amount': php_total,
                    'foreign_amount': foreign_total
                }
        
        return currency_totals
    
    def format_amount(self, amount, currency='PHP'):
        """Format amount with currency symbol"""
        symbol = self.currency_symbols.get(currency, currency)
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