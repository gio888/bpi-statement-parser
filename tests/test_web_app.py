"""
Unit tests for web_app Flask endpoints
"""

import unittest
import tempfile
import os
import sys
import json
import io
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestWebApp(unittest.TestCase):
    """Test cases for Flask web application"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Import Flask app
        from src.web_app import app
        
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
        
        self.app = app
        self.client = app.test_client()
        self.temp_dir = app.config['UPLOAD_FOLDER']
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_health_check_endpoint(self):
        """Test that health check endpoint returns 200"""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('version', data)
    
    def test_index_page_loads(self):
        """Test that index page loads successfully"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_upload_no_files(self):
        """Test upload endpoint with no files"""
        response = self.client.post('/api/upload')
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'No files provided')
    
    def test_upload_invalid_file_type(self):
        """Test upload with non-PDF file"""
        data = {
            'files': (io.BytesIO(b"test content"), 'test.txt')
        }
        response = self.client.post('/api/upload', 
                                   data=data,
                                   content_type='multipart/form-data')
        
        # Should process but find no valid PDFs
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['processed'], 0)
    
    def test_upload_fake_pdf(self):
        """Test upload with fake PDF (wrong header)"""
        # Create a file that claims to be PDF but isn't
        fake_pdf_content = b"Not a real PDF"
        data = {
            'files': (io.BytesIO(fake_pdf_content), 'fake.pdf')
        }
        
        response = self.client.post('/api/upload',
                                   data=data,
                                   content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        
        # Should have an error about invalid PDF
        self.assertTrue(len(result['errors']) > 0)
        self.assertEqual(result['errors'][0]['error'], 'Invalid PDF file')
    
    def test_upload_valid_pdf_header(self):
        """Test upload with valid PDF header (minimal test)"""
        # Create a minimal valid PDF header
        pdf_content = b"%PDF-1.4\n"  # Valid PDF header
        data = {
            'files': (io.BytesIO(pdf_content), 'valid.pdf')
        }
        
        response = self.client.post('/api/upload',
                                   data=data,
                                   content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        
        # Will fail to parse but should recognize as PDF
        self.assertIn('process_id', result)
    
    def test_download_invalid_process_id(self):
        """Test download with invalid process ID"""
        response = self.client.get('/api/download/invalid-id/file.csv')
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Invalid process ID')
    
    def test_download_nonexistent_file(self):
        """Test download with valid process ID but missing file"""
        response = self.client.get('/api/download/20240101_120000/nonexistent.csv')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'File not found')
    
    def test_download_path_traversal_attempt(self):
        """Test that path traversal attempts are blocked"""
        # Try to access parent directory
        response = self.client.get('/api/download/20240101_120000/../../../etc/passwd')
        self.assertEqual(response.status_code, 400)
    
    def test_cleanup_invalid_process_id(self):
        """Test cleanup with invalid process ID"""
        response = self.client.delete('/api/cleanup/invalid-id')
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Invalid process ID')
    
    def test_cleanup_nonexistent_process(self):
        """Test cleanup with valid but nonexistent process ID"""
        response = self.client.delete('/api/cleanup/20240101_120000')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Process folder not found')
    
    def test_cleanup_existing_process(self):
        """Test cleanup with existing process folder"""
        # Create a test process folder
        process_id = '20240101_120000'
        process_folder = os.path.join(self.temp_dir, process_id)
        os.makedirs(process_folder)
        
        # Create a test file in it
        test_file = os.path.join(process_folder, 'test.csv')
        with open(test_file, 'w') as f:
            f.write('test,data\n')
        
        # Cleanup should work
        response = self.client.delete(f'/api/cleanup/{process_id}')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Folder should be gone
        self.assertFalse(os.path.exists(process_folder))
    
    def test_download_all_invalid_process(self):
        """Test download all with invalid process ID"""
        response = self.client.get('/api/download-all/invalid-id')
        self.assertEqual(response.status_code, 400)
    
    def test_cors_headers(self):
        """Test that CORS headers are properly set"""
        response = self.client.get('/api/health')
        
        # Check for CORS headers
        self.assertIn('Access-Control-Allow-Origin', response.headers)

class TestWebAppHelpers(unittest.TestCase):
    """Test helper functions in web_app"""
    
    def test_allowed_file(self):
        """Test allowed_file function"""
        from src.web_app import allowed_file
        
        self.assertTrue(allowed_file('test.pdf'))
        self.assertTrue(allowed_file('test.PDF'))
        self.assertTrue(allowed_file('my.file.pdf'))
        self.assertFalse(allowed_file('test.txt'))
        self.assertFalse(allowed_file('test'))
        self.assertFalse(allowed_file(''))
    
    def test_validate_pdf(self):
        """Test PDF validation function"""
        from src.web_app import validate_pdf
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Valid PDF header
            f.write(b'%PDF-1.4')
            valid_pdf = f.name
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Invalid file
            f.write(b'Not a PDF')
            invalid_pdf = f.name
        
        try:
            self.assertTrue(validate_pdf(valid_pdf))
            self.assertFalse(validate_pdf(invalid_pdf))
            self.assertFalse(validate_pdf('/nonexistent/file.pdf'))
        finally:
            os.unlink(valid_pdf)
            os.unlink(invalid_pdf)

if __name__ == '__main__':
    unittest.main()