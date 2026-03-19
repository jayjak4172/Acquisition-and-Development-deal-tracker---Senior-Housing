"""
Split existing deals that contain multiple transactions
Fixed version with correct schema for development_projects table
"""

import sqlite3
import json
from openai import OpenAI
import os
from datetime import datetime
import argparse

def extract_multiple_deals(article_text, article_title, source_url):
    """
    Extract multiple deals from a single article using GPT
    """
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    prompt = f"""You are analyzing a senior housing industry news article that may contain MULTIPLE separate M&A transactions or development projects.

CRITICAL INSTRUCTIONS:
1. Extract EACH separate transaction as a separate JSON object
2. If article mentions multiple companies acquiring different properties → separate deals
3. If article is a roundup/digest with multiple transactions → separate deals
4. Return a JSON array with ALL deals found

Article Title: {article_title}
Article URL: {source_url}

Article Content:
{article_text[:8000]}

Analyze this article and return a JSON array of ALL separate transactions.

For M&A/Financing deals, use this format:
{{
  "deal_type": "M&A" or "Financing",
  "property_name": "name or N/A",
  "seller": "seller name or N/A",
  "buyer": "buyer name or N/A",
  "broker": "broker name or N/A",
  "price": "price as number or N/A",
  "total_units": "total units or N/A",
  "property_count": "number of properties or N/A",
  "property_type": "AL/MC/IL/CCRC/SNF/Mixed or N/A",
  "region": "state/region or N/A",
  "year_built": "YYYY or N/A",
  "property_age": "number or N/A"
}}

For Development projects, use this format:
{{
  "deal_type": "Development",
  "property_name": "project name or N/A",
  "developer": "developer name or N/A",
  "total_project_cost": "cost as number or N/A",
  "unit_count": "number of units or N/A",
  "building_type": "AL/MC/IL/CCRC/SNF/Mixed or N/A",
  "region": "state/region or N/A"
}}

CRITICAL RULES:
- Return a JSON ARRAY: [deal1, deal2, deal3, ...]
- If only ONE deal found, still return an array: [deal1]
- Each deal must be a separate object
- Use "N/A" for missing fields
- Price/cost must be a number (e.g., 71000000) or "N/A"

Return ONLY the JSON array, no other text."""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a precise data extraction assistant. Always return valid JSON arrays."},
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
        deals = json.loads(response_text)
        
        # Ensure it's a list
        if not isinstance(deals, list):
            deals = [deals]
        
        return deals
    
    except Exception as e:
        print(f"   ✗ Extraction error: {str(e)[:100]}")
        return None

