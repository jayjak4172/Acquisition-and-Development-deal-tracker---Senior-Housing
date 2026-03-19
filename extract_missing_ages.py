"""
Extract Missing Age Data from Existing Articles
Re-analyzes raw_article_text in database to find missed year_built/property_age
"""

import sqlite3
from openai import OpenAI
import json
import os
import time

CURRENT_YEAR = 2026

def extract_age_from_text(article_text, article_url=""):
    """Use GPT to extract ONLY age/year from article text"""
    
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    prompt = f"""Extract ONLY the year built or property age from this article text.

CURRENT YEAR: 2026

Look for these exact phrases:
- "built in [YYYY]"
- "constructed in [YYYY]"
- "developed in [YYYY]"
- "opened in [YYYY]"
- "completed in [YYYY]"
- "[X] years old"
- "age of [X]"
- "originally built..."
- "renovated in [YYYY]" (count as year_built)

IMPORTANT RULES:
1. If you find a 4-digit year (1800-2026), extract it
2. If you find age in years (e.g., "15 years old"), extract the number
3. If year is mentioned multiple times, use the EARLIEST year (original construction)
4. Return N/A ONLY if truly no age/year mentioned
5. Ignore phrases like "30th-largest operator" - this is NOT property age!

Article Text:
{article_text[:3000]}

Return ONLY this JSON:
{{
  "year_built": "YYYY or N/A",
  "property_age": "number or N/A",
  "confidence": "high/medium/low"
}}

NO other text. ONLY JSON."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You extract ONLY year built or property age from text. Return only valid JSON."},
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
        
        # Calculate missing field
        year_built = data.get('year_built', 'N/A')
        property_age = data.get('property_age', 'N/A')
        
        # If we have year, calculate age
        if year_built != 'N/A' and year_built is not None:
            try:
                year_int = int(year_built)
                if 1800 <= year_int <= CURRENT_YEAR:
                    calculated_age = CURRENT_YEAR - year_int
                    if property_age == 'N/A':
                        property_age = calculated_age
                else:
                    year_built = 'N/A'
            except:
                year_built = 'N/A'
        
        # If we have age, calculate year
        if property_age != 'N/A' and property_age is not None and year_built == 'N/A':
            try:
                age_int = int(property_age)
                if 1 <= age_int <= 200:
                    calculated_year = CURRENT_YEAR - age_int
                    year_built = calculated_year
                else:
                    property_age = 'N/A'
            except:
                property_age = 'N/A'
        
        return {
            'year_built': year_built,
            'property_age': property_age,
            'confidence': data.get('confidence', 'medium')
        }
    
    except Exception as e:
        print(f"      ✗ GPT error: {str(e)[:50]}")
        return None

def extract_missing_ages():
    """Main function to extract missing age data"""
    
    print("\n" + "="*70)
    print("EXTRACT MISSING AGE DATA FROM EXISTING ARTICLES")
    print("="*70 + "\n")
    
    conn = sqlite3.connect('senior_housing_deals.db')
    cursor = conn.cursor()
    
    # Find deals with missing age data
    cursor.execute("""
        SELECT deal_id, raw_article_text, source_url, article_title
        FROM deals
        WHERE (year_built = 'N/A' OR year_built IS NULL)
          AND (property_age = 'N/A' OR property_age IS NULL)
          AND raw_article_text IS NOT NULL
          AND LENGTH(raw_article_text) > 50
    """)
    
    missing_deals = cursor.fetchall()
    
    print(f"📊 Found {len(missing_deals)} deals with missing age data\n")
    
    if len(missing_deals) == 0:
        print("✓ No deals need age extraction!")
        conn.close()
        return
    
    # Estimate cost
    estimated_cost = len(missing_deals) * 0.001  # ~$0.001 per API call
    print(f"💰 Estimated cost: ${estimated_cost:.2f}")
    print(f"⏱️  Estimated time: {len(missing_deals) * 2} seconds\n")
    
    response = input(f"Continue with {len(missing_deals)} extractions? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        conn.close()
        return
    
    print("\n" + "="*70)
    print("PROCESSING")
    print("="*70 + "\n")
    
    extracted = 0
    failed = 0
    no_data = 0
    
    for i, (deal_id, article_text, url, title) in enumerate(missing_deals, 1):
        print(f"[{i}/{len(missing_deals)}] Deal #{deal_id}: {title[:50]}...")
        
        # Extract age
        result = extract_age_from_text(article_text, url)
        
        if result is None:
            print(f"      ✗ Extraction failed")
            failed += 1
            continue
        
        year_built = result['year_built']
        property_age = result['property_age']
        confidence = result['confidence']
        
        # Check if we found anything
        if year_built == 'N/A' and property_age == 'N/A':
            print(f"      ⊘ No age data in article")
            no_data += 1
        else:
            # Update database
            cursor.execute("""
                UPDATE deals
                SET year_built = ?,
                    property_age = ?
                WHERE deal_id = ?
            """, (year_built, property_age, deal_id))
            
            conn.commit()
            
            print(f"      ✓ year_built={year_built}, property_age={property_age} ({confidence} confidence)")
            extracted += 1
        
        # Rate limit: 1 request per second
        if i < len(missing_deals):
            time.sleep(1)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"✓ Extracted: {extracted} deals")
    print(f"⊘ No data:   {no_data} deals")
    print(f"✗ Failed:    {failed} deals")
    print(f"\nCoverage improvement:")
    
    # Calculate new coverage
    cursor.execute("SELECT COUNT(*) FROM deals")
    total_deals = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM deals
        WHERE year_built != 'N/A' OR property_age != 'N/A'
    """)
    deals_with_age = cursor.fetchone()[0]
    
    coverage = deals_with_age / total_deals * 100
    print(f"  Before: 22 deals (28.6%)")
    print(f"  After:  {deals_with_age} deals ({coverage:.1f}%)")
    print(f"  Gain:   +{extracted} deals (+{extracted/total_deals*100:.1f}%)\n")
    
    # Show examples
    print("="*70)
    print("EXAMPLES OF EXTRACTED DATA")
    print("="*70 + "\n")
    
    cursor.execute("""
        SELECT deal_id, article_title, year_built, property_age, region
        FROM deals
        WHERE deal_id IN (
            SELECT deal_id FROM deals
            WHERE year_built != 'N/A' OR property_age != 'N/A'
            ORDER BY deal_id DESC
            LIMIT 5
        )
    """)
    
    examples = cursor.fetchall()
    for deal_id, title, year_built, age, region in examples:
        print(f"Deal #{deal_id}: {title[:50]}...")
        print(f"  Year: {year_built} | Age: {age} years | Region: {region}\n")
    
    print("="*70)
    print("COMPLETE!")
    print("="*70 + "\n")
    
    conn.close()

if __name__ == "__main__":
    extract_missing_ages()
