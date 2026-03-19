# URL FETCHER - 개선 버전 가이드
## 하루 50개 자동 제한 + 안정성 개선

---

## ✅ 개선 사항:

### 1. Session 관리
```python
session = requests.Session()
# → 연결 재사용, 더 빠르고 안정적
```

### 2. 더 나은 에러 처리
```python
- Timeout 감지
- 404 Not Found 처리
- 403 Blocked 감지
- 에러 개수 표시
```

### 3. URL 정규화
```python
https://example.com/article/  ← 이것과
https://example.com/article   ← 이것을 같게 처리
# → 중복 방지
```

### 4. 하루 제한 (자동!)
```python
# 자동으로 50개만 수집
# 더 필요하면 --limit 100
```

---

## 🚀 사용법:

### 기본 (하루 50개 자동 제한):
```bash
python url_fetcher_improved.py 1 5 1 3
```

**결과:**
- 페이지는 많이 스캔해도
- 최대 50개 URL만 저장
- 자동 제한!

---

### 더 많이 수집하고 싶으면:
```bash
python url_fetcher_improved.py 1 10 1 5 --limit 100
```

**결과:**
- 최대 100개 수집

---

### 제한 없이:
```bash
python url_fetcher_improved.py 1 20 1 10 --limit 999
```

---

## 📊 출력 예시:

```
======================================================================
🔍 SHB URL FETCHER - IMPROVED VERSION
======================================================================

⚙️  Settings:
   Acquisitions: Pages 1-5 (5 pages)
   Development:  Pages 1-3 (3 pages)
   Daily limit:  50 articles

📊 ACQUISITIONS:
----------------------------------------------------------------------
  [Page 1] (1/5) ✓ 10 articles
  [Page 2] (2/5) ✓ 10 articles
  [Page 3] (3/5) ✓ 10 articles
  [Page 4] (4/5) ✓ 10 articles
  [Page 5] (5/5) ✓ 9 articles

🏗️  DEVELOPMENT PROJECTS:
----------------------------------------------------------------------
  [Page 1] (1/3) ✓ 8 articles
  [Page 2] (2/3) ✓ 8 articles
  [Page 3] (3/3) ✓ 7 articles

⚠️  Found 72 new URLs, limiting to 50  ← 자동 제한!

======================================================================
SUMMARY
======================================================================

📊 ACQUISITIONS (Pages 1-5):
   Found: 49
   Already in DB: 0
   New: 42

🏗️  DEVELOPMENT (Pages 1-3):
   Found: 23
   Already in DB: 0
   New: 8

✓ Total new URLs: 50  ← 딱 50개!
  (At daily limit of 50)

📝 Saved 50 URLs to urls.txt
```

---

## 🎯 매일 루틴:

```bash
# Day 1 (50개)
python url_fetcher_improved.py 1 5 1 3
python scraper.py

# Day 2 (50개)
python url_fetcher_improved.py 6 10 4 6
python scraper.py

# Day 3 (50개)
python url_fetcher_improved.py 11 15 7 9
python scraper.py
```

**페이지 많이 지정해도 자동으로 50개만!** ✅

---

## 💡 왜 이게 좋은가?

### 기존 (url_fetcher_range.py):
```bash
python url_fetcher_range.py 1 5 1 3
# → 페이지 5개 스캔
# → 50개 URL 수집
# → 50개 전부 저장
```

**문제:** 
- 페이지 수를 정확히 계산해야 함
- 50개 맞추기 어려움

---

### 개선 (url_fetcher_improved.py):
```bash
python url_fetcher_improved.py 1 10 1 5
# → 페이지 15개 스캔
# → 150개 URL 발견
# → **자동으로 50개만 저장!** ✅
```

**장점:**
- 페이지 수 걱정 없음
- 항상 정확히 50개
- 간단!

---

## 🔍 에러 표시:

**에러가 나면:**
```
  [Page 10] (10/10) ✗ 404 Not Found
  [Page 11] (11/11) ✗ Timeout
  [Page 12] (12/12) ✓ 10 articles

  ⚠️  Errors: Timeout=1, 404=1, 403=0, Other=0
```

**알 수 있는 것:**
- 어떤 에러인지
- 몇 개 에러났는지
- 계속 진행할지 판단 가능

---

## 📋 비교:

| 기능 | 기존 | 개선 |
|------|------|------|
| Session | ❌ | ✅ |
| 에러 구분 | ❌ | ✅ (Timeout, 404, 403) |
| URL 정규화 | ❌ | ✅ |
| 하루 제한 | ❌ 수동 | ✅ 자동 (50개) |
| 안정성 | 보통 | 높음 |

---

## ✅ 체크리스트:

```
[ ] url_fetcher_improved.py 다운로드
[ ] 테스트 실행
[ ] 결과 확인 (50개 제한됨?)
[ ] 매일 사용 시작
```

---

## 🎯 Quick Start:

```bash
# 1. 다운로드 완료

# 2. 테스트
python url_fetcher_improved.py 1 5 1 3

# 3. 확인
notepad urls.txt

# 4. Scrape
python scraper.py

# 5. 매일 반복!
```

---

**이제 페이지 수 걱정 없이 매일 정확히 50개씩!** 🎉
