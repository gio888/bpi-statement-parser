import pandas as pd
import pdfplumber
from datetime import datetime
import time
import re

def parse_bpi_advanced_pdfplumber():
    print("=" * 60)
    print("BPI STATEMENT PARSER - ADVANCED PDFPLUMBER")
    print("Enhanced table detection + text parsing")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        all_transactions = []
        
        with pdfplumber.open("../data/Statement BPI Master 2025-05-12.pdf") as pdf:
            for page_num, page in enumerate(pdf.pages):
                print(f"\nProcessing page {page_num + 1}...")
                
                # Method 1: Try to extract tables
                tables = page.extract_tables()
                print(f"Found {len(tables)} table(s) on page {page_num + 1}")
                
                if tables:
                    for table_num, table in enumerate(tables):
                        print(f"\nTable {table_num + 1} on page {page_num + 1}:")
                        transactions = process_pdfplumber_table(table, f"PAGE_{page_num + 1}_TABLE_{table_num + 1}")
                        all_transactions.extend(transactions)
                
                # Method 2: Extract text and parse line by line
                text = page.extract_text()
                if text:
                    print(f"\nExtracting from text (page {page_num + 1})...")
                    text_transactions = extract_from_text(text, f"PAGE_{page_num + 1}_TEXT")
                    all_transactions.extend(text_transactions)
                
                # Method 3: Try to extract words with positions (advanced)
                print(f"\nTrying advanced word extraction (page {page_num + 1})...")
                word_transactions = extract_from_words(page, f"PAGE_{page_num + 1}_WORDS")
                all_transactions.extend(word_transactions)
        
        # Remove duplicates and finalize
        if all_transactions:
            df = pd.DataFrame(all_transactions)
            df = remove_duplicates(df)
            df = clean_dataframe(df)
            
            extraction_time = time.time() - start_time
            
            print(f"\n✓ Extracted {len(df)} unique transactions in {extraction_time:.2f} seconds")
            print("\nFinal transactions:")
            print(df.to_string())
            
            # Save to CSV
            output_path = f"../data/output/bpi_advanced_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(output_path, index=False)
            print(f"\nSaved to: {output_path}")
            
            # Summary
            print(f"\nSummary:")
            print(f"Total transactions: {len(df)}")
            print(f"Total amount: ₱{df['Amount'].sum():,.2f}")
            print(f"Processing time: {extraction_time:.2f} seconds")
            
        else:
            print("No transactions found")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def process_pdfplumber_table(table, source):
    """Process table extracted by pdfplumber"""
    transactions = []
    
    if not table:
        return transactions
    
    print(f"Table from {source}:")
    for i, row in enumerate(table):
        print(f"  Row {i}: {row}")
        
        if row and len(row) >= 4:
            # Clean row data
            clean_row = [cell.strip() if cell else '' for cell in row]
            
            # Check for transaction pattern
            if (looks_like_date(clean_row[0]) and 
                looks_like_date(clean_row[1]) and
                any(looks_like_amount(cell) for cell in clean_row[2:])):
                
                # Find amount
                amount = None
                amount_idx = -1
                
                for j in range(len(clean_row) - 1, 1, -1):
                    if looks_like_amount(clean_row[j]):
                        amount = float(clean_row[j].replace(',', '').replace('₱', ''))
                        amount_idx = j
                        break
                
                if amount and amount > 0:
                    # Description
                    desc_parts = clean_row[2:amount_idx]
                    description = ' '.join([part for part in desc_parts if part]).strip()
                    
                    if description and len(description) > 2:
                        transaction = {
                            'Source': source,
                            'Transaction_Date': clean_row[0],
                            'Post_Date': clean_row[1],
                            'Description': description,
                            'Amount': amount,
                            'Currency': 'PHP',  # Default for table extraction
                            'Foreign_Amount': None
                        }
                        transactions.append(transaction)
                        print(f"    -> Found: {description} - {amount}")
    
    return transactions

def extract_from_text(text, source):
    """Extract transactions from plain text"""
    transactions = []
    lines = text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or should_skip_line(line):
            i += 1
            continue
        
        # PHP transaction (single line)
        php_pattern = r'^([A-Za-z]{3,9})\s+(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{1,2})\s+(.+?)\s+(\d{1,3}(?:,\d{3})*\.\d{2})

