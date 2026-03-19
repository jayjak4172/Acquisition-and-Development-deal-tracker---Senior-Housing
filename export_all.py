import sqlite3
import csv
from datetime import datetime

conn = sqlite3.connect('senior_housing_deals.db')
cursor = conn.cursor()

timestamp = datetime.now().strftime('%Y%m%d_%H%M')

# M&A Deals
cursor.execute("SELECT * FROM deals")
rows = cursor.fetchall()
columns = [d[0] for d in cursor.description]

filename_deals = f'ma_deals_{timestamp}.csv'
with open(filename_deals, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(columns)
    writer.writerows(rows)
print(f"✓ M&A Deals: {len(rows)}개 → {filename_deals}")

# Development Projects
cursor.execute("SELECT * FROM development_projects")
rows = cursor.fetchall()
columns = [d[0] for d in cursor.description]

filename_dev = f'development_{timestamp}.csv'
with open(filename_dev, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(columns)
    writer.writerows(rows)
print(f"✓ Development: {len(rows)}개 → {filename_dev}")

conn.close()
print(f"\n✅ 완료! Excel에서 열어봐.")
