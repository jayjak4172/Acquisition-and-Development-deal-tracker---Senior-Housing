"""
Re-Extract Data from Existing Deals
Comprehensively re-analyzes ALL deals to extract:
- Property names
- Broker vs Seller
- Age data
- Better property_count

Uses existing raw_article_text - no re-scraping needed!
"""

import sqlite3
from openai import OpenAI
import json
import os
import time
from datetime import datetime

CURRENT_YEAR = 2026

def re_extract_deal_data(article_text, article_title="", current_data=None):
    """Re-extract property_name, broker, seller, age from existing article"""
    
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Show current values for context
    current_seller = current_data.get('seller', 'N/A') if current_data else 'N/A'
    current_buyer = current_data.get('buyer', 'N/A') if current_data else 'N/A'
    
    prompt = f"""Re-analyze this article to extract SPECIFIC fields. Focus on accuracy.

CURRENT YEAR: 2026

=== CRITICAL: BROKER vs SELLER ===

KNOWN BROKERS (intermediaries - NOT sellers/buyers):
- SLIB / Senior Living Investment Brokerage
- Blueprint / Blueprint Healthcare
- Continuum / Continuum Advisors
- Helios / Helios Healthcare Advisors
- Zett Group / The Zett Group
- JLL / JLL Capital Markets
- Marcus & Millichap
- CBRE
- Cushman & Wakefield
- Colliers
- Newmark
- Kislak / The Kislak Co
- Northmark

RULES:
1. "SLIB arranged the sale" → seller: "Undisclosed", broker: "SLIB"
2. "Blueprint brokered" → seller: "Undisclosed", broker: "Blueprint"
3. "on behalf of undisclosed seller" → seller: "Undisclosed", broker: [company]
4. "represented the seller" → that company is BROKER

=== PROPERTY NAME ===

Extract the ACTUAL property/community name:
- "Churchill Estates" (property name)
- "Laurel Circle" (property name)
- "Morrison Ranch" (property name)

NOT seller names! Look for:
- "located in"
- "the community"
- "the property"
- Named communities in title

=== AGE DATA ===

Look for:
- "built in [YYYY]"
- "constructed in [YYYY]"
- "developed in [YYYY]"
- "opened in [YYYY]"
- "[X] years old"
- "average age of [X]"

=== PROPERTY COUNT ===

SINGLE property:
- "a community"
- "the property"
- "one facility"
→ property_count: 1

MULTIPLE:
- "portfolio of 5"
- "three communities"
→ property_count: [number]

Article Title: {article_title}

Current Extraction (may be wrong):
- Seller: {current_seller}
- Buyer: {current_buyer}

Article Text:
{article_text[:4000]}

Return ONLY JSON:
{{
  "property_name": "Exact property/community name or N/A",
  "seller": "ACTUAL seller (NOT broker) or Undisclosed or N/A",
  "buyer": "ACTUAL buyer (NOT broker) or N/A",
  "broker": "Broker/intermediary or N/A",
  "year_built": "YYYY or N/A",
  "property_age": "number or N/A",
  "property_count": "1 for single property, number for portfolio, or N/A",
  "confidence": "high/medium/low"
}}

CRITICAL: Return ONLY JSON, no other text."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You re-extract specific fields from M&A articles. Focus on property names, brokers vs sellers, and age. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Clean response
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        # Parse JSON
        data = json.loads(response_text)
        
        # Calculate missing age field
        year_built = data.get('year_built', 'N/A')
        property_age = data.get('property_age', 'N/A')
        
        if year_built != 'N/A' and year_built is not None:
            try:
                year_int = int(year_built)
                if 1800 <= year_int <= CURRENT_YEAR:
                    if property_age == 'N/A':
                        data['property_age'] = CURRENT_YEAR - year_int
                else:
                    data['year_built'] = 'N/A'
            except:
                data['year_built'] = 'N/A'
        
        if property_age != 'N/A' and property_age is not None and year_built == 'N/A':
            try:
                age_int = int(property_age)
                if 1 <= age_int <= 200:
                    data['year_built'] = CURRENT_YEAR - age_int
                else:
                    data['property_age'] = 'N/A'
            except:
                data['property_age'] = 'N/A'
        
        return data
    
    except Exception as e:
        print(f"      ✗ GPT error: {str(e)[:50]}")
        return None

def recalculate_units_per_property(total_units, property_count):
    """Recalculate with correct logic"""
    if total_units in ['N/A', None, 0, '0']:
        return 'N/A'
    
    if property_count in ['N/A', None, 0, '0', 1, '1']:
        try:
            return float(total_units)
        except:
            return 'N/A'
    
    try:
        units = float(total_units)
        props = float(property_count)
        return round(units / props, 1)
    except:
        return 'N/A'

def re_extract_all_deals(test_mode=True, limit=None):
    """Re-extract data for all existing deals"""
    
    print("\n" + "="*70)
    print("RE-EXTRACT DATA FROM ALL EXISTING DEALS")
    print("="*70 + "\n")
    
    if test_mode:
        print("⚠️  TEST MODE: Will show changes but NOT update database")
        print("   Run with test_mode=False to apply changes\n")
    
    conn = sqlite3.connect('senior_housing_deals.db')
    cursor = conn.cursor()
    
    # Get all deals with article text
    query = """
        SELECT deal_id, property_name, seller, buyer, broker,
               year_built, property_age, property_count, total_units, units_per_property,
               article_title, raw_article_text, source_url
        FROM deals
        WHERE raw_article_text IS NOT NULL
          AND LENGTH(raw_article_text) > 50
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    deals = cursor.fetchall()
    
    print(f"📊 Found {len(deals)} deals to re-extract\n")
    
    if len(deals) == 0:
        print("✓ No deals to process")
        conn.close()
        return
    
    # Estimate cost
    estimated_cost = len(deals) * 0.0015  # ~$0.0015 per call (longer prompt)
    print(f"💰 Estimated cost: ${estimated_cost:.2f}")
    print(f"⏱️  Estimated time: {len(deals) * 2} seconds\n")
    
    if not test_mode:
        response = input(f"Continue with {len(deals)} re-extractions? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            conn.close()
            return
    
    print("\n" + "="*70)
    print("PROCESSING")
    print("="*70 + "\n")
    
    changes = {
        'property_name': 0,
        'broker': 0,
        'seller': 0,
        'age': 0,
        'property_count': 0,
        'units_per_property': 0,
        'no_change': 0,
        'failed': 0
    }
    
    for i, row in enumerate(deals, 1):
        (deal_id, old_property_name, old_seller, old_buyer, old_broker,
         old_year_built, old_property_age, old_property_count, total_units, old_units_per_property,
         article_title, article_text, url) = row
        
        print(f"[{i}/{len(deals)}] Deal #{deal_id}: {article_title[:50]}...")
        
        # Current data
        current_data = {
            'seller': old_seller,
            'buyer': old_buyer,
            'broker': old_broker,
            'property_name': old_property_name,
            'year_built': old_year_built,
            'property_age': old_property_age,
            'property_count': old_property_count
        }
        
        # Re-extract
        result = re_extract_deal_data(article_text, article_title, current_data)
        
        if result is None:
            print(f"      ✗ Extraction failed")
            changes['failed'] += 1
            continue
        
        # Check what changed
        changed = []
        
        # Property name
        new_property_name = result.get('property_name', 'N/A')
        if new_property_name != 'N/A' and new_property_name != old_property_name:
            changed.append(f"property_name: '{old_property_name}' → '{new_property_name}'")
            changes['property_name'] += 1
        
        # Broker
        new_broker = result.get('broker', 'N/A')
        if new_broker != old_broker and new_broker != 'N/A':
            changed.append(f"broker: '{old_broker}' → '{new_broker}'")
            changes['broker'] += 1
        
        # Seller
        new_seller = result.get('seller', 'N/A')
        if new_seller != old_seller:
            changed.append(f"seller: '{old_seller}' → '{new_seller}'")
            changes['seller'] += 1
        
        # Age
        new_year_built = result.get('year_built', 'N/A')
        new_property_age = result.get('property_age', 'N/A')
        
        age_changed = False
        if (new_year_built != 'N/A' and new_year_built != old_year_built) or \
           (new_property_age != 'N/A' and new_property_age != old_property_age):
            changed.append(f"age: year={new_year_built}, age={new_property_age}")
            changes['age'] += 1
            age_changed = True
        
        # Property count
        new_property_count = result.get('property_count', 'N/A')
        if new_property_count != 'N/A' and str(new_property_count) != str(old_property_count):
            changed.append(f"property_count: {old_property_count} → {new_property_count}")
            changes['property_count'] += 1
        
        # Recalculate units_per_property
        new_units_per_property = recalculate_units_per_property(total_units, new_property_count if new_property_count != 'N/A' else old_property_count)
        if new_units_per_property != 'N/A' and new_units_per_property != old_units_per_property:
            changed.append(f"units_per_property: {old_units_per_property} → {new_units_per_property}")
            changes['units_per_property'] += 1
        
        # Display changes
        if changed:
            for change in changed:
                print(f"      ✓ {change}")
            
            # Update database if not test mode
            if not test_mode:
                cursor.execute("""
                    UPDATE deals
                    SET property_name = ?,
                        seller = ?,
                        broker = ?,
                        year_built = ?,
                        property_age = ?,
                        property_count = ?,
                        units_per_property = ?,
                        last_updated = ?
                    WHERE deal_id = ?
                """, (
                    new_property_name if new_property_name != 'N/A' else old_property_name,
                    new_seller if new_seller != 'N/A' else old_seller,
                    new_broker if new_broker != 'N/A' else old_broker,
                    new_year_built if new_year_built != 'N/A' else old_year_built,
                    new_property_age if new_property_age != 'N/A' else old_property_age,
                    new_property_count if new_property_count != 'N/A' else old_property_count,
                    new_units_per_property if new_units_per_property != 'N/A' else old_units_per_property,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    deal_id
                ))
                conn.commit()
        else:
            print(f"      ⊘ No changes")
            changes['no_change'] += 1
        
        # Rate limit
        if i < len(deals):
            time.sleep(1.2)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\n📊 CHANGES DETECTED:")
    print(f"  Property Names:     {changes['property_name']} deals")
    print(f"  Broker Extracted:   {changes['broker']} deals")
    print(f"  Seller Corrected:   {changes['seller']} deals")
    print(f"  Age Added:          {changes['age']} deals")
    print(f"  Property Count:     {changes['property_count']} deals")
    print(f"  Units/Property:     {changes['units_per_property']} deals")
    print(f"  No Changes:         {changes['no_change']} deals")
    print(f"  Failed:             {changes['failed']} deals")
    
    total_changed = sum(changes.values()) - changes['no_change'] - changes['failed']
    print(f"\n✓ Total deals improved: {total_changed}/{len(deals)}")
    
    if test_mode:
        print("\n⚠️  TEST MODE - No changes were saved to database")
        print("   Run again with test_mode=False to apply changes")
    else:
        print("\n✓ Changes saved to database!")
        
        # Verify
        print("\n📊 VERIFICATION:")
        
        cursor.execute("""
            SELECT COUNT(*) FROM deals WHERE property_name != 'N/A'
        """)
        print(f"  Deals with property names: {cursor.fetchone()[0]}")
        
        cursor.execute("""
            SELECT COUNT(*) FROM deals WHERE broker != 'N/A'
        """)
        print(f"  Deals with brokers: {cursor.fetchone()[0]}")
        
        cursor.execute("""
            SELECT COUNT(*) FROM deals 
            WHERE year_built != 'N/A' OR property_age != 'N/A'
        """)
        print(f"  Deals with age data: {cursor.fetchone()[0]}")
    
    print("\n" + "="*70)
    print("COMPLETE!")
    print("="*70 + "\n")
    
    conn.close()

if __name__ == "__main__":
    import sys
    
    # Default: test mode with 5 deals
    test_mode = True
    limit = 5
    
    # Parse arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--run':
            test_mode = False
            limit = None
        elif sys.argv[1] == '--test':
            test_mode = True
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    print("\nUSAGE:")
    print("  python re_extract_all.py              # Test mode: 5 deals")
    print("  python re_extract_all.py --test 10    # Test mode: 10 deals")
    print("  python re_extract_all.py --run        # REAL RUN: All deals\n")
    
    re_extract_all_deals(test_mode=test_mode, limit=limit)