def extract_from_words(page, source):
    """Extract using word-level extraction with positions"""
    transactions = []
    
    try:
        # Get words with their positions
        words = page.extract_words()
        
        # Group words by line (similar y-coordinate)
        lines = {}
        for word in words:
            y = round(word['top'])
            if y not in lines:
                lines[y] = []
            lines[y].append(word)
        
        # Sort lines by y-coordinate and process
        for y in sorted(lines.keys()):
            line_words = sorted(lines[y], key=lambda w: w['x0'])
            line_text = ' '.join([w['text'] for w in line_words])
            
            # Check if this line looks like a transaction
            if has_transaction_pattern(line_text):
                transaction = parse_word_line(line_words, source)
                if transaction:
                    transactions.append(transaction)
    
    except Exception as e:
        print(f"Word extraction failed: {e}")
    
    return transactions

def parse_word_line(words, source):
    """Parse a line of words into transaction"""
    if len(words) < 4:
        return None
    
    # Look for date-date-description-amount pattern
    dates = []
    descriptions = []
    amounts = []
    
    for word in words:
        text = word['text']
        if looks_like_date(text):
            dates.append(text)
        elif looks_like_amount(text):
            amounts.append(float(text.replace(',', '')))
        else:
            descriptions.append(text)
    
    if len(dates) >= 2 and len(amounts) >= 1 and descriptions:
        return {
            'Source': source,
            'Transaction_Date': dates[0],
            'Post_Date': dates[1],
            'Description': ' '.join(descriptions),
            'Amount': amounts[-1],  # Last amount
            'Currency': 'PHP',  # Default for word extraction
            'Foreign_Amount': None
        }
    
    return None

def has_transaction_pattern(text):
    """Check if text line has transaction pattern"""
    # Quick check for date-date-text-amount pattern
    parts = text.split()
    if len(parts) < 4:
        return False
    
    date_count = sum(1 for part in parts if looks_like_date(part))
    amount_count = sum(1 for part in parts if looks_like_amount(part))
    
    return date_count >= 2 and amount_count >= 1

def create_transaction_from_match(match, source):
    """Create transaction from regex match"""
    try:
        return {
            'Source': source,
            'Transaction_Date': f"{match.group(1)} {match.group(2)}",
            'Post_Date': f"{match.group(3)} {match.group(4)}",
            'Description': match.group(5).strip(),
            'Amount': float(match.group(6).replace(',', ''))
        }
    except (ValueError, AttributeError):
        return None

def looks_like_date(text):
    """Check if text looks like a date"""
    if not text:
        return False
    date_pattern = r'^[A-Za-z]{3,9}\s*\d{1,2}$'
    return bool(re.match(date_pattern, text.strip()))

def looks_like_amount(text):
    """Check if text looks like a monetary amount"""
    if not text:
        return False
    amount_pattern = r'^\d{1,3}(?:,\d{3})*\.\d{2}$'
    clean_text = text.replace('₱', '').strip()
    return bool(re.match(amount_pattern, clean_text))

def should_skip_line(line):
    """Check if line should be skipped"""
    skip_patterns = [
        r'Statement of Account', r'Customer Number', r'Previous Balance',
        r'Past Due', r'Ending Balance', r'Unbilled Installment',
        r'Finance Charge', r'Payment.*Thank You', r'Transaction\s+Post.*Date',
        r'BPI.*CARD', r'GIOVANNI BACAREZA'
    ]
    
    for pattern in skip_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False

def remove_duplicates(df):
    """Remove duplicate transactions"""
    # Remove exact duplicates
    df = df.drop_duplicates(subset=['Transaction_Date', 'Post_Date', 'Description', 'Amount'])
    
    # Keep only the best source (prefer table over text)
    source_priority = {'TABLE': 1, 'TEXT': 2, 'WORDS': 3}
    df['priority'] = df['Source'].apply(lambda x: min([source_priority.get(part, 9) for part in x.split('_')]))
    df = df.sort_values('priority').drop_duplicates(subset=['Transaction_Date', 'Post_Date', 'Description', 'Amount'], keep='first')
    df = df.drop('priority', axis=1)
    
    return df

