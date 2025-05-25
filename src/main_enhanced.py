# main.py - Enhanced BPI Statement Parser with batch processing
import sys
import os

def show_menu():
    """Show main menu options"""
    print("="*60)
    print("BPI STATEMENT PARSER")
    print("="*60)
    print("1. Process single PDF")
    print("2. Process multiple PDFs (batch)")
    print("3. Exit")
    print("="*60)

def get_user_choice():
    """Get user menu choice"""
    while True:
        try:
            choice = input("Select option (1-3): ").strip()
            if choice in ['1', '2', '3']:
                return int(choice)
            else:
                print("Please enter 1, 2, or 3")
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            sys.exit(0)

def single_pdf_mode():
    """Process single PDF (original functionality)"""
    print("\n📄 SINGLE PDF MODE")
    print("-" * 30)
    
    # Get PDF file path
    pdf_path = input("Enter PDF file path (or press Enter for default): ").strip()
    
    if not pdf_path:
        pdf_path = "../data/Statement BPI Master 2025-05-12.pdf"
        print(f"Using default: {pdf_path}")
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    # Import and run single PDF processor
    try:
        from main_modular import main as process_single
        # Temporarily modify the file path in main_modular
        import main_modular
        
        # Run single PDF processing
        print(f"\n🚀 Processing: {pdf_path}")
        
        # You could enhance this to accept the path parameter
        # For now, user needs to place file in expected location
        process_single()
        
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")

def batch_pdf_mode():
    """Process multiple PDFs"""
    print("\n📁 BATCH PDF MODE")
    print("-" * 30)
    
    try:
        from batch_processor import main as process_batch
        process_batch()
    except Exception as e:
        print(f"❌ Error in batch processing: {e}")

def main():
    """Main application entry point"""
    while True:
        try:
            show_menu()
            choice = get_user_choice()
            
            if choice == 1:
                single_pdf_mode()
            elif choice == 2:
                batch_pdf_mode()
            elif choice == 3:
                print("\n👋 Goodbye!")
                break
            
            # Ask if user wants to continue
            if choice in [1, 2]:
                print("\n" + "="*60)
                continue_choice = input("Return to main menu? (y/n): ").strip().lower()
                if continue_choice not in ['y', 'yes']:
                    print("\n👋 Goodbye!")
                    break
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print("Returning to main menu...")

if __name__ == "__main__":
    main()