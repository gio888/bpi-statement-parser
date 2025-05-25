# check_skip_patterns.py - See what's being skipped
import re

def check_skip_patterns():
    """Check which lines are being skipped"""
    print("🔍 CHECKING SKIP PATTERNS")
    print("="*50)
    
    skip_patterns = [
        r'Statement of Account', 
        r'Customer Number', 
        r'Previous Balance',
        r'Past Due', 
        r'Ending Balance', 
        r'Unbilled Installment',
        r'Finance Charge', 
        r'GIOVANNI BACAREZA',
        r'Transaction\s+Post.*Date',
        r'^\d{6}-\d-\d{2}-\d{7}',
        r'^Date\s*$',
        r'^Transaction\s*$',
        r'^Post Date\s*$',
        r'^Description\s*$',
        r'^Amount\s*$'
    ]
    
    # Test the problematic lines
    test_lines = [
        "October 1 October 2 Payment -Thank You -21,401.07",
        "September 14 September 14 Reversal-Finance Charges -699.18", 
        "September 15 September 18 Backblaze.Com SanMateo US",
        "U.S.Dollar 40.42 2,337.48",
        "Finance Charge 0.00",
        "Previous Balance 21,401.07"
    ]
    
    for line in test_lines:
        print(f"\nTesting: '{line}'")
        
        should_skip = False
        for pattern in skip_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                print(f"  ❌ SKIPPED by pattern: {pattern}")
                should_skip = True
                break
        
        if not should_skip:
            print(f"  ✅ NOT SKIPPED - should be processed")

if __name__ == "__main__":
    check_skip_patterns()