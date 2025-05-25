import pandas as pd
import tabula
from datetime import datetime
import time

def parse_bpi_with_tabula():
    print("=" * 60)
    print("BPI STATEMENT PARSER - TABULA METHOD")
    print("Specialized PDF table extraction")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Extract all tables from the PDF
        print("Extracting tables with tabula...")
        dfs = tabula.read_pdf(
            "../data/Statement BPI Master 2025-05-12.pdf", 
            pages='all',
            multiple_tables=True,
            pandas_options={'header': None}
        )
        
        print(f"Found {len(dfs)} table(s)")
        
        all_transactions = []
        
        for i, df in enumerate(dfs):
            print(f"\nTable {i+1}:")
            print(f"Shape: {df.shape}")
            print("First few rows:")
            print(df.head())
            print("\nAll data:")
            print(df.to_string())
            
            # Process this table for transactions
            transactions = process_tabula_table(df, i)
            all_transactions.extend(transactions)
        
        # Combine all transactions
        if all_transactions:
            final_df = pd.DataFrame(all_transactions)
            
            # Clean and format
            final_df = clean_dataframe(final_df)
            
            extraction_time = time.time() - start_time
            
            print(f"\n✓ Extracted {len(final_df)} transactions in {extraction_time:.2f} seconds")
            print("\nFinal transactions:")
            print(final_df.to_string())
            
            # Save to CSV
            output_path = f"../data/output/bpi_tabula_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            final_df.to_csv(output_path, index=False)
            print(f"\nSaved to: {output_path}")
            
            # Summary
            print(f"\nSummary:")
            print(f"Total transactions: {len(final_df)}")
            print(f"Total amount: ₱{final_df['Amount'].sum():,.2f}")
            print(f"Processing time: {extraction_time:.2f} seconds")
            
        else:
            print("No transactions found")
            
    except Exception as e:
        print(f"Error: {e}")

def process_tabula_table(df, table_index):
    """Process a tabula-extracted table to find transactions"""
    transactions = []
    
    if df.empty:
        return transactions
    
    # Look for transaction patterns in the dataframe
    for index, row in df.iterrows():
        # Convert row to list and clean
        row_data = [str(cell).strip() if pd.notna(cell) else '' for cell in row.values]
        
        # Skip empty rows
        if not any(row_data):
            continue
        
        print(f"Processing row {index}: {row_data}")
        
        # Look for date patterns in first columns
        if len(row_data) >= 4:
            # Check if first two cells look like dates
            if looks_like_date(row_data[0]) and looks_like_date(row_data[1]):
                # Find amount (last numeric cell)
                amount = None
                amount_idx = -1
                
                for i in range(len(row_data) - 1, -1, -1):
                    if looks_like_amount(row_data[i]):
                        amount = float(row_data[i].replace(',', '').replace('₱', ''))
                        amount_idx = i
                        break
                
                if amount and amount > 0:
                    # Description is everything between dates and amount
                    desc_parts = row_data[2:amount_idx]
                    description = ' '.join([part for part in desc_parts if part and part != 'nan']).strip()
                    
                    if description and len(description) > 2:
                        transaction = {
                            'Card_Type': f'TABLE_{table_index + 1}',
                            'Transaction_Date': row_data[0],
                            'Post_Date': row_data[1],
                            'Description': description,
                            'Amount': amount
                        }
                        transactions.append(transaction)
                        print(f"  -> Found transaction: {description} - {amount}")
    
    return transactions

def looks_like_date(text):
    """Check if text looks like a date"""
    import re
    if not text or text == 'nan':
        return False
    date_pattern = r'^[A-Za-z]{3,9}\s*\d{1,2}$'
    return bool(re.match(date_pattern, text.strip()))

def looks_like_amount(text):
    """Check if text looks like a monetary amount"""
    import re
    if not text or text == 'nan':
        return False
    amount_pattern = r'^\d{1,3}(?:,\d{3})*\.\d{2}$'
    clean_text = text.replace('₱', '').strip()
    return bool(re.match(amount_pattern, clean_text))

def clean_dataframe(df):
    """Clean and format the DataFrame"""
    # Convert date columns to datetime
    current_year = datetime.now().year
    
    for date_col in ['Transaction_Date', 'Post_Date']:
        if date_col in df.columns:
            df[date_col] = df[date_col].apply(lambda x: parse_date(x, current_year))
    
    # Sort by transaction date
    if 'Transaction_Date' in df.columns:
        df = df.sort_values('Transaction_Date').reset_index(drop=True)
    
    return df

def parse_date(date_str, year):
    """Parse date string to datetime object"""
    try:
        date_obj = datetime.strptime(f"{date_str} {year}", "%b %d %Y")
        return date_obj
    except ValueError:
        try:
            date_obj = datetime.strptime(f"{date_str} {year}", "%B %d %Y")
            return date_obj
        except ValueError:
            return None

if __name__ == "__main__":
    parse_bpi_with_tabula()