def clean_dataframe(df):
    """Clean and format the DataFrame"""
    current_year = datetime.now().year
    
    for date_col in ['Transaction_Date', 'Post_Date']:
        if date_col in df.columns:
            df[date_col] = df[date_col].apply(lambda x: parse_date(x, current_year))
    
    if 'Transaction_Date' in df.columns:
        df = df.sort_values('Transaction_Date').reset_index(drop=True)
    
    return df

def parse_date(date_str, year):
    """Parse date string to datetime object"""
    try:
        return datetime.strptime(f"{date_str} {year}", "%b %d %Y")
    except ValueError:
        try:
            return datetime.strptime(f"{date_str} {year}", "%B %d %Y")
        except ValueError:
            return None

if __name__ == "__main__":
    parse_bpi_advanced_pdfplumber()
        php_match = re.match(php_pattern, line)
        
        if php_match:
            transaction = create_transaction_from_match(php_match, source)
            if transaction:
                # Add currency info for PHP transactions
                transaction['Currency'] = 'PHP'
                transaction['Foreign_Amount'] = None
                transactions.append(transaction)
            i += 1
            continue
        
        # Foreign currency (two lines)
        foreign_pattern = r'^([A-Za-z]{3,9})\s+(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{1,2})\s+(.+?)\s+(US|SG|NZ)

def extract_from_words(page, source):
    """Extract using word-level extraction with positions"""
    transactions = []
    
    try:
        # Get words with their positions
        words = page.extract_words()
        
        # Group words by line (similar y-coordinate)
        lines = {}
        for word in words:
            y = round(word['top'])
            if y not in lines:
                lines[y] = []
            lines[y].append(word)
        
        # Sort lines by y-coordinate and process
        for y in sorted(lines.keys()):
            line_words = sorted(lines[y], key=lambda w: w['x0'])
            line_text = ' '.join([w['text'] for w in line_words])
            
            # Check if this line looks like a transaction
            if has_transaction_pattern(line_text):
                transaction = parse_word_line(line_words, source)
                if transaction:
                    transactions.append(transaction)
    
    except Exception as e:
        print(f"Word extraction failed: {e}")
    
    return transactions

def parse_word_line(words, source):
    """Parse a line of words into transaction"""
    if len(words) < 4:
        return None
    
    # Look for date-date-description-amount pattern
    dates = []
    descriptions = []
    amounts = []
    
    for word in words:
        text = word['text']
        if looks_like_date(text):
            dates.append(text)
        elif looks_like_amount(text):
            amounts.append(float(text.replace(',', '')))
        else:
            descriptions.append(text)
    
    if len(dates) >= 2 and len(amounts) >= 1 and descriptions:
        return {
            'Source': source,
            'Transaction_Date': dates[0],
            'Post_Date': dates[1],
            'Description': ' '.join(descriptions),
            'Amount': amounts[-1]  # Last amount
        }
    
    return None

def has_transaction_pattern(text):
    """Check if text line has transaction pattern"""
    # Quick check for date-date-text-amount pattern
    parts = text.split()
    if len(parts) < 4:
        return False
    
    date_count = sum(1 for part in parts if looks_like_date(part))
    amount_count = sum(1 for part in parts if looks_like_amount(part))
    
    return date_count >= 2 and amount_count >= 1

def create_transaction_from_match(match, source):
    """Create transaction from regex match"""
    try:
        return {
            'Source': source,
            'Transaction_Date': f"{match.group(1)} {match.group(2)}",
            'Post_Date': f"{match.group(3)} {match.group(4)}",
            'Description': match.group(5).strip(),
            'Amount': float(match.group(6).replace(',', ''))
        }
    except (ValueError, AttributeError):
        return None

def looks_like_date(text):
    """Check if text looks like a date"""
    if not text:
        return False
    date_pattern = r'^[A-Za-z]{3,9}\s*\d{1,2}$'
    return bool(re.match(date_pattern, text.strip()))

def looks_like_amount(text):
    """Check if text looks like a monetary amount"""
    if not text:
        return False
    amount_pattern = r'^\d{1,3}(?:,\d{3})*\.\d{2}$'
    clean_text = text.replace('₱', '').strip()
    return bool(re.match(amount_pattern, clean_text))

