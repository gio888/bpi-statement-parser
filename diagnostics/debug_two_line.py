# debug_two_line.py - Check why foreign currency isn't being parsed
import re

def test_two_line_patterns():
    """Test the two-line foreign currency patterns"""
    print("🔍 TESTING TWO-LINE FOREIGN CURRENCY PATTERNS")
    print("="*60)
    
    # Known two-line pairs from the 2023 PDF
    test_pairs = [
        ("September 15 September 18 Backblaze.Com SanMateo US", "U.S.Dollar 40.42 2,337.48"),
        ("September 20 September 21 Medium Monthly SanFrancisco US", "U.S.Dollar 5.00 289.55"),
        ("October 2 October 2 Google Cloud Wzzjnt Sg SG", "U.S.Dollar 0.01 0.58"),
        ("October 4 October 4 Nintendo Cd1065471405 8002553700 US", "U.S.Dollar 7.99 463.27"),
        ("October 3 October 4 Audible*T90n24ln1 Amzn.Com/Bill US", "U.S.Dollar 14.95 866.84"),
        ("October 6 October 6 Wsj/Barrons Subscripti 800-568-7625 US", "U.S.Dollar 9.99 577.21"),
        ("October 8 October 9 Backblaze.Com SanMateo US", "U.S.Dollar 9.36 541.00"),
        ("October 9 October 10 Epic!Reading AndLearRedwood City US", "U.S.Dollar 9.99 580.15")
    ]
    
    # Current patterns from the parser
    pattern1 = r'^([A-Za-z]{3,9})\s*(\d{1,2})\s+([A-Za-z]{3,9})\s*(\d{1,2})\s+(.+?)\s+(US|SG|NZ|[A-Z]{2,3})$'
    pattern2 = r'^([A-Z][a-z]*(?:\s*[A-Z][a-z]*)*)\s*Dollar\s+([\d.,]+)\s+(\d{1,3}(?:,\d{3})*\.\d{2})$'
    
    print(f"Pattern 1 (first line): {pattern1}")
    print(f"Pattern 2 (second line): {pattern2}")
    print()
    
    for i, (line1, line2) in enumerate(test_pairs, 1):
        print(f"Test {i}:")
        print(f"  Line 1: '{line1}'")
        print(f"  Line 2: '{line2}'")
        
        match1 = re.match(pattern1, line1)
        match2 = re.match(pattern2, line2)
        
        if match1:
            print(f"  ✓ Line 1 matches - Groups: {match1.groups()}")
        else:
            print(f"  ✗ Line 1 NO MATCH")
            
        if match2:
            print(f"  ✓ Line 2 matches - Groups: {match2.groups()}")
        else:
            print(f"  ✗ Line 2 NO MATCH")
            
        if match1 and match2:
            print(f"  🎉 BOTH MATCH - should be captured as foreign currency")
        else:
            print(f"  ❌ PARSING FAILURE")
        
        print()

if __name__ == "__main__":
    test_two_line_patterns()