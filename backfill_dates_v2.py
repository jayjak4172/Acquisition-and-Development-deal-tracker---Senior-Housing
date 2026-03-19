"""
backfill_dates_v2.py
- SHB URLs: 재방문해서 meta tag에서 날짜 추출 (로그인 불필요)
- SHN URLs: URL 패턴 /YYYY/MM/DD/ 에서 추출
- 나머지: N/A 유지
- 하루 제한: deals 40개, development 10개
"""

import sqlite3
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime

DAILY_LIMIT = {
    'deals': 40,
    'development_projects': 10,
}

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]

HEADERS = {
    'User-Agent': random.choice(USER_AGENTS),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def parse_date_from_url(url):
    """SHN URL 패턴: /2024/03/15/"""
    match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
    if match:
        return "{}-{}-{}".format(*match.groups())
    return None

def parse_date_from_text(text):
    """본문 텍스트에서 날짜 파싱 (fallback)"""
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

def fetch_shb_date(url):
    """SHB URL 재방문해서 날짜 추출"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Method 1: meta tag
        meta = soup.find('meta', {'property': 'article:published_time'})
        if meta and meta.get('content'):
            return meta['content'][:10]

        # Method 2: <time> tag
        time_tag = soup.find('time')
        if time_tag:
            dt = time_tag.get('datetime') or time_tag.get_text(strip=True)
            if dt:
                # datetime attr: "2026-01-28T..."
                match = re.match(r'(\d{4}-\d{2}-\d{2})', dt)
                if match:
                    return match.group(1)

        # Method 3: byline text
        full_text = soup.get_text()
        return parse_date_from_text(full_text)

    except Exception as e:
        print(f"    fetch 실패: {e}")
        return None

def backfill():
    conn = sqlite3.connect('senior_housing_deals.db')
    cursor = conn.cursor()

    total_updated = 0

    for table, id_col in [('deals', 'deal_id'), ('development_projects', 'project_id')]:
        cursor.execute(f"""
            SELECT {id_col}, source_url, raw_article_text
            FROM {table}
            WHERE article_date IS NULL OR article_date = 'N/A' OR article_date = ''
        """)
        rows = cursor.fetchall()
        limit = DAILY_LIMIT[table]
        total_remaining = len(rows)
        rows = rows[:limit]  # 하루 제한 적용

        print(f"\n{'='*60}")
        print(f"{table}: 전체 미완료 {total_remaining}개 → 오늘 {len(rows)}개 처리")
        print(f"{'='*60}")

        updated = 0
        skipped = 0

        for i, (row_id, url, raw_text) in enumerate(rows, 1):
            # 요청마다 User-Agent 랜덤 교체
            HEADERS['User-Agent'] = random.choice(USER_AGENTS)
            print(f"[{i}/{len(rows)}] id={row_id}")

            date = None

            if url and 'seniorshousingbusiness.com' in url:
                # SHB: 재방문
                print(f"    SHB 재방문...")
                date = fetch_shb_date(url)
                if i < len(rows):
                    sleep_sec = random.uniform(5, 10)
                    print(f"    ⏳ {sleep_sec:.1f}초 대기...")
                    time.sleep(sleep_sec)

            elif url and 'seniorhousingnews.com' in url:
                # SHN: URL 패턴
                date = parse_date_from_url(url)
                if not date:
                    date = parse_date_from_text(raw_text)

            else:
                # 기타: raw_text fallback
                date = parse_date_from_text(raw_text)

            if date:
                cursor.execute(f"""
                    UPDATE {table} SET article_date = ?
                    WHERE {id_col} = ?
                """, (date, row_id))
                conn.commit()
                print(f"    ✓ → {date}")
                updated += 1
            else:
                print(f"    - 날짜 못 찾음")
                skipped += 1

        print(f"\n{table} 결과: {updated}개 업데이트, {skipped}개 실패")
        remaining_after = total_remaining - updated - skipped
        if remaining_after > 0:
            print(f"  → 내일 남은 것: {remaining_after}개")
        total_updated += updated

    conn.close()
    print(f"\n✅ 전체 {total_updated}개 article_date 채움")

if __name__ == "__main__":
    backfill()
