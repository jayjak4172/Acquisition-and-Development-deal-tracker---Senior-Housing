import sqlite3
import csv

conn = sqlite3.connect('senior_housing_deals.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM deals")
rows = cursor.fetchall()
columns = [d[0] for d in cursor.description]

with open('all_deals.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(columns)
    writer.writerows(rows)

print(f"✓ Exported {len(rows)} deals")
conn.close()