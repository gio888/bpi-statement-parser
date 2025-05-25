# pdf_extractor.py - Handles PDF text extraction
import pdfplumber

class PDFExtractor:
    def __init__(self, file_path):
        self.file_path = file_path
    
    def extract_text(self):
        """Extract text using PyPDF2 (works better for this PDF)"""
        text = ""
        try:
            import PyPDF2
            with open(self.file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                print(f"Extracting from {len(pdf_reader.pages)} pages using PyPDF2...")
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text += f"\n=== PAGE {page_num + 1} ===\n"
                        text += page_text + "\n"
                        print(f"  Page {page_num + 1}: {len(page_text)} characters")
                    else:
                        print(f"  Page {page_num + 1}: empty")
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
            raise
        
        return text
    
    def get_page_count(self):
        """Get number of pages in PDF"""
        with pdfplumber.open(self.file_path) as pdf:
            return len(pdf.pages)
    
    def extract_text_by_page(self):
        """Extract text page by page"""
        pages = []
        with pdfplumber.open(self.file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                pages.append(page_text if page_text else "")
        return pages