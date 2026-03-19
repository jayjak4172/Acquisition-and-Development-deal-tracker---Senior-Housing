# migrate_location.py
# 기존 DB에 metro/state 컬럼 추가하고 GPT로 region 파싱해서 채움

import sqlite3
import openai
import json
import os

openai.api_key = os.environ["OPENAI_API_KEY"]

def migrate():
    conn = sqlite3.connect("senior_housing_deals.db")
    cursor = conn.cursor()

    # 1. 컬럼 추가 (이미 있으면 에러 무시)
    for table in ["deals", "development_projects"]:
        for col in ["metro TEXT", "state TEXT"]:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col}")
                print(f"✓ {table}: {col} 추가됨")
            except sqlite3.OperationalError:
                print(f"  {table}: {col.split()[0]} 이미 존재")

    conn.commit()

    # 2. 기존 region 값 → metro/state 파싱 (GPT)
    for table, id_col in [("deals", "deal_id"), ("development_projects", "project_id")]:
        cursor.execute(f"""
            SELECT {id_col}, region, raw_article_text
            FROM {table}
            WHERE (metro IS NULL OR metro = '') 
            AND (region IS NOT NULL AND region != '')
        """)
        rows = cursor.fetchall()
        print(f"\n{table}: {len(rows)}개 backfill 예정")

        for row_id, region, raw_text in rows:
            # region 텍스트 + 원문에서 metro/state 추출
            context = region or ""
            if raw_text:
                context += "\n\n" + raw_text[:1000]  # 원문 앞부분만

            try:
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{
                        "role": "user",
                        "content": f"""From this location context about a senior housing deal, extract:
- metro: The metro area (e.g. "Atlanta", "Phoenix", "New York", "Chicago")
- state: Two-letter US state code (e.g. "GA", "AZ", "NY", "IL")

If multiple locations, use the primary one.
If unknown, use null.

Location context: {context}

Respond ONLY with JSON: {{"metro": "...", "state": "..."}}"""
                    }],
                    max_tokens=60,
                    temperature=0
                )
                result = json.loads(response.choices[0].message.content.strip())
                metro = result.get("metro") or ""
                state = result.get("state") or ""
            except Exception as e:
                print(f"  GPT 오류 (id={row_id}): {e}")
                metro, state = "", ""

            cursor.execute(f"""
                UPDATE {table} SET metro=?, state=?
                WHERE {id_col}=?
            """, (metro, state, row_id))
            print(f"  {row_id}: region='{region}' → metro='{metro}', state='{state}'")

    conn.commit()
    conn.close()
    print("\n✅ Migration 완료!")

if __name__ == "__main__":
    migrate()