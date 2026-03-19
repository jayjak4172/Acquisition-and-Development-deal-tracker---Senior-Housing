"""
View database statistics - v2.5
Shows financing breakdown + property type + age analysis
"""

from database import DealDatabase
from collections import Counter

def view_enhanced_stats():
    """Display enhanced database statistics"""
    db = DealDatabase()
    stats = db.get_stats()
    deals = db.get_all_deals()
    
    print("\n" + "="*70)
    print("DATABASE STATISTICS - v2.5 (FINANCING TRACKING)")
    print("="*70)
    
    # Basic stats
    print(f"\n📊 OVERVIEW:")
    print(f"  Total Deals: {stats['total_deals']}")
    print(f"  - Acquisitions: {stats['acquisitions']}")
    print(f"  - Financings: {stats['financings']}")
    print(f"  Total Deal Value: ${stats['total_value_millions']:.2f}M")
    print(f"  Total Properties: {stats['total_properties']}")
    print(f"  Total Units: {stats['total_units']:,}")
    
    if not deals:
        print("\n  No deals in database yet")
        return
    
    # Collect data
    property_types = []
    year_builts = []
    ages = []
    buyers = []
    financing_methods = []
    borrowers = []
    lenders = []
    financing_purposes = []
    
    for deal in deals:
        deal_type = deal[1]  # deal_type column
        prop_type = deal[17]  # property_type column
        year_built = deal[18]  # year_built column
        age = deal[19]  # property_age column
        buyer = deal[5]  # buyer column
        fin_method = deal[20]  # financing_method column
        borrower = deal[22]  # borrower column
        lender = deal[23]  # lender column
        fin_purpose = deal[24]  # financing_purpose column
        
        if prop_type and prop_type != 'N/A':
            property_types.append(prop_type)
        if year_built and year_built != 'N/A':
            try:
                year_builts.append(int(year_built))
            except:
                pass
        if age and age != 'N/A':
            try:
                ages.append(int(age))
            except:
                pass
        if buyer and buyer != 'N/A':
            buyers.append(buyer)
        if fin_method and fin_method != 'N/A':
            financing_methods.append(fin_method)
        if borrower and borrower != 'N/A':
            borrowers.append(borrower)
        if lender and lender != 'N/A':
            lenders.append(lender)
        if fin_purpose and fin_purpose != 'N/A':
            financing_purposes.append(fin_purpose)
    
    # Financing Analysis (NEW!)
    if financing_methods or financing_purposes:
        print(f"\n💰 FINANCING BREAKDOWN:")
        print("-" * 70)
        
        if financing_methods:
            print(f"\n  Financing Methods:")
            method_counts = Counter(financing_methods)
            for method, count in method_counts.most_common():
                percentage = (count / len(financing_methods)) * 100
                print(f"    {method:15s} {count:3d} deals ({percentage:5.1f}%)")
        
        if financing_purposes:
            print(f"\n  Financing Purposes:")
            purpose_counts = Counter(financing_purposes)
            for purpose, count in purpose_counts.most_common():
                percentage = (count / len(financing_purposes)) * 100
                print(f"    {purpose:20s} {count:3d} deals ({percentage:5.1f}%)")
        
        if lenders:
            print(f"\n  Top Lenders:")
            lender_counts = Counter(lenders)
            for lender, count in lender_counts.most_common(5):
                print(f"    {count:2d}x  {lender}")
        
        if borrowers:
            print(f"\n  Top Borrowers:")
            borrower_counts = Counter(borrowers)
            for borrower, count in borrower_counts.most_common(5):
                print(f"    {count:2d}x  {borrower}")
    
    # Property Type Stats
    if property_types:
        print(f"\n🏢 PROPERTY TYPE BREAKDOWN:")
        print("-" * 70)
        type_counts = Counter(property_types)
        
        type_names = {
            'AL': 'Assisted Living',
            'MC': 'Memory Care',
            'IL': 'Independent Living',
            'CCRC': 'Continuing Care Retirement Community',
            'AA': 'Active Adult',
            'SNF': 'Skilled Nursing Facility',
            'Mixed': 'Mixed Use'
        }
        
        for prop_type, count in type_counts.most_common():
            full_name = type_names.get(prop_type, prop_type)
            percentage = (count / len(property_types)) * 100
            print(f"  {prop_type:6s} - {full_name:40s} {count:3d} deals ({percentage:5.1f}%)")
        
        print(f"\n  Total with property type: {len(property_types)}/{stats['total_deals']}")
    
    # Age/Year Built Stats
    if year_builts or ages:
        print(f"\n🏗️  BUILDING AGE ANALYSIS:")
        print("-" * 70)
        print("  (Ages shown are at time of announcement/transaction)")
        print()
        
        if year_builts:
            avg_year = sum(year_builts) / len(year_builts)
            min_year = min(year_builts)
            max_year = max(year_builts)
            print(f"  Average Year Built: {int(avg_year)}")
            print(f"  Oldest Property: {min_year} ({2026 - min_year} years old)")
            print(f"  Newest Property: {max_year} ({2026 - max_year} years old)")
        
        if ages:
            avg_age = sum(ages) / len(ages)
            min_age = min(ages)
            max_age = max(ages)
            print(f"\n  Average Property Age: {int(avg_age)} years")
            print(f"  Newest: {min_age} years")
            print(f"  Oldest: {max_age} years")
        
        if ages:
            age_ranges = {
                'New (0-5 years)': len([a for a in ages if a <= 5]),
                'Recent (6-10 years)': len([a for a in ages if 6 <= a <= 10]),
                'Mature (11-20 years)': len([a for a in ages if 11 <= a <= 20]),
                'Older (21+ years)': len([a for a in ages if a > 20])
            }
            print(f"\n  Age Distribution:")
            for range_name, count in age_ranges.items():
                if count > 0:
                    percentage = (count / len(ages)) * 100
                    print(f"    {range_name:20s} {count:3d} ({percentage:5.1f}%)")
        
        print(f"\n  Total with age/year data: {max(len(year_builts), len(ages))}/{stats['total_deals']}")
    
    # Top Buyers
    if buyers:
        print(f"\n💼 TOP BUYERS:")
        print("-" * 70)
        buyer_counts = Counter(buyers)
        for buyer, count in buyer_counts.most_common(10):
            print(f"  {count:2d}x  {buyer}")
    
    # Recent deals
    print("\n" + "="*70)
    print("RECENT DEALS (최근 5개)")
    print("="*70)
    
    for i, deal in enumerate(deals[:5], 1):
        deal_id = deal[0]
        deal_type = deal[1] if deal[1] != 'N/A' else 'Unknown'
        buyer = deal[5] if deal[5] != 'N/A' else 'N/A'
        seller = deal[4] if deal[4] != 'N/A' else 'N/A'
        price = deal[12]
        prop_type = deal[17] if deal[17] != 'N/A' else 'N/A'
        year_built = deal[18] if deal[18] != 'N/A' else 'N/A'
        age = deal[19] if deal[19] != 'N/A' else 'N/A'
        fin_method = deal[20] if deal[20] != 'N/A' else 'N/A'
        
        # Financing-specific fields
        borrower = deal[22] if deal[22] != 'N/A' else 'N/A'
        lender = deal[23] if deal[23] != 'N/A' else 'N/A'
        fin_purpose = deal[24] if deal[24] != 'N/A' else 'N/A'
        loan_amount = deal[25]
        
        print(f"\n[{i}] {deal_type}")
        
        if deal_type == 'Acquisition':
            print(f"    {buyer} ← {seller}")
            
            if price and price != 'N/A':
                try:
                    print(f"    💰 ${float(price)/1_000_000:.2f}M")
                except:
                    print(f"    💰 {price}")
            
            if prop_type != 'N/A':
                print(f"    🏢 Type: {prop_type}")
            
            if year_built != 'N/A':
                print(f"    🏗️  Built: {year_built}")
            elif age != 'N/A':
                print(f"    🏗️  Age: {age} years")
            
            if fin_method != 'N/A':
                print(f"    💵 Financing: {fin_method}")
        
        elif deal_type == 'Financing':
            print(f"    {borrower} from {lender}")
            
            if loan_amount and loan_amount != 'N/A':
                try:
                    print(f"    💰 ${float(loan_amount)/1_000_000:.2f}M")
                except:
                    print(f"    💰 {loan_amount}")
            
            if fin_purpose != 'N/A':
                print(f"    🎯 Purpose: {fin_purpose}")
    
    # Data completeness
    print("\n" + "="*70)
    print("DATA QUALITY CHECK")
    print("="*70)
    
    total = stats['total_deals']
    if total > 0:
        completeness = {
            'Buyer': len([d for d in deals if d[5] and d[5] != 'N/A']),
            'Seller': len([d for d in deals if d[4] and d[4] != 'N/A']),
            'Price': stats['deals_with_price'],
            'Property Type': len(property_types),
            'Year Built/Age': max(len(year_builts), len(ages)),
            'Financing Method': len(financing_methods),
            'Deal Type': len([d for d in deals if d[1] and d[1] != 'N/A']),
        }
        
        print("\nField Completeness:")
        for field, count in completeness.items():
            percentage = (count / total) * 100
            bar = '█' * int(percentage / 5) + '░' * (20 - int(percentage / 5))
            print(f"  {field:20s} [{bar}] {percentage:5.1f}% ({count}/{total})")
    
    print("\n" + "="*70)
    print("To export: python export_data.py")
    print("="*70 + "\n")

if __name__ == "__main__":
    view_enhanced_stats()
