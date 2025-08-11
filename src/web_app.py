"""
BPI Statement Parser - Web Application
Flask backend for web interface
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
import zipfile
import io

# Import existing processing modules
import sys
# Add both parent and src directory to path for flexible imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try both import methods for compatibility
try:
    from pdf_extractor import PDFExtractor
    from transaction_parser import TransactionParser
    from currency_handler import CurrencyHandler
    from statement_finalizer import finalize_statement_csv
    from batch_processor import BatchStatementProcessor
    from config_loader import get_config
except ImportError:
    from src.pdf_extractor import PDFExtractor
    from src.transaction_parser import TransactionParser
    from src.currency_handler import CurrencyHandler
    from src.statement_finalizer import finalize_statement_csv
    from src.batch_processor import BatchStatementProcessor
    from src.config_loader import get_config
from account_mapper import AccountMapper
import pandas as pd

def create_accounting_format(df, corrections_dict=None):
    """
    Convert transaction dataframe to double-entry accounting format
    
    Args:
        df: Original transaction dataframe (with capitalized columns)
        corrections_dict: Dict of corrections {transaction_id: new_account}
    
    Returns:
        DataFrame with accounting format columns
    """
    accounting_df = pd.DataFrame()
    
    # Basic columns (using capitalized column names)
    accounting_df['Date'] = df.get('Transaction Date', df.get('Date', ''))
    accounting_df['Description'] = df.get('Description', '')
    
    # Double-entry amount logic
    original_amounts = pd.to_numeric(df.get('Amount', 0), errors='coerce').fillna(0)
    
    accounting_df['Amount (Negated)'] = original_amounts.apply(lambda x: x if x > 0 else 0)
    accounting_df['Amount'] = original_amounts.apply(lambda x: 0 if x > 0 else abs(x))
    
    # Account column (original card account from Card column)
    accounting_df['Account'] = df.get('Card', 'BPI Card').apply(
        lambda card: f"Liabilities:Credit Card:BPI Mastercard:{card}" if card != 'BPI Card' else 'Liabilities:Credit Card:BPI Mastercard'
    )
    
    # Target Account (corrected classification)
    target_accounts = []
    for idx, row in df.iterrows():
        if corrections_dict and idx in corrections_dict:
            # Use user correction
            target_accounts.append(corrections_dict[idx])
        else:
            # Use original AI prediction (already in Target Account column)
            target_accounts.append(row['Target Account'])
    
    accounting_df['Target Account'] = target_accounts
    
    return accounting_df

app = Flask(__name__, static_folder='../static', static_url_path='/static')
CORS(app, origins=['http://localhost:8080', 'http://127.0.0.1:8080'])

# Configuration
UPLOAD_FOLDER = tempfile.mkdtemp(prefix='bpi_upload_')
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Global storage for review sessions
review_sessions = {}

def allowed_file(filename):
    """Check if file is allowed PDF"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_pdf(file_path):
    """Validate that file is actually a PDF"""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
            return header == b'%PDF'
    except:
        return False

