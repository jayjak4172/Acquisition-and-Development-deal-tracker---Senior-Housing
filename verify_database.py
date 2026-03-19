"""
Database Verification After Re-Extraction
"""

import sqlite3
import pandas as pd

conn = sqlite3.connect('senior_housing_deals.db')

print("="*70)
print("DATABASE VERIFICATION")
print("="*70 + "\n")

# 1. Property Names
print("1. PROPERTY NAMES (sample):")
print("-"*70)
df = pd.read_sql_query("""
    SELECT deal_id, property_name, region
    FROM deals
    WHERE property_name != 'N/A'
    ORDER BY deal_id DESC
    LIMIT 10
""", conn)
print(df.to_string(index=False))

# 2. Brokers
print("\n2. BROKERS:")
print("-"*70)
df = pd.read_sql_query("""
    SELECT broker, COUNT(*) as deals
    FROM deals
    WHERE broker != 'N/A'
    GROUP BY broker
    ORDER BY deals DESC
""", conn)
print(df.to_string(index=False))

# 3. Top Sellers (should NOT include brokers!)
print("\n3. TOP SELLERS (should NOT be SLIB/Blueprint):")
print("-"*70)
df = pd.read_sql_query("""
    SELECT seller, COUNT(*) as deals
    FROM deals
    WHERE seller != 'N/A'
    GROUP BY seller
    ORDER BY deals DESC
    LIMIT 10
""", conn)
print(df.to_string(index=False))

# 4. Age Coverage
print("\n4. AGE COVERAGE:")
print("-"*70)
df = pd.read_sql_query("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN year_built != 'N/A' OR property_age != 'N/A' 
               THEN 1 ELSE 0 END) as with_age
    FROM deals
""", conn)
total = df['total'][0]
with_age = df['with_age'][0]
print(f"Coverage: {with_age}/{total} = {with_age/total*100:.1f}%")

print("\nAge Distribution:")
df = pd.read_sql_query("""
    SELECT 
        CASE 
            WHEN CAST(property_age AS INTEGER) <= 5 THEN '0-5 years'
            WHEN CAST(property_age AS INTEGER) <= 10 THEN '6-10 years'
            WHEN CAST(property_age AS INTEGER) <= 20 THEN '11-20 years'
            WHEN CAST(property_age AS INTEGER) <= 30 THEN '21-30 years'
            ELSE '30+ years'
        END as age_range,
        COUNT(*) as count
    FROM deals
    WHERE property_age != 'N/A'
    GROUP BY age_range
    ORDER BY age_range
""", conn)
print(df.to_string(index=False))

# 5. Unit Calculations
print("\n5. UNIT CALCULATIONS (single properties):")
print("-"*70)
df = pd.read_sql_query("""
    SELECT property_name, total_units, property_count, units_per_property
    FROM deals
    WHERE CAST(property_count AS TEXT) = '1'
    ORDER BY deal_id DESC
    LIMIT 10
""", conn)
print(df.to_string(index=False))

# Sanity Checks
print("\n" + "="*70)
print("SANITY CHECKS:")
print("="*70)

# Check: No brokers in seller field
df = pd.read_sql_query("""
    SELECT COUNT(*) as count
    FROM deals
    WHERE seller IN ('SLIB', 'Blueprint', 'Continuum', 'Helios', 
                     'Helios Healthcare Advisors', 'JLL', 'Zett Group')
""", conn)
if df['count'][0] > 0:
    print(f"WARNING: {df['count'][0]} deals still have brokers as sellers!")
else:
    print(f"OK: No brokers in seller field")

# Check: Units/property for single properties
df = pd.read_sql_query("""
    SELECT COUNT(*) as count
    FROM deals
    WHERE CAST(property_count AS TEXT) = '1'
      AND total_units != 'N/A'
      AND CAST(units_per_property AS TEXT) != CAST(total_units AS TEXT)
""", conn)
if df['count'][0] > 0:
    print(f"WARNING: {df['count'][0]} single properties have wrong units_per_property!")
else:
    print(f"OK: All single properties calculated correctly")

# Summary
print("\n" + "="*70)
print("SUMMARY:")
print("="*70)

cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM deals WHERE property_name != 'N/A'")
prop_names = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM deals WHERE broker != 'N/A'")
brokers = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM deals WHERE year_built != 'N/A' OR property_age != 'N/A'")
ages = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM deals")
total_deals = cursor.fetchone()[0]

print(f"Property Names:  {prop_names}/{total_deals} ({prop_names/total_deals*100:.1f}%)")
print(f"Brokers:         {brokers}/{total_deals} ({brokers/total_deals*100:.1f}%)")
print(f"Age Data:        {ages}/{total_deals} ({ages/total_deals*100:.1f}%)")

conn.close()

print("\n" + "="*70)
print("VERIFICATION COMPLETE!")
print("="*70)