def should_skip_line(line):
    """Check if line should be skipped"""
    skip_patterns = [
        r'Statement of Account', r'Customer Number', r'Previous Balance',
        r'Past Due', r'Ending Balance', r'Unbilled Installment',
        r'Finance Charge', r'Payment.*Thank You', r'Transaction\s+Post.*Date',
        r'BPI.*CARD', r'GIOVANNI BACAREZA'
    ]
    
    for pattern in skip_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False

def remove_duplicates(df):
    """Remove duplicate transactions"""
    # Remove exact duplicates
    df = df.drop_duplicates(subset=['Transaction_Date', 'Post_Date', 'Description', 'Amount'])
    
    # Keep only the best source (prefer table over text)
    source_priority = {'TABLE': 1, 'TEXT': 2, 'WORDS': 3}
    df['priority'] = df['Source'].apply(lambda x: min([source_priority.get(part, 9) for part in x.split('_')]))
    df = df.sort_values('priority').drop_duplicates(subset=['Transaction_Date', 'Post_Date', 'Description', 'Amount'], keep='first')
    df = df.drop('priority', axis=1)
    
    return df

def clean_dataframe(df):
    """Clean and format the DataFrame"""
    current_year = datetime.now().year
    
    for date_col in ['Transaction_Date', 'Post_Date']:
        if date_col in df.columns:
            df[date_col] = df[date_col].apply(lambda x: parse_date(x, current_year))
    
    if 'Transaction_Date' in df.columns:
        df = df.sort_values('Transaction_Date').reset_index(drop=True)
    
    return df

def parse_date(date_str, year):
    """Parse date string to datetime object"""
    try:
        return datetime.strptime(f"{date_str} {year}", "%b %d %Y")
    except ValueError:
        try:
            return datetime.strptime(f"{date_str} {year}", "%B %d %Y")
        except ValueError:
            return None

if __name__ == "__main__":
    parse_bpi_advanced_pdfplumber()
        foreign_match = re.match(foreign_pattern, line)
        
        if foreign_match and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            currency_pattern = r'U\.S\.\s+Dollar\s+([\d.,]+)\s+(\d{1,3}(?:,\d{3})*\.\d{2})

def extract_from_words(page, source):
    """Extract using word-level extraction with positions"""
    transactions = []
    
    try:
        # Get words with their positions
        words = page.extract_words()
        
        # Group words by line (similar y-coordinate)
        lines = {}
        for word in words:
            y = round(word['top'])
            if y not in lines:
                lines[y] = []
            lines[y].append(word)
        
        # Sort lines by y-coordinate and process
        for y in sorted(lines.keys()):
            line_words = sorted(lines[y], key=lambda w: w['x0'])
            line_text = ' '.join([w['text'] for w in line_words])
            
            # Check if this line looks like a transaction
            if has_transaction_pattern(line_text):
                transaction = parse_word_line(line_words, source)
                if transaction:
                    transactions.append(transaction)
    
    except Exception as e:
        print(f"Word extraction failed: {e}")
    
    return transactions

def parse_word_line(words, source):
    """Parse a line of words into transaction"""
    if len(words) < 4:
        return None
    
    # Look for date-date-description-amount pattern
    dates = []
    descriptions = []
    amounts = []
    
    for word in words:
        text = word['text']
        if looks_like_date(text):
            dates.append(text)
        elif looks_like_amount(text):
            amounts.append(float(text.replace(',', '')))
        else:
            descriptions.append(text)
    
    if len(dates) >= 2 and len(amounts) >= 1 and descriptions:
        return {
            'Source': source,
            'Transaction_Date': dates[0],
            'Post_Date': dates[1],
            'Description': ' '.join(descriptions),
            'Amount': amounts[-1]  # Last amount
        }
    
    return None

def has_transaction_pattern(text):
    """Check if text line has transaction pattern"""
    # Quick check for date-date-text-amount pattern
    parts = text.split()
    if len(parts) < 4:
        return False
    
    date_count = sum(1 for part in parts if looks_like_date(part))
    amount_count = sum(1 for part in parts if looks_like_amount(part))
    
    return date_count >= 2 and amount_count >= 1

