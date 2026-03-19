"""
Check for entity duplicates in database
Helps identify which companies need normalization
"""

from database import DealDatabase
from collections import Counter

def check_entity_duplicates():
    """Find potential duplicate entities"""
    db = DealDatabase()
    deals = db.get_all_deals()
    
    # Collect all buyers and sellers
    buyers = []
    sellers = []
    
    for deal in deals:
        buyer = deal[3]  # buyer column
        seller = deal[2]  # seller column
        
        if buyer and buyer != 'N/A':
            buyers.append(buyer)
        if seller and seller != 'N/A':
            sellers.append(seller)
    
    # Count frequencies
    buyer_counts = Counter(buyers)
    seller_counts = Counter(sellers)
    
    print("\n" + "="*70)
    print("ENTITY DUPLICATE CHECK")
    print("="*70)
    
    print("\n📊 TOP BUYERS:")
    print("-" * 70)
    for buyer, count in buyer_counts.most_common(20):
        print(f"  {count:2d}x  {buyer}")
    
    print("\n📊 TOP SELLERS:")
    print("-" * 70)
    for seller, count in seller_counts.most_common(20):
        print(f"  {count:2d}x  {seller}")
    
    # Find potential duplicates (case-insensitive)
    print("\n⚠️  POTENTIAL DUPLICATES (case-insensitive):")
    print("-" * 70)
    
    # Check buyers
    buyer_lower = {}
    for buyer in set(buyers):
        lower = buyer.lower()
        if lower not in buyer_lower:
            buyer_lower[lower] = []
        buyer_lower[lower].append(buyer)
    
    duplicates_found = False
    for lower, variations in buyer_lower.items():
        if len(variations) > 1:
            duplicates_found = True
            print(f"\n  {lower}:")
            for var in variations:
                count = buyer_counts[var]
                print(f"    - {var} ({count}x)")
    
    # Check sellers
    seller_lower = {}
    for seller in set(sellers):
        lower = seller.lower()
        if lower not in seller_lower:
            seller_lower[lower] = []
        seller_lower[lower].append(seller)
    
    for lower, variations in seller_lower.items():
        if len(variations) > 1:
            duplicates_found = True
            print(f"\n  {lower}:")
            for var in variations:
                count = seller_counts[var]
                print(f"    - {var} ({count}x)")
    
    if not duplicates_found:
        print("  ✓ No obvious duplicates found!")
    
    print("\n" + "="*70)
    print("RECOMMENDATIONS:")
    print("="*70)
    print("\nIf you see duplicates:")
    print("1. Add them to entity_mapping.py")
    print("2. Re-run scraper to normalize future extractions")
    print("3. (Optional) Run normalize_existing.py to fix old data")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    check_entity_duplicates()
