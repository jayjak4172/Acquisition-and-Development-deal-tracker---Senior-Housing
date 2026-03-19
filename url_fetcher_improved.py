"""
URL Fetcher - Improved Version
- Session management
- Better error handling
- URL normalization
- Daily limit (default 50 articles)
"""

import requests
from bs4 import BeautifulSoup
import time
from database import DealDatabase
from urllib.parse import urlsplit, urlunsplit

# 하루 수집 제한
DEFAULT_DAILY_LIMIT = 50

def normalize_url(url):
    """
    URL 정규화 (중복 방지)
    
    - trailing slash 제거
    - 소문자 변환
    - fragment 제거
    """
    try:
        parts = urlsplit(url)
        # https로 통일, 소문자, trailing slash 제거, fragment 제거
        clean_path = parts.path.rstrip('/')
        normalized = urlunsplit((
            'https',
            parts.netloc.lower(),
            clean_path,
            '',  # query string 유지하려면 parts.query
            ''   # fragment 제거
        ))
        return normalized
    except:
        return url

def create_session():
    """Session 생성 및 설정"""
    session = requests.Session()
    
    # Headers 설정
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    
    return session

def fetch_category_urls_range(session, base_url, start_page, end_page):
    """
    페이지 범위에서 URLs 수집 (개선된 에러 처리)
    
    Args:
        session: requests.Session object
        base_url: Category URL
        start_page: 시작 페이지
        end_page: 끝 페이지
    
    Returns:
        List of normalized article URLs
    """
    
    all_urls = []
    total_pages = end_page - start_page + 1
    errors = {'timeout': 0, '404': 0, '403': 0, 'other': 0}
    
    for page_num in range(start_page, end_page + 1):
        relative_num = page_num - start_page + 1
        
        # Build URL
        if page_num == 1:
            page_url = base_url
        else:
            page_url = f"{base_url}page/{page_num}/"
        
        print(f"  [Page {page_num}] ({relative_num}/{total_pages}) ", end="")
        
        try:
            # Request with timeout
            response = session.get(page_url, timeout=15)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.find_all('article')
            
            # Extract URLs
            page_urls = []
            for article in articles:
                title_link = article.find('h2')
                if title_link:
                    link = title_link.find('a')
                    if link and link.get('href'):
                        raw_url = link['href']
                        # Normalize URL
                        normalized_url = normalize_url(raw_url)
                        page_urls.append(normalized_url)
            
            all_urls.extend(page_urls)
            print(f"✓ {len(page_urls)} articles")
            
            # Rate limiting
            if page_num < end_page:
                time.sleep(1.5)
        
        except requests.Timeout:
            print("✗ Timeout")
            errors['timeout'] += 1
            
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                print("✗ 404 Not Found")
                errors['404'] += 1
            elif e.response.status_code == 403:
                print("✗ 403 Blocked")
                errors['403'] += 1
            else:
                print(f"✗ HTTP {e.response.status_code}")
                errors['other'] += 1
        
        except Exception as e:
            print(f"✗ Error: {str(e)[:40]}")
            errors['other'] += 1
    
    # Remove duplicates (after normalization)
    all_urls = list(dict.fromkeys(all_urls))
    
    # Show errors if any
    if sum(errors.values()) > 0:
        print(f"\n  ⚠️  Errors: Timeout={errors['timeout']}, 404={errors['404']}, 403={errors['403']}, Other={errors['other']}")
    
    return all_urls

def fetch_shb_urls_range(acq_start, acq_end, dev_start, dev_end, daily_limit=DEFAULT_DAILY_LIMIT):
    """
    SHB에서 URLs 수집 (개선 버전)
    
    Args:
        acq_start: Acquisitions 시작 페이지
        acq_end: Acquisitions 끝 페이지
        dev_start: Development 시작 페이지
        dev_end: Development 끝 페이지
        daily_limit: 하루 최대 수집 개수 (기본 50)
    """
    
    # Session 생성
    session = create_session()
    
    print("\n" + "="*70)
    print("🔍 SHB URL FETCHER - IMPROVED VERSION")
    print("="*70 + "\n")
    
    print("⚙️  Settings:")
    print(f"   Acquisitions: Pages {acq_start}-{acq_end} ({acq_end-acq_start+1} pages)")
    print(f"   Development:  Pages {dev_start}-{dev_end} ({dev_end-dev_start+1} pages)")
    print(f"   Daily limit:  {daily_limit} articles\n")
    
    # Fetch acquisitions
    acquisition_urls = []
    if acq_end > 0:
        print("📊 ACQUISITIONS:")
        print("-"*70)
        acquisition_urls = fetch_category_urls_range(
            session,
            "https://seniorshousingbusiness.com/category/acquisitions/",
            acq_start,
            acq_end
        )
    
    # Fetch development
    dev_urls = []
    if dev_end > 0:
        print("\n🏗️  DEVELOPMENT PROJECTS:")
        print("-"*70)
        dev_urls = fetch_category_urls_range(
            session,
            "https://seniorshousingbusiness.com/category/development/",
            dev_start,
            dev_end
        )
    
    # Combine
    all_urls = acquisition_urls + dev_urls
    
    # Filter existing
    db = DealDatabase()
    new_urls = [url for url in all_urls if not db.url_exists(url)]
    
    # Apply daily limit
    if len(new_urls) > daily_limit:
        print(f"\n⚠️  Found {len(new_urls)} new URLs, limiting to {daily_limit}")
        new_urls = new_urls[:daily_limit]
    
    # Separate back into categories
    new_acquisitions = [url for url in new_urls if url in acquisition_urls]
    new_dev = [url for url in new_urls if url in dev_urls]
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    if acq_end > 0:
        print(f"\n📊 ACQUISITIONS (Pages {acq_start}-{acq_end}):")
        print(f"   Found: {len(acquisition_urls)}")
        print(f"   Already in DB: {len(acquisition_urls) - len(new_acquisitions)}")
        print(f"   New: {len(new_acquisitions)}")
    
    if dev_end > 0:
        print(f"\n🏗️  DEVELOPMENT (Pages {dev_start}-{dev_end}):")
        print(f"   Found: {len(dev_urls)}")
        print(f"   Already in DB: {len(dev_urls) - len(new_dev)}")
        print(f"   New: {len(new_dev)}")
    
    total_new = len(new_acquisitions) + len(new_dev)
    print(f"\n✓ Total new URLs: {total_new}")
    
    if total_new < daily_limit and total_new > 0:
        print(f"  (Under daily limit of {daily_limit})")
    elif total_new == daily_limit:
        print(f"  (At daily limit of {daily_limit})")
    
    # Close session
    session.close()
    
    return {
        'acquisitions': new_acquisitions,
        'development': new_dev
    }

