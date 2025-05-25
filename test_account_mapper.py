# test_account_mapper.py - Test the account mapper on real CSV data
import pandas as pd
import os
from account_mapper import AccountMapper

def test_account_mapping(csv_path, accounts_csv_path=None):
    """Test account mapping on real CSV data"""
    print("="*80)
    print("TESTING ACCOUNT MAPPER ON REAL DATA")
    print("="*80)
    
    # Check if CSV exists
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    # Load the CSV
    print(f"📖 Loading CSV: {os.path.basename(csv_path)}")
    try:
        df = pd.read_csv(csv_path)
        print(f"   ✅ Loaded {len(df)} transactions")
        print(f"   📋 Columns: {list(df.columns)}")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return
    
    # Check if Description column exists
    if 'Description' not in df.columns:
        print("❌ 'Description' column not found in CSV")
        return
    
    # Initialize account mapper
    print(f"\n🎯 Initializing account mapper...")
    if accounts_csv_path and os.path.exists(accounts_csv_path):
        mapper = AccountMapper(accounts_csv_path)
    else:
        print("   ⚠️  No accounts CSV provided, using built-in mappings only")
        mapper = AccountMapper()
    
    # Test mapping on all descriptions
    print(f"\n🔍 Testing account mapping on {len(df)} transactions...")
    
    descriptions = df['Description'].tolist()
    mapped_accounts = []
    mapping_details = []
    
    for i, desc in enumerate(descriptions):
        account = mapper.map_description_to_account(desc)
        mapped_accounts.append(account)
        mapping_details.append({
            'index': i + 1,
            'description': desc,
            'mapped_account': account
        })
    
    # Add results to dataframe for analysis
    df_test = df.copy()
    df_test['Mapped_Account'] = mapped_accounts
    
    # Generate summary
    print(f"\n📊 MAPPING RESULTS SUMMARY")
    print("="*80)
    
    total_transactions = len(df_test)
    manual_review_count = mapped_accounts.count('Manual Review')
    auto_mapped_count = total_transactions - manual_review_count
    
    print(f"Total transactions: {total_transactions}")
    print(f"Auto-mapped: {auto_mapped_count} ({auto_mapped_count/total_transactions*100:.1f}%)")
    print(f"Manual review needed: {manual_review_count} ({manual_review_count/total_transactions*100:.1f}%)")
    
    # Show account distribution
    print(f"\n🎯 ACCOUNT DISTRIBUTION:")
    account_counts = df_test['Mapped_Account'].value_counts()
    for account, count in account_counts.items():
        percentage = (count / total_transactions) * 100
        print(f"   {account}: {count} transactions ({percentage:.1f}%)")
    
    # Show some successful mappings
    print(f"\n✅ SUCCESSFUL MAPPINGS (sample):")
    successful_mappings = df_test[df_test['Mapped_Account'] != 'Manual Review']
    if len(successful_mappings) > 0:
        sample_size = min(10, len(successful_mappings))
        for _, row in successful_mappings.head(sample_size).iterrows():
            desc = row['Description'][:50] + "..." if len(row['Description']) > 50 else row['Description']
            print(f"   '{desc}' → {row['Mapped_Account']}")
    
    # Show manual review cases
    manual_review_cases = df_test[df_test['Mapped_Account'] == 'Manual Review']
    if len(manual_review_cases) > 0:
        print(f"\n⚠️  MANUAL REVIEW NEEDED (first 10):")
        sample_size = min(10, len(manual_review_cases))
        for _, row in manual_review_cases.head(sample_size).iterrows():
            desc = row['Description'][:60] + "..." if len(row['Description']) > 60 else row['Description']
            print(f"   '{desc}'")
    
    # Ask if user wants to save results
    print(f"\n💾 SAVE TEST RESULTS?")
    save_choice = input("Save results to CSV for review? (y/n): ").strip().lower()
    
    if save_choice in ['y', 'yes']:
        # Generate output filename
        base_name = os.path.basename(csv_path).replace('.csv', '')
        output_path = os.path.join(os.path.dirname(csv_path), f"{base_name}_with_account_mapping_test.csv")
        
        # Save with mapping results
        df_test.to_csv(output_path, index=False)
        print(f"✅ Test results saved to: {os.path.basename(output_path)}")
        
        # Also save just the manual review cases
        if len(manual_review_cases) > 0:
            manual_review_path = os.path.join(os.path.dirname(csv_path), f"{base_name}_manual_review_needed.csv")
            manual_review_cases[['Description', 'Amount', 'Currency']].to_csv(manual_review_path, index=False)
            print(f"📋 Manual review cases saved to: {os.path.basename(manual_review_path)}")
    
    return df_test

def main():
    """Main test function"""
    # Default paths
    csv_path = "/home/user/Library/CloudStorage/GoogleDrive-user@example.com/My Drive/Money/BPI/For Import Statement BPI Master 2025-05-25-1413.csv"
    accounts_csv_path = "/path/to/project/data/input/Accounts List 2024-07.csv"
    
    # Allow user to specify different paths
    import sys
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    if len(sys.argv) > 2:
        accounts_csv_path = sys.argv[2]
    
    print(f"Testing with:")
    print(f"   CSV file: {csv_path}")
    print(f"   Accounts file: {accounts_csv_path}")
    print()
    
    # Run the test
    result_df = test_account_mapping(csv_path, accounts_csv_path)
    
    if result_df is not None:
        print("\n" + "="*80)
        print("🎉 Test completed!")
        print("Review the results above to see how well the mapping worked.")
        print("Adjust the known_mappings and keyword_rules in account_mapper.py as needed.")
        print("="*80)

if __name__ == "__main__":
    main()