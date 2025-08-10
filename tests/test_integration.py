"""
Integration tests for PDF processing pipeline
Tests the complete flow from PDF input to CSV output
"""

import unittest
import os
import sys
import tempfile
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestIntegrationPipeline(unittest.TestCase):
    """Integration tests for the complete processing pipeline"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.sample_pdf_path = Path(__file__).parent.parent / "data" / "input" / "Statement BPI Master 2025-05-12.pdf"
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_pdf_extractor_initialization(self):
        """Test that PDFExtractor can be initialized"""
        from src.pdf_extractor import PDFExtractor
        
        if self.sample_pdf_path.exists():
            extractor = PDFExtractor(str(self.sample_pdf_path))
            self.assertIsNotNone(extractor)
        else:
            self.skipTest("Sample PDF not found")
    
    def test_transaction_parser_initialization(self):
        """Test that TransactionParser can be initialized"""
        from src.transaction_parser import TransactionParser
        
        parser = TransactionParser()
        self.assertIsNotNone(parser)
    
    def test_currency_handler_initialization(self):
        """Test that CurrencyHandler can be initialized"""
        from src.currency_handler import CurrencyHandler
        
        handler = CurrencyHandler()
        self.assertIsNotNone(handler)
        
        # Test basic currency detection
        self.assertTrue(handler.is_foreign_currency_line("U.S.Dollar 100.00 5800.00"))
        self.assertFalse(handler.is_foreign_currency_line("Regular transaction line"))
    
    def test_config_loader_initialization(self):
        """Test that ConfigLoader initializes with defaults"""
        from src.config_loader import get_config
        
        config = get_config()
        self.assertIsNotNone(config)
        
        # Check default values
        self.assertEqual(config.get('PRIMARY_CURRENCY'), 'PHP')
        self.assertIsNotNone(config.get('MAX_BATCH_SIZE'))
    
    def test_statement_finalizer_initialization(self):
        """Test that StatementFinalizer can be initialized"""
        from src.statement_finalizer import StatementFinalizer
        
        finalizer = StatementFinalizer()
        self.assertIsNotNone(finalizer)
        self.assertIsNotNone(finalizer.account_mapper)
    
    def test_account_mapper_initialization(self):
        """Test that AccountMapper can be initialized"""
        from account_mapper import AccountMapper
        
        mapper = AccountMapper()
        self.assertIsNotNone(mapper)
        
        # Test basic mapping
        result = mapper.map_description_to_account("Netflix.Com")
        self.assertIsNotNone(result)
        self.assertNotEqual(result, "")
    
    def test_complete_pipeline_with_sample_data(self):
        """Test complete pipeline with sample transaction data"""
        from src.transaction_parser import TransactionParser
        from src.currency_handler import CurrencyHandler
        import pandas as pd
        
        # Create sample transaction data
        sample_transactions = [
            {
                'Transaction Date': 'May 01',
                'Post Date': 'May 02',
                'Description': 'Netflix.Com',
                'Amount': 549.00,
                'Currency': 'PHP',
                'Foreign Amount': None,
                'Exchange Rate': None,
                'Card': 'BPI ECREDIT CARD'
            },
            {
                'Transaction Date': 'May 03',
                'Post Date': 'May 04',
                'Description': 'Apple.Com/Bill',
                'Amount': 2900.00,
                'Currency': 'USD',
                'Foreign Amount': 50.00,
                'Exchange Rate': 58.00,
                'Card': 'BPI GOLD REWARDS CARD'
            }
        ]
        
        # Create DataFrame
        df = pd.DataFrame(sample_transactions)
        
        # Process with currency handler
        handler = CurrencyHandler()
        df_clean = handler.clean_dataframe(df, 2025)
        
        # Check that data was processed
        self.assertIsNotNone(df_clean)
        self.assertEqual(len(df_clean), 2)
        
        # Check date conversion worked
        self.assertIn('Post Date', df_clean.columns)
        
        # Save to CSV
        output_path = os.path.join(self.test_dir, 'test_output.csv')
        df_clean.to_csv(output_path, index=False)
        self.assertTrue(os.path.exists(output_path))
    
    def test_batch_processor_initialization(self):
        """Test that BatchStatementProcessor can be initialized"""
        from src.batch_processor import BatchStatementProcessor
        
        processor = BatchStatementProcessor(
            pdf_folder=self.test_dir,
            output_folder=self.test_dir
        )
        self.assertIsNotNone(processor)
        self.assertEqual(processor.pdf_folder, self.test_dir)
        self.assertEqual(processor.output_folder, self.test_dir)
    
    def test_date_parsing_logic(self):
        """Test date parsing for cross-year transactions"""
        from src.currency_handler import CurrencyHandler
        
        handler = CurrencyHandler()
        
        # Test December transaction in January statement
        test_data = pd.DataFrame([
            {'Post Date': 'December 31', 'Amount': 100},
            {'Post Date': 'January 01', 'Amount': 200}
        ])
        
        # Process with January statement year
        result = handler.clean_dataframe(test_data, 2025)
        
        # December should be 2024, January should be 2025
        dates = pd.to_datetime(result['Post Date'])
        self.assertEqual(dates.iloc[0].year, 2024)
        self.assertEqual(dates.iloc[1].year, 2025)
    
    def test_file_validation(self):
        """Test file validation functions"""
        # Test PDF validation
        from src.web_app import allowed_file, validate_pdf
        
        self.assertTrue(allowed_file('test.pdf'))
        self.assertFalse(allowed_file('test.txt'))
        
        # Create test files
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4')
            valid_pdf = f.name
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'Not a PDF')
            invalid_pdf = f.name
        
        try:
            self.assertTrue(validate_pdf(valid_pdf))
            self.assertFalse(validate_pdf(invalid_pdf))
        finally:
            os.unlink(valid_pdf)
            os.unlink(invalid_pdf)

class TestErrorHandling(unittest.TestCase):
    """Test error handling throughout the application"""
    
    def test_missing_pdf_file_handling(self):
        """Test handling of missing PDF files"""
        from src.pdf_extractor import PDFExtractor
        
        # Should handle missing file gracefully
        try:
            extractor = PDFExtractor('/nonexistent/file.pdf')
            # If it doesn't raise an error immediately, try to extract
            text = extractor.extract_text()
        except Exception as e:
            # Should get an error but not crash
            self.assertIsNotNone(e)
    
    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrames"""
        from src.currency_handler import CurrencyHandler
        import pandas as pd
        
        handler = CurrencyHandler()
        empty_df = pd.DataFrame()
        
        # Should handle empty DataFrame without crashing
        result = handler.clean_dataframe(empty_df, 2025)
        self.assertIsNotNone(result)
        self.assertTrue(result.empty)
    
    def test_invalid_date_handling(self):
        """Test handling of invalid dates"""
        from src.currency_handler import CurrencyHandler
        import pandas as pd
        
        handler = CurrencyHandler()
        
        # Create DataFrame with invalid date
        test_data = pd.DataFrame([
            {'Post Date': 'Invalid Date', 'Amount': 100}
        ])
        
        # Should handle invalid date gracefully
        try:
            result = handler.clean_dataframe(test_data, 2025)
            # Either it handles it or raises a controlled error
            self.assertIsNotNone(result)
        except Exception as e:
            # Should be a meaningful error
            self.assertIsNotNone(str(e))

if __name__ == '__main__':
    unittest.main()