def save_to_urls_txt(urls, append=True):
    """URLs를 urls.txt에 저장"""
    
    mode = 'a' if append else 'w'
    
    with open('urls.txt', mode, encoding='utf-8') as f:
        if append:
            f.write(f"\n# Auto-fetched - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        if urls['acquisitions']:
            f.write("# Acquisitions\n")
            for url in urls['acquisitions']:
                f.write(f"{url}\n")
        
        if urls['development']:
            f.write("\n# Development Projects\n")
            for url in urls['development']:
                f.write(f"{url}\n")
    
    total = len(urls['acquisitions']) + len(urls['development'])
    print(f"\n📝 Saved {total} URLs to urls.txt")

if __name__ == "__main__":
    import sys
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print("""
SHB URL FETCHER - IMPROVED VERSION

FEATURES:
  ✓ Session management (faster, more stable)
  ✓ Better error handling (timeout, 404, 403)
  ✓ URL normalization (duplicate prevention)
  ✓ Daily limit (default 50 articles)

USAGE:
  python url_fetcher_improved.py <acq_start> <acq_end> <dev_start> <dev_end> [--limit N]

EXAMPLES:
  # Default (50 articles limit)
  python url_fetcher_improved.py 1 5 1 3
  
  # Custom limit (100 articles)
  python url_fetcher_improved.py 1 10 1 5 --limit 100
  
  # No limit
  python url_fetcher_improved.py 1 20 1 10 --limit 999

DAILY PLAN (50 articles/day):
  Day 1: python url_fetcher_improved.py 1 5 1 3
  Day 2: python url_fetcher_improved.py 6 10 4 6
  Day 3: python url_fetcher_improved.py 11 15 7 9
  ...

ARGUMENTS:
  acq_start   Acquisitions 시작 페이지
  acq_end     Acquisitions 끝 페이지
  dev_start   Development 시작 페이지
  dev_end     Development 끝 페이지
  --limit N   하루 최대 수집 개수 (기본 50)
""")
        sys.exit(0)
    
    # Parse arguments
    if len(sys.argv) < 5:
        print("ERROR: Need 4 arguments!")
        print("Usage: python url_fetcher_improved.py <acq_start> <acq_end> <dev_start> <dev_end>")
        print("\nRun with --help for more info")
        sys.exit(1)
    
    try:
        acq_start = int(sys.argv[1])
        acq_end = int(sys.argv[2])
        dev_start = int(sys.argv[3])
        dev_end = int(sys.argv[4])
    except ValueError:
        print("ERROR: First 4 arguments must be numbers!")
        sys.exit(1)
    
    # Parse limit
    daily_limit = DEFAULT_DAILY_LIMIT
    if '--limit' in sys.argv:
        idx = sys.argv.index('--limit')
        if idx + 1 < len(sys.argv):
            try:
                daily_limit = int(sys.argv[idx + 1])
            except ValueError:
                print(f"ERROR: --limit value must be a number")
                sys.exit(1)
    
    # Validate
    if acq_end > 0 and acq_start > acq_end:
        print("ERROR: acq_start must be <= acq_end")
        sys.exit(1)
    
    if dev_end > 0 and dev_start > dev_end:
        print("ERROR: dev_start must be <= dev_end")
        sys.exit(1)
    
    # Fetch
    urls = fetch_shb_urls_range(acq_start, acq_end, dev_start, dev_end, daily_limit)
    
    # Save if found
    total_new = len(urls['acquisitions']) + len(urls['development'])
    
    if total_new > 0:
        save_to_urls_txt(urls, append=True)
        
        print("\n" + "="*70)
        print("NEXT STEPS:")
        print("="*70)
        print("\n1. (Optional) Add SHN URLs manually:")
        print("   notepad urls.txt")
        print("\n2. Run scraper:")
        print("   python scraper.py")
        print("\n" + "="*70 + "\n")
    else:
        print("\n✓ No new URLs found!")
        print("   All articles in this range are already in the database.\n")
