"""
backfill_dates.py
기존 deals/development_projects에서 article_date가 N/A인 것들
raw_article_text + source_url에서 날짜 파싱해서 채움
"""

import sqlite3
import re
from datetime import datetime

def parse_date_from_text(text):
    """본문에서 날짜 텍스트 파싱 (e.g. January 28, 2026)"""
    if not text or text == 'N/A':
        return None
    
    match = re.search(
        r'(January|February|March|April|May|June|July|August'
        r'|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})',
        text
    )
    if match:
        try:
            return datetime.strptime(match.group(0), "%B %d, %Y").strftime("%Y-%m-%d")
        except:
            pass
    return None

def parse_date_from_url(url):
    """URL에서 날짜 파싱 (e.g. /2024/03/15/)"""
    if not url:
        return None
    match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month}-{day}"
    return None

def backfill():
    conn = sqlite3.connect('senior_housing_deals.db')
    cursor = conn.cursor()

    total_updated = 0

    for table, id_col in [('deals', 'deal_id'), ('development_projects', 'project_id')]:
        cursor.execute(f"""
            SELECT {id_col}, source_url, raw_article_text, article_date
            FROM {table}
            WHERE article_date IS NULL OR article_date = 'N/A' OR article_date = ''
        """)
        rows = cursor.fetchall()
        print(f"\n{table}: {len(rows)}개 backfill 대상")

        updated = 0
        for row_id, url, raw_text, current_date in rows:
            # Method 1: 본문 텍스트에서 파싱
            date = parse_date_from_text(raw_text)

            # Method 2: URL에서 파싱 (SHN)
            if not date:
                date = parse_date_from_url(url)

            if date:
                cursor.execute(f"""
                    UPDATE {table} SET article_date = ?
                    WHERE {id_col} = ?
                """, (date, row_id))
                print(f"  ✓ id={row_id}: → {date}  ({url[-50:] if url else 'N/A'})")
                updated += 1
            else:
                print(f"  - id={row_id}: 날짜 못 찾음 ({url[-50:] if url else 'N/A'})")

        conn.commit()
        print(f"  → {updated}/{len(rows)}개 업데이트 완료")
        total_updated += updated

    conn.close()
    print(f"\n✅ 전체 {total_updated}개 article_date 채움")

if __name__ == "__main__":
    backfill()