def create_transaction_from_match(match, source):
    """Create transaction from regex match"""
    try:
        return {
            'Source': source,
            'Transaction_Date': f"{match.group(1)} {match.group(2)}",
            'Post_Date': f"{match.group(3)} {match.group(4)}",
            'Description': match.group(5).strip(),
            'Amount': float(match.group(6).replace(',', ''))
        }
    except (ValueError, AttributeError):
        return None

def looks_like_date(text):
    """Check if text looks like a date"""
    if not text:
        return False
    date_pattern = r'^[A-Za-z]{3,9}\s*\d{1,2}$'
    return bool(re.match(date_pattern, text.strip()))

def looks_like_amount(text):
    """Check if text looks like a monetary amount"""
    if not text:
        return False
    amount_pattern = r'^\d{1,3}(?:,\d{3})*\.\d{2}$'
    clean_text = text.replace('₱', '').strip()
    return bool(re.match(amount_pattern, clean_text))

def should_skip_line(line):
    """Check if line should be skipped"""
    skip_patterns = [
        r'Statement of Account', r'Customer Number', r'Previous Balance',
        r'Past Due', r'Ending Balance', r'Unbilled Installment',
        r'Finance Charge', r'Payment.*Thank You', r'Transaction\s+Post.*Date',
        r'BPI.*CARD', r'GIOVANNI BACAREZA'
    ]
    
    for pattern in skip_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False

def remove_duplicates(df):
    """Remove duplicate transactions"""
    # Remove exact duplicates
    df = df.drop_duplicates(subset=['Transaction_Date', 'Post_Date', 'Description', 'Amount'])
    
    # Keep only the best source (prefer table over text)
    source_priority = {'TABLE': 1, 'TEXT': 2, 'WORDS': 3}
    df['priority'] = df['Source'].apply(lambda x: min([source_priority.get(part, 9) for part in x.split('_')]))
    df = df.sort_values('priority').drop_duplicates(subset=['Transaction_Date', 'Post_Date', 'Description', 'Amount'], keep='first')
    df = df.drop('priority', axis=1)
    
    return df

def clean_dataframe(df):
    """Clean and format the DataFrame"""
    current_year = datetime.now().year
    
    for date_col in ['Transaction_Date', 'Post_Date']:
        if date_col in df.columns:
            df[date_col] = df[date_col].apply(lambda x: parse_date(x, current_year))
    
    if 'Transaction_Date' in df.columns:
        df = df.sort_values('Transaction_Date').reset_index(drop=True)
    
    return df

def parse_date(date_str, year):
    """Parse date string to datetime object"""
    try:
        return datetime.strptime(f"{date_str} {year}", "%b %d %Y")
    except ValueError:
        try:
            return datetime.strptime(f"{date_str} {year}", "%B %d %Y")
        except ValueError:
            return None

if __name__ == "__main__":
    parse_bpi_advanced_pdfplumber()
            currency_match = re.search(currency_pattern, next_line)
            
            if currency_match:
                # Determine currency based on country code
                country_code = foreign_match.group(6)
                currency = 'USD' if country_code == 'US' else ('SGD' if country_code == 'SG' else 'NZD')
                
                foreign_amount = float(currency_match.group(1).replace(',', ''))
                php_amount = float(currency_match.group(2).replace(',', ''))
                
                transaction = {
                    'Source': source,
                    'Transaction_Date': f"{foreign_match.group(1)} {foreign_match.group(2)}",
                    'Post_Date': f"{foreign_match.group(3)} {foreign_match.group(4)}",
                    'Description': foreign_match.group(5).strip(),
                    'Amount': php_amount,
                    'Currency': currency,
                    'Foreign_Amount': foreign_amount
                }
                transactions.append(transaction)
                i += 2
                continue
        
        i += 1
    
    return transactions

def extract_from_words(page, source):
    """Extract using word-level extraction with positions"""
    transactions = []
    
    try:
        # Get words with their positions
        words = page.extract_words()
        
        # Group words by line (similar y-coordinate)
        lines = {}
        for word in words:
            y = round(word['top'])
            if y not in lines:
                lines[y] = []
            lines[y].append(word)
        
        # Sort lines by y-coordinate and process
        for y in sorted(lines.keys()):
            line_words = sorted(lines[y], key=lambda w: w['x0'])
            line_text = ' '.join([w['text'] for w in line_words])
            
            # Check if this line looks like a transaction
            if has_transaction_pattern(line_text):
                transaction = parse_word_line(line_words, source)
                if transaction:
                    transactions.append(transaction)
    
    except Exception as e:
        print(f"Word extraction failed: {e}")
    
    return transactions

