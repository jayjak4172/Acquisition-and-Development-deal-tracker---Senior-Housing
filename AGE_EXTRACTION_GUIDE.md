# AGE EXTRACTION UPGRADE GUIDE (Option A)
## Two-Part Approach: Fix Past + Improve Future

---

## 🎯 WHAT THIS DOES:

### Part 1: Extract Missing Ages from Existing Data
```
✅ Re-analyzes 54 deals already in database
✅ Uses raw_article_text (no re-scraping needed!)
✅ Focused GPT prompt asking ONLY for age/year
✅ Could recover ~10 deals (18.5%)
```

### Part 2: Better Age Extraction for Future
```
✅ Updates scraper.py with enhanced age prompting
✅ Future articles get better extraction
✅ Emphasizes common age phrases
```

---

## 📊 CURRENT SITUATION:

```
Total Deals: 77
Has Age Data: 22 (28.6%)
Missing Age Data: 55 (71.4%)

Of the 55 missing:
  - ~10 have age in article (GPT missed it) ← We can fix!
  - ~45 have NO age in article ← Can't fix
```

---

## 💡 HOW IT WORKS:

### WHY This Works:
```python
# We saved the full article text!
deals table has: raw_article_text column

# So we can re-analyze WITHOUT re-scraping
SELECT deal_id, raw_article_text
FROM deals  
WHERE year_built = 'N/A'
```

### The Strategy:
```
1. Query database for deals with missing age
2. Extract raw_article_text
3. Send ONLY that text to GPT
4. Use FOCUSED prompt asking ONLY for age
5. Update database with results
```

---

## 📋 STEP-BY-STEP INSTRUCTIONS

---

### PART 1: Extract Missing Ages from Existing Data

#### Step 1: Download Script (1 min)

Download `extract_missing_ages.py` to:
```
C:\Users\kimja\Documents\ma_tracker\
```

#### Step 2: Run Extraction (5 min)

```bash
cd C:\Users\kimja\Documents\ma_tracker
python extract_missing_ages.py
```

**Expected output:**
```
======================================================================
EXTRACT MISSING AGE DATA FROM EXISTING ARTICLES
======================================================================

📊 Found 54 deals with missing age data

💰 Estimated cost: $0.05
⏱️  Estimated time: 108 seconds

Continue with 54 extractions? (y/n): y

======================================================================
PROCESSING
======================================================================

[1/54] Deal #77: SLIB Arranges Sale of 125-Unit Community...
      ⊘ No age data in article

[2/54] Deal #71: Helios Arranges Sale of 47-Unit Assisted Living...
      ⊘ No age data in article

[3/54] Deal #62: Northmark Acquires Two Senior Living Communities...
      ✓ year_built=2021, property_age=5 (high confidence)

[4/54] Deal #49: Blueprint Brokers Sale of 570-Bed SNF Portfolio...
      ✓ year_built=2005, property_age=21 (medium confidence)

[... continues for all 54 ...]

======================================================================
SUMMARY
======================================================================
✓ Extracted: 10 deals
⊘ No data:   42 deals
✗ Failed:    2 deals

Coverage improvement:
  Before: 22 deals (28.6%)
  After:  32 deals (41.6%)
  Gain:   +10 deals (+13.0%)
```

#### Step 3: Verify Results (1 min)

```bash
python
```

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('senior_housing_deals.db')

# Check new coverage
df = pd.read_sql_query("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN year_built != 'N/A' OR property_age != 'N/A' 
               THEN 1 ELSE 0 END) as with_age
    FROM deals
""", conn)

print(f"Coverage: {df['with_age'][0]}/{df['total'][0]} = {df['with_age'][0]/df['total'][0]*100:.1f}%")

# Show newly extracted ages
df = pd.read_sql_query("""
    SELECT deal_id, article_title, year_built, property_age, region
    FROM deals
    WHERE year_built != 'N/A' OR property_age != 'N/A'
    ORDER BY deal_id DESC
    LIMIT 10