def split_existing_deals(test_mode=True, limit=5):
    """
    Find articles with multiple deals and split them
    """
    print("\n" + "="*70)
    print("Split Existing Deals - Extract Multiple Transactions")
    print("="*70 + "\n")
    
    if test_mode:
        print(f"⚠️  TEST MODE - Processing up to {limit} articles")
        print("   No changes will be saved to database\n")
    else:
        print("🔥 LIVE MODE - Changes will be saved to database\n")
    
    conn = sqlite3.connect('senior_housing_deals.db')
    cursor = conn.cursor()
    
    # Find long articles (likely contain multiple deals)
    cursor.execute("""
        SELECT deal_id, article_title, source_url, raw_article_text, 
               LENGTH(raw_article_text) as text_length
        FROM deals 
        WHERE LENGTH(raw_article_text) > 1500
        ORDER BY text_length DESC
        LIMIT ?
    """, (limit if test_mode else 999999,))
    
    articles = cursor.fetchall()
    
    if not articles:
        print("✓ No long articles found")
        conn.close()
        return
    
    print(f"📊 Found {len(articles)} articles to analyze\n")
    print("="*70 + "\n")
    
    stats = {
        'processed': 0,
        'failed': 0,
        'single_deal': 0,
        'multiple_deals': 0,
        'total_deals_extracted': 0
    }
    
    new_deals_to_add = []
    new_dev_projects_to_add = []
    deals_to_delete = []
    
    for i, row in enumerate(articles, 1):
        deal_id, article_title, source_url, article_text, text_length = row
        
        print(f"[{i}/{len(articles)}] Deal #{deal_id}: {article_title[:50]}...")
        print(f"   Article length: {text_length} chars")
        
        # Extract
        deals = extract_multiple_deals(article_text, article_title, source_url)
        
        if deals is None:
            print(f"   ✗ Failed")
            stats['failed'] += 1
            continue
        
        num_deals = len(deals)
        stats['processed'] += 1
        stats['total_deals_extracted'] += num_deals
        
        if num_deals == 1:
            print(f"   ℹ Single deal (keeping as-is)")
            stats['single_deal'] += 1
        else:
            print(f"   ✓ Found {num_deals} separate deals!")
            stats['multiple_deals'] += 1
            
            # Add to deletion list
            deals_to_delete.append(deal_id)
            
            # Process each deal
            for idx, deal in enumerate(deals, 1):
                deal_type = deal.get('deal_type', 'M&A')
                
                # Create unique URL for each deal from same article
                unique_url = f"{source_url}#{idx}"
                
                if deal_type == 'Development':
                    # Development project - use correct schema
                    cost = deal.get('total_project_cost', 'N/A')
                    units = deal.get('unit_count', 'N/A')
                    
                    # Convert to proper types (REAL and INTEGER)
                    try:
                        cost_value = float(cost) if cost != 'N/A' else None
                    except:
                        cost_value = None
                    
                    try:
                        units_value = int(units) if units != 'N/A' else None
                    except:
                        units_value = None
                    
                    dev_data = (
                        unique_url,
                        article_title,
                        article_text[:5000],
                        deal.get('developer', 'N/A'),
                        deal.get('property_name', 'N/A'),
                        cost_value,  # total_project_cost (REAL)
                        units_value,  # unit_count (INTEGER)
                        deal.get('building_type', 'N/A'),
                        deal.get('region', 'N/A'),
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    )
                    new_dev_projects_to_add.append(dev_data)
                    print(f"      Deal {idx}: Development - {deal.get('property_name', 'N/A')}")
                else:
                    # M&A or Financing deal
                    deal_data = (
                        unique_url,
                        article_title,
                        article_text[:5000],
                        deal_type,
                        deal.get('property_name', 'N/A'),
                        deal.get('seller', 'N/A'),
                        deal.get('buyer', 'N/A'),
                        deal.get('broker', 'N/A'),
                        str(deal.get('price', 'N/A')),
                        str(deal.get('total_units', 'N/A')),
                        str(deal.get('property_count', 'N/A')),
                        deal.get('property_type', 'N/A'),
                        deal.get('region', 'N/A'),
                        str(deal.get('year_built', 'N/A')),
                        str(deal.get('property_age', 'N/A')),
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    )
                    new_deals_to_add.append(deal_data)
                    buyer = deal.get('buyer', 'N/A')
                    seller = deal.get('seller', 'N/A')
                    print(f"      Deal {idx}: {deal_type} - {buyer} ← {seller}")
        
        print()
    
    # Summary
    print("="*70)
    print("Summary")
    print("="*70)
    print(f"Processed: {stats['processed']}")
    print(f"Failed: {stats['failed']}")
    print(f"Single deal articles: {stats['single_deal']}")
    print(f"Multiple deal articles: {stats['multiple_deals']}")
    print(f"Total deals extracted: {stats['total_deals_extracted']}")
    print(f"\nNew M&A deals to add: {len(new_deals_to_add)}")
    print(f"New development projects to add: {len(new_dev_projects_to_add)}")
    print(f"Original deals to delete: {len(deals_to_delete)}")
    
    net_change = len(new_deals_to_add) + len(new_dev_projects_to_add) - len(deals_to_delete)
    print(f"\nNet change: +{net_change} deals")
    
    # Save changes
    if not test_mode and (new_deals_to_add or new_dev_projects_to_add):
        print("\n" + "="*70)
        print("Saving changes to database...")
        print("="*70 + "\n")
        
        try:
            # Add new deals
            for deal_data in new_deals_to_add:
                cursor.execute("""
                    INSERT INTO deals (
                        source_url, article_title, raw_article_text,
                        deal_type, property_name, seller, buyer, broker,
                        price, total_units, property_count, property_type, region,
                        year_built, property_age, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, deal_data)
            
            # Add development projects - CORRECT SCHEMA
            for dev_data in new_dev_projects_to_add:
                cursor.execute("""
                    INSERT INTO development_projects (
                        source_url, article_title, raw_article_text,
                        developer, property_name,
                        total_project_cost, unit_count, building_type, region,
                        last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, dev_data)
            
            # Delete original deals
            for deal_id in deals_to_delete:
                cursor.execute("DELETE FROM deals WHERE deal_id = ?", (deal_id,))
            
            conn.commit()
            print("✓ Changes saved successfully!")
            
        except Exception as e:
            conn.rollback()
            print(f"✗ Error saving: {str(e)}")
    
    elif test_mode:
        print("\n⚠️  TEST MODE - No changes saved")
    
    conn.close()
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Split articles with multiple deals')
    parser.add_argument('--run', action='store_true', help='Run in live mode (saves changes)')
    parser.add_argument('--test', type=int, default=5, help='Test mode limit (default: 5)')
    
    args = parser.parse_args()
    
    if args.run:
        split_existing_deals(test_mode=False)
    else:
        split_existing_deals(test_mode=True, limit=args.test)
