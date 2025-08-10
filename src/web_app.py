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
import pandas as pd

app = Flask(__name__, static_folder='../static', static_url_path='/static')
CORS(app, origins=['http://localhost:8080', 'http://127.0.0.1:8080'])

# Configuration
UPLOAD_FOLDER = tempfile.mkdtemp(prefix='bpi_upload_')
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

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
            
            # Save main CSV
            timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
            main_filename = f"For Import Statement BPI Master Batch {timestamp}.csv"
            main_csv_path = os.path.join(process_folder, main_filename)
            df_clean.to_csv(main_csv_path, index=False)
            
            # Run finalization to create the 4 output files
            finalization_result = finalize_statement_csv(main_csv_path, statement_dates)
            
            # Collect all output files
            if finalization_result:
                output_files.append({
                    'name': main_filename,
                    'path': main_csv_path,
                    'type': 'main'
                })
                
                # Add card-specific files
                for csv_path in finalization_result.get('card_csvs', []):
                    if os.path.exists(csv_path):
                        output_files.append({
                            'name': os.path.basename(csv_path),
                            'path': csv_path,
                            'type': 'card'
                        })
        
        # Prepare response
        response_data = {
            'success': len(results) > 0,
            'processed': len(results),
            'errors': errors,
            'total_transactions': len(all_transactions),
            'results': results,
            'output_files': output_files,
            'process_id': process_id
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
        
        # Parse transactions
        parser = TransactionParser()
        card_transactions = parser.parse_transactions(text)
        
        # Extract statement date
        statement_date = None
        for line in text.split('\n'):
            if 'Statement Date:' in line:
                date_str = line.split('Statement Date:')[1].strip()
                try:
                    statement_date = pd.to_datetime(date_str).strftime('%Y-%m-%d')
                except:
                    pass
                break
        
        # Flatten transactions
        all_transactions = []
        for card_name, transactions in card_transactions.items():
            for trans in transactions:
                trans['Card'] = card_name
                if statement_date:
                    trans['Statement Date'] = statement_date
                all_transactions.append(trans)
        
        return {
            'success': True,
            'filename': filename,
            'transactions': all_transactions,
            'transaction_count': len(all_transactions),
            'cards': list(card_transactions.keys()),
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