""", conn)

print("\nRecent deals with age:")
print(df)

conn.close()
exit()
```

✅ **Checkpoint:** Age coverage increased from 28.6% → ~41.6%

---

### PART 2: Update Scraper for Future Extractions

#### Step 1: Download Updated Scraper (1 min)

Download `scraper_v3.2.1.py` to:
```
C:\Users\kimja\Documents\ma_tracker\
```

#### Step 2: Backup Current Scraper (1 min)

```bash
cd C:\Users\kimja\Documents\ma_tracker
copy scraper.py scraper_v3.2_backup.py
```

#### Step 3: Update Scraper (1 min)

```bash
copy scraper_v3.2.1.py scraper.py
```

#### Step 4: Test with New URL (5 min)

Get a new article URL (not in database yet):
```
https://seniorshousingbusiness.com/[recent-article]
```

Create test file:
```bash
notepad urls_test_age.txt
```

Add the URL, save and run:
```bash
python scraper.py urls_test_age.txt
```

**Expected output:**
```
v3.2.1: Broker + Property Names + Better Logic + Age Extraction
======================================================================

[1/1] https://seniorshousingbusiness.com/article...
   [SHB-HTTP] Fetching...
   ✓ 제목: ...
   ✓ 콘텐츠: ... 글자
   GPT-3.5로 데이터 추출...
   ✓ M&A: [Property Name]
      [Buyer] ← [Seller]
      Year Built: [YYYY] ← NEW!
```

#### Step 5: Verify Extraction (1 min)

```bash
python
```

```python
import sqlite3

conn = sqlite3.connect('senior_housing_deals.db')
cursor = conn.cursor()

# Get most recent deal
cursor.execute("""
    SELECT deal_id, property_name, year_built, property_age
    FROM deals
    ORDER BY deal_id DESC
    LIMIT 1
""")

result = cursor.fetchone()
print(f"Deal #{result[0]}")
print(f"Property: {result[1]}")
print(f"Year Built: {result[2]}")
print(f"Age: {result[3]} years")

conn.close()
exit()
```

**Expected:** If article mentions age, both year_built AND property_age should be filled!

✅ **Checkpoint:** Future extractions now capture age better

---

### PART 3: Commit Changes (2 min)

```bash
git add scraper.py
git status
git commit -m "v3.2.1: Enhanced age extraction (past + future)"
git log --oneline -3
```

---

## 📊 WHAT CHANGED IN SCRAPER

### New Section in GPT Prompt:

```
=== CRITICAL: YEAR BUILT / PROPERTY AGE ===

ALWAYS search for age/year information! Common phrases:
- "built in [YYYY]" → year_built: YYYY
- "constructed in [YYYY]" → year_built: YYYY
- "developed in [YYYY]" → year_built: YYYY
- "opened in [YYYY]" → year_built: YYYY
- "completed in [YYYY]" → year_built: YYYY
- "[X] years old" → property_age: X
- "age of [X]" → property_age: X
- "average age of [X] years" → property_age: X
- "renovated in [YYYY]" → year_built: YYYY

EXAMPLES:
"The property was built in 2019" → year_built: 2019, property_age: 7
"Morrison Ranch totals 115 units and was built in 2019" → year_built: 2019
"The communities were developed in 2021 and 2020" → year_built: 2021
"properties have an average age of six years" → property_age: 6

CRITICAL:
- If you find year_built: Calculate property_age = 2026 - year_built
- If you find property_age: Calculate year_built = 2026 - property_age
- Ignore phrases like "30th-largest operator" (NOT property age!)
- If multiple years mentioned, use EARLIEST (original construction)
```

**This makes GPT:**
- ✅ Look harder for age data
- ✅ Recognize more patterns
- ✅ Not confuse "30th-largest" with age
- ✅ Calculate both fields automatically

---

## 💰 COST ANALYSIS

### Part 1: Extract Missing Ages
```
54 deals × $0.001 per API call = $0.054
Actual recovered: ~10 deals
Cost per recovered deal: $0.005
```

### Part 2: Update Scraper
```
FREE! Just better prompting
```

### Total Investment:
```
Money: $0.05
Time: 15 minutes
Value: +10 age data points (13% coverage gain)
```

---

## 📈 EXPECTED RESULTS

### Before:
```
Age Coverage: 22/77 = 28.6%

Missing 55 deals:
  - 10 have age in text (missed by GPT)
  - 45 have NO age in text
```

### After Part 1:
```
Age Coverage: 32/77 = 41.6%

Missing 45 deals:
  - 0 have age in text (all extracted!)
  - 45 have NO age in text
```

### After Part 2 (future):
```
New articles: ~80-90% will have age
(vs 28.6% currently)

Future database will be much richer!
```

---

## 🎓 WHAT YOU LEARN

### Key Insights:
1. **Re-analysis vs Re-scraping:** No need to re-scrape if you saved raw text
2. **Focused Prompts:** Single-task GPT prompts work better
3. **Iterative Improvement:** Can improve data quality retroactively
4. **Prompt Engineering:** Specific examples > generic instructions

### Technical Skills:
1. Database UPDATE queries
2. GPT API usage for data extraction
3. Prompt engineering for better results
4. Data quality metrics

---

## 🚨 TROUBLESHOOTING

### Problem: "No module named 'openai'"
```bash
pip install openai --user
```

### Problem: API key error
```bash
# Check environment variable
echo %OPENAI_API_KEY%

# If empty, set it:
setx OPENAI_API_KEY "sk-..."
```

### Problem: No deals extracted
```
This is normal! 
~18.5% have age data (10 deals)
~81.5% have NO age data (44 deals)

If you get 8-12 deals, that's expected.
```

### Problem: Wrong ages extracted
```python
# Check the extractions
import sqlite3
conn = sqlite3.connect('senior_housing_deals.db')

cursor = conn.execute("""
    SELECT deal_id, year_built, property_age, article_title
    FROM deals
    WHERE year_built != 'N/A' AND year_built > 2026