@app.route('/')
def index():
    """Serve the main web interface"""
    return app.send_static_file('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'version': '1.0.0'})

@app.route('/api/upload', methods=['POST'])
def upload_and_process():
    """Handle PDF upload and processing"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    # Process each uploaded file
    results = []
    all_transactions = []
    statement_dates = []
    errors = []
    
    # Create temporary processing folder
    process_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    process_folder = os.path.join(app.config['UPLOAD_FOLDER'], process_id)
    os.makedirs(process_folder, exist_ok=True)
    
    try:
        for file in files:
            if file and allowed_file(file.filename):
                # Save uploaded file
                filename = secure_filename(file.filename)
                filepath = os.path.join(process_folder, filename)
                file.save(filepath)
                
                # Validate PDF
                if not validate_pdf(filepath):
                    errors.append({
                        'file': filename,
                        'error': 'Invalid PDF file'
                    })
                    continue
                
                # Process the PDF
                try:
                    result = process_single_pdf(filepath, filename)
                    results.append(result)
                    
                    # Collect transactions for batch output
                    if result['success'] and result['transactions']:
                        all_transactions.extend(result['transactions'])
                        if result.get('statement_date'):
                            statement_dates.append(result['statement_date'])
                        
                except Exception as e:
                    errors.append({
                        'file': filename,
                        'error': str(e)
                    })
        
        # If we have transactions, create the combined output files
        output_files = []
        review_data = None
        
        if all_transactions:
            # Create DataFrame from all transactions
            df = pd.DataFrame(all_transactions)
            
            # Clean and process with currency handler
            currency_handler = CurrencyHandler()
            # Use the year from the first statement date if available
            statement_year = datetime.now().year
            if statement_dates:
                statement_year = pd.to_datetime(statement_dates[0]).year
            df_clean = currency_handler.clean_dataframe(df, statement_year)
            
            # Apply account mapping with confidence scores for review
            try:
                config = get_config()
                accounts_csv_path = config.get('ACCOUNTS_CSV_PATH')
                if not accounts_csv_path:
                    raise ValueError("ACCOUNTS_CSV_PATH not configured")
            except Exception as e:
                print(f"Config error: {e}")
                accounts_csv_path = os.path.join('data', 'input', 'Accounts List 2024-07.csv')
            
            mapper = AccountMapper(accounts_csv_path)
            
            # Generate mapping data for review interface
            review_transactions = []
            ai_predictions = []
            
            for index, row in df_clean.iterrows():
                description = row.get('Description', '')
                mapping_data = mapper.get_mapping_with_metadata(description)
                
                ai_predictions.append(mapping_data['account'])
                
                review_transactions.append({
                    'id': index,
                    'date': row.get('Transaction Date', ''),
                    'description': description,
                    'amount': row.get('Amount', 0),
                    'card': row.get('Card', ''),
                    'current_account': mapping_data['account'],
                    'confidence': mapping_data['confidence'],
                    'source': mapping_data['source'],
                    'alternatives': mapping_data['alternatives'],
                    'pattern_matched': mapping_data['pattern_matched']
                })
            
            # Add Target Account column to dataframe with AI predictions
            df_clean['Target Account'] = ai_predictions
            
            # Store review session data
            review_data = {
                'transactions': review_transactions,
                'valid_accounts': mapper.get_all_valid_accounts(),
                'total_transactions': len(review_transactions),
                'high_confidence': len([t for t in review_transactions if t['confidence'] >= 70]),
                'medium_confidence': len([t for t in review_transactions if 50 <= t['confidence'] < 70]),
                'low_confidence': len([t for t in review_transactions if t['confidence'] < 50]),
                'original_df': df_clean,
                'process_folder': process_folder,
                'statement_dates': statement_dates
            }
            
            # Store review session
            review_sessions[process_id] = review_data
            
            # Save main CSV with new naming convention (without finalization initially)
            # Use statement date if available, otherwise current date
            if statement_dates:
                date_str = statement_dates[0]  # Use first statement date
            else:
                date_str = datetime.now().strftime("%Y-%m-%d")
            main_filename = f"{date_str}_Statement_BPI_Mastercard_Batch.csv"
            main_csv_path = os.path.join(process_folder, main_filename)
            df_clean.to_csv(main_csv_path, index=False)
            
            # Store main file info but don't run finalization yet (wait for review)
            output_files.append({
                'name': main_filename,
                'path': main_csv_path,
                'type': 'main'
            })
        
        # Prepare response
        # Consider it successful if we processed files without fatal errors,
        # even if no transactions were found
        files_processed = len([r for r in results if r.get('success', False)])
        
        response_data = {
            'success': files_processed > 0 or len(errors) == 0,
            'processed': files_processed,
            'errors': errors,
            'total_transactions': len(all_transactions),
            'results': results,
            'output_files': output_files,
            'process_id': process_id,
            'has_review_data': review_data is not None,
            'review_summary': {
                'total_transactions': review_data['total_transactions'] if review_data else 0,
                'high_confidence': review_data['high_confidence'] if review_data else 0,
                'medium_confidence': review_data['medium_confidence'] if review_data else 0,
                'low_confidence': review_data['low_confidence'] if review_data else 0
            } if review_data else None
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

def process_single_pdf(filepath, filename):
    """Process a single PDF file"""
    try:
        # Extract text from PDF
        extractor = PDFExtractor(filepath)
        text = extractor.extract_text()
        
        # Extract statement date first (needed for year context)
        statement_date = None
        statement_year = None
        import re
        for line in text.split('\n'):
            # Look for "STATEMENT DATE JULY13,2025" format (case insensitive)
            if 'STATEMENT DATE' in line.upper():
                try:
                    # Extract date part after "STATEMENT DATE"
                    date_part = line.upper().split('STATEMENT DATE')[1].strip()
                    # Parse formats like "JULY13,2025" or "JULY 13, 2025"
                    match = re.match(r'([A-Z]+)\s*(\d{1,2}),\s*(\d{4})', date_part)
                    if match:
                        month_name, day, year = match.groups()
                        # Convert to standard format
                        from datetime import datetime
                        month_num = datetime.strptime(month_name, '%B').month
                        statement_date = f"{year}-{month_num:02d}-{int(day):02d}"
                        statement_year = int(year)
                        break
                except Exception as e:
                    print(f"Warning: Could not parse statement date from: {line}")
                    continue
        
        # Parse transactions with statement year for proper date context
        parser = TransactionParser()
        all_transactions = parser.parse_transactions(text, statement_year)
        
        # Add statement date to transactions if found
        if statement_date and all_transactions:
            for trans in all_transactions:
                trans['Statement Date'] = statement_date
        
        # Extract unique card names from transactions (check both 'Card' and 'card' keys)
        cards = []
        if all_transactions:
            card_names = set()
            for trans in all_transactions:
                card_name = trans.get('Card') or trans.get('card') or 'Unknown'
                card_names.add(card_name)
            cards = list(card_names)
        
        return {
            'success': True,
            'filename': filename,
            'transactions': all_transactions,
            'transaction_count': len(all_transactions),
            'cards': cards,
            'statement_date': statement_date
        }
        
    except Exception as e:
        return {
            'success': False,
            'filename': filename,
            'error': str(e),
            'transactions': [],
            'transaction_count': 0
        }

@app.route('/api/review/<process_id>', methods=['GET'])
def get_review_data(process_id):
    """Get review data for a process"""
    try:
        if process_id not in review_sessions:
            return jsonify({'error': 'Review data not found'}), 404
        
        review_data = review_sessions[process_id]
        
        return jsonify({
            'success': True,
            'transactions': review_data['transactions'],
            'valid_accounts': review_data['valid_accounts'],
            'total_transactions': review_data['total_transactions'],
            'high_confidence': review_data['high_confidence'],
            'medium_confidence': review_data['medium_confidence'],
            'low_confidence': review_data['low_confidence']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/review/<process_id>/corrections', methods=['POST'])
def save_corrections(process_id):
    """Save corrections and generate final files"""
    try:
        if process_id not in review_sessions:
            return jsonify({'error': 'Review session not found'}), 404
        
        corrections = request.get_json()
        if not corrections or 'corrections' not in corrections:
            return jsonify({'error': 'No corrections provided'}), 400
        
        review_data = review_sessions[process_id]
        df = review_data['original_df'].copy()
        
        # Build corrections dictionary
        corrections_dict = {}
        corrections_applied = 0
        
        for correction in corrections['corrections']:
            transaction_id = correction.get('id')
            new_account = correction.get('account')
            
            if transaction_id is not None and new_account and transaction_id < len(df):
                corrections_dict[transaction_id] = new_account
                corrections_applied += 1
        
        # Apply corrections to original dataframe for any intermediate processing
        for transaction_id, new_account in corrections_dict.items():
            df.loc[transaction_id, 'Target Account'] = new_account
        
        # Create accounting format dataframe
        accounting_df = create_accounting_format(df, corrections_dict)
        
        # Save corrected CSV in accounting format
        process_folder = review_data['process_folder']
        statement_dates = review_data['statement_dates']
        
        # Use statement date if available, otherwise current date
        if statement_dates:
            date_str = statement_dates[0]
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        corrected_filename = f"{date_str}_Statement_BPI_Mastercard_Corrected.csv"
        corrected_path = os.path.join(process_folder, corrected_filename)
        
        # Save in accounting format (5 columns)
        accounting_df.to_csv(corrected_path, index=False)
        
        # Only return the corrected file - no finalization needed
        output_files = [{
            'name': corrected_filename,
            'path': corrected_path,
            'type': 'corrected'
        }]
        
        # Update review session with final files
        review_sessions[process_id]['output_files'] = output_files
        review_sessions[process_id]['corrections_applied'] = corrections_applied
        
        return jsonify({
            'success': True,
            'message': f'Applied {corrections_applied} corrections',
            'corrections_applied': corrections_applied,
            'output_files': output_files
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all valid account categories"""
    try:
        # Load account mapper to get categories
        try:
            config = get_config()
            accounts_csv_path = config.get('ACCOUNTS_CSV_PATH')
            if not accounts_csv_path:
                raise ValueError("ACCOUNTS_CSV_PATH not configured")
        except Exception as e:
            print(f"Config error: {e}")
            accounts_csv_path = os.path.join('data', 'input', 'Accounts List 2024-07.csv')
        
        mapper = AccountMapper(accounts_csv_path)
        categories = mapper.get_all_valid_accounts()
        
        return jsonify({
            'success': True,
            'categories': categories,
            'count': len(categories)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<process_id>/<filename>', methods=['GET'])
def download_file(process_id, filename):
    """Download a processed file"""
    try:
        # Security: validate process_id format
        if not process_id.replace('_', '').isdigit():
            return jsonify({'error': 'Invalid process ID'}), 400
        
        # Build file path
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], process_id, filename)
        
        # Security: ensure file is within upload folder
        if not os.path.abspath(file_path).startswith(os.path.abspath(app.config['UPLOAD_FOLDER'])):
            return jsonify({'error': 'Invalid file path'}), 403
        
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({'error': 'File not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-all/<process_id>', methods=['GET'])
def download_all(process_id):
    """Download all files as ZIP"""
    try:
        # Security: validate process_id format
        if not process_id.replace('_', '').isdigit():
            return jsonify({'error': 'Invalid process ID'}), 400
        
        process_folder = os.path.join(app.config['UPLOAD_FOLDER'], process_id)
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add all CSV files to ZIP
            for root, dirs, files in os.walk(process_folder):
                for file in files:
                    if file.endswith('.csv'):
                        file_path = os.path.join(root, file)
                        # Add to ZIP with just the filename (no path)
                        zip_file.write(file_path, file)
        
        zip_buffer.seek(0)
        
        # Send ZIP file
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'bpi_statements_{process_id}.zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cleanup/<process_id>', methods=['DELETE'])
def cleanup_process(process_id):
    """Clean up temporary files for a process"""
    try:
        # Security: validate process_id format
        if not process_id.replace('_', '').isdigit():
            return jsonify({'error': 'Invalid process ID'}), 400
        
        process_folder = os.path.join(app.config['UPLOAD_FOLDER'], process_id)
        
        if os.path.exists(process_folder):
            shutil.rmtree(process_folder)
            return jsonify({'success': True, 'message': 'Files cleaned up'})
        else:
            return jsonify({'success': False, 'message': 'Process folder not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def cleanup_old_files():
    """Clean up old temporary files (older than 1 hour)"""
    import time
    current_time = time.time()
    
    for folder in os.listdir(app.config['UPLOAD_FOLDER']):
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        if os.path.isdir(folder_path):
            # Check folder age
            folder_time = os.path.getctime(folder_path)
            if current_time - folder_time > 3600:  # 1 hour
                try:
                    shutil.rmtree(folder_path)
                except:
                    pass

if __name__ == '__main__':
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Clean up old files on startup
    cleanup_old_files()
    
    # Run the app (localhost only for security)
    print("\n" + "="*60)
    print("🌐 BPI Statement Parser Web Interface")
    print("="*60)
    print(f"Server running at: http://localhost:8080")
    print("Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    app.run(host='127.0.0.1', port=8080, debug=False)