def parse_word_line(words, source):
    """Parse a line of words into transaction"""
    if len(words) < 4:
        return None
    
    # Look for date-date-description-amount pattern
    dates = []
    descriptions = []
    amounts = []
    
    for word in words:
        text = word['text']
        if looks_like_date(text):
            dates.append(text)
        elif looks_like_amount(text):
            amounts.append(float(text.replace(',', '')))
        else:
            descriptions.append(text)
    
    if len(dates) >= 2 and len(amounts) >= 1 and descriptions:
        return {
            'Source': source,
            'Transaction_Date': dates[0],
            'Post_Date': dates[1],
            'Description': ' '.join(descriptions),
            'Amount': amounts[-1]  # Last amount
        }
    
    return None

def has_transaction_pattern(text):
    """Check if text line has transaction pattern"""
    # Quick check for date-date-text-amount pattern
    parts = text.split()
    if len(parts) < 4:
        return False
    
    date_count = sum(1 for part in parts if looks_like_date(part))
    amount_count = sum(1 for part in parts if looks_like_amount(part))
    
    return date_count >= 2 and amount_count >= 1

def create_transaction_from_match(match, source):
    """Create transaction from regex match"""
    try:
        return {
            'Source': source,
            'Transaction_Date': f"{match.group(1)} {match.group(2)}",
            'Post_Date': f"{match.group(3)} {match.group(4)}",
            'Description': match.group(5).strip(),
            'Amount': float(match.group(6).replace(',', ''))
        }
    except (ValueError, AttributeError):
        return None

def looks_like_date(text):
    """Check if text looks like a date"""
    if not text:
        return False
    date_pattern = r'^[A-Za-z]{3,9}\s*\d{1,2}$'
    return bool(re.match(date_pattern, text.strip()))

def looks_like_amount(text):
    """Check if text looks like a monetary amount"""
    if not text:
        return False
    amount_pattern = r'^\d{1,3}(?:,\d{3})*\.\d{2}$'
    clean_text = text.replace('₱', '').strip()
    return bool(re.match(amount_pattern, clean_text))

def should_skip_line(line):
    """Check if line should be skipped"""
    skip_patterns = [
        r'Statement of Account', r'Customer Number', r'Previous Balance',
        r'Past Due', r'Ending Balance', r'Unbilled Installment',
        r'Finance Charge', r'Payment.*Thank You', r'Transaction\s+Post.*Date',
        r'BPI.*CARD', r'GIOVANNI BACAREZA'
    ]
    
    for pattern in skip_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False

def remove_duplicates(df):
    """Remove duplicate transactions"""
    # Remove exact duplicates
    df = df.drop_duplicates(subset=['Transaction_Date', 'Post_Date', 'Description', 'Amount'])
    
    # Keep only the best source (prefer table over text)
    source_priority = {'TABLE': 1, 'TEXT': 2, 'WORDS': 3}
    df['priority'] = df['Source'].apply(lambda x: min([source_priority.get(part, 9) for part in x.split('_')]))
    df = df.sort_values('priority').drop_duplicates(subset=['Transaction_Date', 'Post_Date', 'Description', 'Amount'], keep='first')
    df = df.drop('priority', axis=1)
    
    return df

def clean_dataframe(df):
    """Clean and format the DataFrame"""
    current_year = datetime.now().year
    
    for date_col in ['Transaction_Date', 'Post_Date']:
        if date_col in df.columns:
            df[date_col] = df[date_col].apply(lambda x: parse_date(x, current_year))
    
    if 'Transaction_Date' in df.columns:
        df = df.sort_values('Transaction_Date').reset_index(drop=True)
    
    return df

def parse_date(date_str, year):
    """Parse date string to datetime object"""
    try:
        return datetime.strptime(f"{date_str} {year}", "%b %d %Y")
    except ValueError:
        try:
            return datetime.strptime(f"{date_str} {year}", "%B %d %Y")
        except ValueError:
            return None

if __name__ == "__main__":
    parse_bpi_advanced_pdfplumber()