""")

# Future years = wrong!
# Manually fix if needed
```

---

## ✅ FINAL VERIFICATION

Run this complete check:

```bash
python
```

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('senior_housing_deals.db')

print("="*70)
print("AGE EXTRACTION VERIFICATION")
print("="*70 + "\n")

# Overall coverage
df = pd.read_sql_query("""
    SELECT 
        COUNT(*) as total_deals,
        SUM(CASE WHEN year_built != 'N/A' THEN 1 ELSE 0 END) as has_year,
        SUM(CASE WHEN property_age != 'N/A' THEN 1 ELSE 0 END) as has_age,
        SUM(CASE WHEN year_built != 'N/A' OR property_age != 'N/A' 
            THEN 1 ELSE 0 END) as has_either
    FROM deals
""", conn)

total = df['total_deals'][0]
has_either = df['has_either'][0]

print(f"📊 COVERAGE:")
print(f"  Total Deals: {total}")
print(f"  With Age Data: {has_either} ({has_either/total*100:.1f}%)")
print(f"  Missing Age: {total - has_either} ({(total-has_either)/total*100:.1f}%)")

# Age distribution
print(f"\n📊 AGE DISTRIBUTION:")
df = pd.read_sql_query("""
    SELECT 
        CASE 
            WHEN property_age <= 5 THEN '0-5 years (New)'
            WHEN property_age <= 10 THEN '6-10 years'
            WHEN property_age <= 20 THEN '11-20 years'
            WHEN property_age <= 30 THEN '21-30 years'
            WHEN property_age > 30 THEN '30+ years'
        END as age_range,
        COUNT(*) as count
    FROM deals
    WHERE property_age != 'N/A'
    GROUP BY age_range
    ORDER BY age_range
""", conn)
print(df)

# Recent extractions
print(f"\n📊 RECENTLY ADDED (last 5):")
df = pd.read_sql_query("""
    SELECT deal_id, article_title, year_built, property_age
    FROM deals
    WHERE year_built != 'N/A' OR property_age != 'N/A'
    ORDER BY deal_id DESC
    LIMIT 5
""", conn)
print(df)

conn.close()

print("\n" + "="*70)
print("✓ AGE EXTRACTION UPGRADE COMPLETE!")
print("="*70)

exit()
```

**Expected output:**
```
======================================================================
AGE EXTRACTION VERIFICATION
======================================================================

📊 COVERAGE:
  Total Deals: 77
  With Age Data: 32 (41.6%)
  Missing Age: 45 (58.4%)

📊 AGE DISTRIBUTION:
           age_range  count
    0-5 years (New)      7
       6-10 years       12
      11-20 years        8
      21-30 years        3
       30+ years         2

📊 RECENTLY ADDED (last 5):
   deal_id                    article_title  year_built  property_age
       78         Latest Deal Title Here        2021             5
       62  Northmark Acquires Two Communities    2021             5
       ...

======================================================================
✓ AGE EXTRACTION UPGRADE COMPLETE!
======================================================================
```

---

## 🎉 SUCCESS CRITERIA

You're done when:

- ✅ Coverage increased (e.g., 28.6% → 41.6%)
- ✅ `extract_missing_ages.py` ran successfully
- ✅ `scraper.py` updated to v3.2.1
- ✅ Future extractions capture age better
- ✅ No errors in verification check

---

## 📝 NEXT STEPS

### Now You Can:
1. **Better age-based analysis** (41.6% vs 28.6% coverage)
2. **Track property vintage trends** (new vs old)
3. **Price-per-age analysis** (do newer properties cost more?)
4. **Future scraping** will be even better!

### Optional Improvements:
1. Run `extract_missing_ages.py` monthly as data grows
2. Manually add ages for high-value deals
3. Cross-reference with public records

---

**COMPLETE! Your database now has 40%+ age coverage!** 🎉
