"""
M&A Deal Scraper - v3.2.1
IMPROVEMENTS:
- Distinguishes broker from seller/buyer
- Extracts property/community name
- Improved single-property detection
- Better GPT prompts to avoid confusion
- ENHANCED: Better year_built/property_age extraction
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from openai import OpenAI
import json
import time
import os
import pickle
from database import DealDatabase
import re
from entity_mapping import normalize_entity_name
from datetime import datetime

# NEW: HTTP request libraries
import requests
from bs4 import BeautifulSoup

CURRENT_YEAR = 2026  # Update annually

def setup_browser():
    """Setup Chrome browser for Selenium"""
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--start-maximized')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    return driver

def save_cookies(driver, filepath='cookies.pkl'):
    """Save cookies to file"""
    cookies = driver.get_cookies()
    with open(filepath, 'wb') as f:
        pickle.dump(cookies, f)
    print(f"   ✓ 쿠키 저장 완료")

def load_cookies(driver, filepath='cookies.pkl'):
    """Load cookies from file"""
    try:
        with open(filepath, 'rb') as f:
            cookies = pickle.load(f)
        driver.get("https://seniorhousingnews.com")
        time.sleep(2)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                pass
        print(f"   ✓ 쿠키 로드 완료")
        return True
    except FileNotFoundError:
        print(f"   ℹ 저장된 쿠키 없음")
        return False

def manual_login_and_save(driver):
    """Let user log in manually, then save cookies"""
    print("\n" + "="*70)
    print("수동 로그인 필요")
    print("="*70)
    print("\n지금 열린 Chrome 창에서:")
    print("1. Senior Housing News에 로그인하세요")
    print("2. 로그인 완료 후 아무 기사나 하나 열어보세요")
    print("3. 완료되면 여기 돌아와서 Enter를 누르세요\n")
    
    input("로그인 완료 후 Enter... ")
    save_cookies(driver)
    print("\n✓ 쿠키 저장! 다음부터는 자동 로그인!\n")

def extract_article_date(content, url):
    """Extract article date from URL"""
    url_date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
    if url_date_match:
        year, month, day = url_date_match.groups()
        return f"{year}-{month}-{day}"
    return "N/A"

def fetch_shn_with_selenium(url, first_run=False):
    """Fetch from Senior Housing News using Selenium (requires login)"""
    print(f"   [SHN-Selenium] Chrome 열기: {url[:50]}...")
    
    driver = setup_browser()
    
    try:
        cookies_loaded = load_cookies(driver)
        
        if first_run or not cookies_loaded:
            driver.get("https://seniorhousingnews.com")
            manual_login_and_save(driver)
        
        print(f"   → 기사 페이지로 이동...")
        driver.get(url)
        time.sleep(4)
        
        # Get title
        try:
            title_element = driver.find_element(By.TAG_NAME, 'h1')
            title = title_element.text or driver.title
        except:
            title = driver.title
        
        print(f"   ✓ 제목: {title[:50]}...")
        
        # Get content
        try:
            content_element = driver.find_element(By.CLASS_NAME, 'entry-content')
            content = content_element.text
        except:
            try:
                content_element = driver.find_element(By.TAG_NAME, 'article')
                content = content_element.text
            except:
                content = driver.find_element(By.TAG_NAME, 'body').text
        
        print(f"   ✓ 콘텐츠: {len(content)} 글자")
        
        article_date = extract_article_date(content, url)
        
        driver.quit()
        
        return {
            'title': title,
            'content': content,
            'url': url,
            'article_date': article_date
        }
    
    except Exception as e:
        try:
            driver.quit()
        except:
            pass
        raise Exception(f"SHN fetch failed: {str(e)}")

def fetch_shb_with_requests(url):
    """Fetch from Seniors Housing Business using HTTP requests (faster, safer!)"""
    print(f"   [SHB-HTTP] Fetching: {url[:50]}...")
    
    # Headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        # Make HTTP request
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get title
        try:
            title_element = soup.find('h1')
            title = title_element.get_text(strip=True) if title_element else "N/A"
        except:
            title = "N/A"
        
        print(f"   ✓ 제목: {title[:50]}...")
        
        # Get content
        try:
            content_element = soup.find('div', class_='entry-content')
            if content_element:
                content = content_element.get_text(separator='\n', strip=True)
            else:
                article_element = soup.find('article')
                if article_element:
                    content = article_element.get_text(separator='\n', strip=True)
                else:
                    content = "N/A"
        except:
            content = "N/A"
        
        print(f"   ✓ 콘텐츠: {len(content)} 글자")
        
        article_date = extract_article_date(content, url)
        
        return {
            'title': title,
            'content': content,
            'url': url,
            'article_date': article_date
        }
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"SHB HTTP fetch failed: {str(e)}")
    except Exception as e:
        raise Exception(f"SHB parsing failed: {str(e)}")

def fetch_article(url, first_run=False):
    """Route to appropriate fetcher based on URL"""
    if 'seniorshousingbusiness.com' in url:
        return fetch_shb_with_requests(url)
    else:
        return fetch_shn_with_selenium(url, first_run)

def calculate_age_and_year(year_built, property_age, announcement_date=None, article_date=None):
    """Calculate missing field from the one provided"""
    reference_year = CURRENT_YEAR
    
    if announcement_date and announcement_date != 'N/A':
        try:
            reference_year = int(announcement_date.split('-')[0])
        except:
            pass
    elif article_date and article_date != 'N/A':
        try:
            reference_year = int(article_date.split('-')[0])
        except:
            reference_year = CURRENT_YEAR
    
    if year_built and year_built != 'N/A':
        try:
            year_int = int(year_built)
            calc_age = reference_year - year_int
            return year_int, calc_age
        except:
            pass
    
    if property_age and property_age != 'N/A':
        try:
            age_int = int(property_age)
            calc_year = reference_year - age_int
            return calc_year, age_int
        except:
            pass
    
    return 'N/A', 'N/A'

def extract_deal_data(article):
    """Extract M&A deal or Development project data"""
    print(f"   GPT-3.5로 데이터 추출...")
    
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # ENHANCED PROMPT with broker detection and property name
    prompt = f"""Extract M&A deal OR Development project information. CRITICAL: Distinguish brokers from sellers/buyers and extract property names.

CURRENT YEAR: 2026

=== CRITICAL: BROKER vs SELLER/BUYER ===

BROKERS (intermediaries - NOT sellers or buyers):
- SLIB / Senior Living Investment Brokerage
- Blueprint / Blueprint Healthcare
- Continuum / Continuum Advisors
- Helios / Helios Healthcare Advisors
- Zett Group / The Zett Group
- JLL / JLL Capital Markets
- Marcus & Millichap
- CBRE
- Cushman & Wakefield
- Colliers
- Newmark
- Kislak / The Kislak Co

IMPORTANT RULES:
1. If article says "SLIB arranged the sale" or "Blueprint brokered" → seller: "Undisclosed", broker: "SLIB"
2. If article says "on behalf of undisclosed seller" → seller: "Undisclosed", broker: [company name]
3. If article says "represented the seller" → that company is the BROKER, not the seller
4. NEVER put a broker name in seller or buyer field!

=== PROPERTY NAME vs SELLER ===

PROPERTY/COMMUNITY NAME (examples):
- "Churchill Estates"
- "Laurel Circle"
- "Green Oaks of Holland"
- "Morrison Ranch"
- "The Atrium at Boca Raton"

CRITICAL: Property/community names are NOT sellers!
- If article says "Churchill Estates, a community located in..." → property_name: "Churchill Estates", seller: [actual seller if mentioned]
- Property names are usually mentioned with "located in", "features", "comprises", "totals"

=== TRANSACTION TYPE CLASSIFICATION ===

1. M&A Deal - Acquisition of EXISTING properties:
   - Company acquires another company/portfolio
   - Purchase of operating facilities
   → transaction_type: "M&A"

2. Development Project - NEW construction:
   - Land acquisition for development
   - New building construction
   - Ground-up development
   → transaction_type: "Development"

3. Financing-Only Deal:
   - Loans, bonds, refinancing
   → transaction_type: "Financing"

=== PROPERTY COUNT RULES ===

SINGLE PROPERTY transaction:
- Article mentions "a community", "the property", "one facility"
- NO mention of multiple properties
→ property_count: 1

MULTIPLE PROPERTIES:
- "portfolio of 5 communities"
- "three facilities"
- "multiple properties"
→ property_count: [actual number]

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

Article Title: {article['title']}
URL: {article['url']}

Article Content:
{article['content'][:6000]}

Return ONLY this JSON format. Use "N/A" for missing data:

FOR M&A DEALS:
{{
  "transaction_type": "M&A",
  "property_name": "Name of the property/community or N/A",
  
  "region": "State/region or N/A",
  "seller": "ACTUAL seller (NOT broker!) or Undisclosed or N/A",
  "buyer": "ACTUAL buyer (NOT broker!) or N/A",
  "broker": "Broker/intermediary name or N/A",
  
  "transaction_date": "YYYY-MM-DD when deal CLOSED or N/A",
  "announcement_date": "YYYY-MM-DD when ANNOUNCED or N/A",
  "article_date": "{article.get('article_date', 'N/A')}",
  
  "seller_rationale": "WHY sold (brief) or N/A",
  "buyer_rationale": "WHY bought (brief) or N/A",
  "post_deal_plan": "Plans after closing or N/A",
  
  "price": NUMBER only in dollars or N/A,
  "deal_terms": "Stock / Cash / Asset Swap or N/A",
  
  "total_units": "TOTAL units (number) or N/A",
  "property_count": "NUMBER of properties (1 for single property) or N/A",
  
  "property_type": "AL / MC / IL / CCRC / AA / SNF / Mixed or N/A",
  "year_built": "YYYY format or N/A",
  "property_age": "Number of years or N/A",
  
  "operator": "Who will OPERATE properties after acquisition or N/A",
  "operator_change": 0 or 1,
  
  "financing_method": "Cash / Debt / Equity / Mixed or N/A",
  "financing_details": "Details of financing structure or N/A",
  
  "extraction_confidence": 1-5
}}

FOR DEVELOPMENT PROJECTS:
{{
  "transaction_type": "Development",
  "property_name": "Name of the project/community or N/A",
  
  "project_name": "Name of project (can be same as property_name) or N/A",
  "developer": "STANDARDIZED developer name or N/A",
  "general_contractor": "STANDARDIZED contractor name or N/A",
  "architect": "STANDARDIZED architect name or N/A",
  "civil_engineer": "N/A",
  "landscape_architect": "N/A",
  "interior_designer": "N/A",
  
  "operator": "Who will OPERATE when completed or N/A",
  "operator_type": "Owner-Operated / Third-Party / N/A",
  
  "region": "State/region or N/A",
  "building_type": "AL / MC / IL / CCRC / AA / SNF / Mixed or N/A",
  "unit_count": NUMBER or N/A,
  "building_size_sqft": NUMBER or N/A,
  "land_size_acres": NUMBER or N/A,
  
  "total_project_cost": NUMBER only in dollars or N/A,
  "funding_method": "Debt / Equity / Mixed or N/A",
  "funding_details": "N/A",
  
  "income_target": "Affordable / Middle / Luxury / Mixed or N/A",
  "age_target": "55+ / 65+ / 75+ / 80+ / Mixed or N/A",
  
  "amenities": "comma-separated list or N/A",
  "services_provided": "N/A",
  
  "announcement_date": "YYYY-MM-DD or N/A",
  "expected_completion_date": "YYYY-MM-DD or N/A",
  "project_status": "Announced / Under Construction / Completed or N/A",
  "article_date": "{article.get('article_date', 'N/A')}",
  
  "extraction_confidence": 1-5
}}

FOR FINANCING-ONLY DEALS:
{{
  "transaction_type": "Financing",
  "deal_type": "Financing",
  "property_name": "Name of property being financed or N/A",
  
  "borrower": "STANDARDIZED borrower name or N/A",
  "lender": "STANDARDIZED lender name or N/A",
  "financing_purpose": "Acquisition / Refinancing / Development / Renovation / Expansion / General Corporate or N/A",
  "loan_amount": NUMBER only in dollars or N/A,
  "loan_terms": "Interest rate, maturity, covenants or N/A",
  
  "region": "State/region or N/A",
  "announcement_date": "YYYY-MM-DD or N/A",
  "article_date": "{article.get('article_date', 'N/A')}",
  
  "extraction_confidence": 1-5
}}

CRITICAL RULES:
- NEVER put broker names (SLIB, Blueprint, etc.) in seller or buyer fields!
- Property name is the NAME of the community, not the seller/buyer
- For single property deals: property_count: 1 (NOT N/A!)
- Price/loan_amount: NUMBER only. "$71M" = 71000000
- Use "N/A" for missing - NEVER null, never 0, never empty string
- Return ONLY JSON, no markdown"""
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a precise M&A, Development, and Financing data extraction assistant. CRITICAL: Distinguish brokers from sellers/buyers. Extract property names. Never confuse property names with seller names. Return only valid JSON with 'N/A' for missing fields."},
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
    data = json.loads(response_text)
    
    # POST-PROCESSING: Entity normalization
    for field in ['buyer', 'seller', 'broker', 'borrower', 'lender', 'developer', 
                  'general_contractor', 'architect', 'civil_engineer', 
                  'landscape_architect', 'interior_designer', 'operator']:
        if data.get(field) and data[field] != 'N/A':
            data[field] = normalize_entity_name(data[field])
    
    # POST-PROCESSING: Calculate missing year_built or property_age (M&A only)
    if data.get('transaction_type') == 'M&A':
        year_built = data.get('year_built')
        property_age = data.get('property_age')
        announcement_date = data.get('announcement_date')
        article_date = data.get('article_date')
        
        calc_year, calc_age = calculate_age_and_year(year_built, property_age, announcement_date, article_date)
        
        if data.get('year_built') == 'N/A' and calc_year != 'N/A':
            data['year_built'] = calc_year
        if data.get('property_age') == 'N/A' and calc_age != 'N/A':
            data['property_age'] = calc_age
    
    # Ensure N/A for missing values
    for key in data:
        if data[key] is None or data[key] == "" or data[key] == 0:
            data[key] = "N/A"
    
    # Add metadata
    data['source_url'] = article['url']
    data['article_title'] = article['title']
    data['raw_article_text'] = article['content'][:5000]
    
    return data

def process_urls_from_file(filename='urls.txt'):
    """Process URLs - handles M&A, Development, and Financing"""
    print("\n" + "="*70)
    print("v3.2.1: Broker + Property Names + Better Logic + Age Extraction")
    print("="*70 + "\n")
    
    cookies_exist = os.path.exists('cookies.pkl')
    
    if not cookies_exist:
        print("ℹ️  처음 실행 - Senior Housing News 로그인 필요\n")
    else:
        print("✓ SHN 자동 로그인 준비!\n")
    
    # Read URLs
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and line.strip().startswith('http')]
    except FileNotFoundError:
        print(f"✗ 파일 없음: {filename}")
        return
    
    if not urls:
        print("✗ URL이 없습니다")
        return
    
    print(f"📋 {len(urls)}개 URL 발견\n")
    
    # Initialize database
    db = DealDatabase()
    
    # Filter existing
    new_urls = [url for url in urls if not db.url_exists(url)]
    
    print(f"상태:")
    print(f"   이미 있음: {len(urls) - len(new_urls)}")
    print(f"   처리할 것: {len(new_urls)}\n")
    
    if not new_urls:
        print("✓ 모두 처리됨!")
        return
    
    print("="*70)
    print("처리 시작")
    print("="*70 + "\n")
    
    successful = 0
    failed = 0
    
    for i, url in enumerate(new_urls, 1):
        print(f"[{i}/{len(new_urls)}] {url[:60]}...")
        
        try:
            first_run = (i == 1 and not cookies_exist and 'seniorhousingnews.com' in url)
            
            # Fetch
            article = fetch_article(url, first_run=first_run)
            
            # Extract
            data = extract_deal_data(article)
            
            # Save based on transaction type
            transaction_type = data.get('transaction_type', 'M&A')
            
            if transaction_type == 'Development':
                result = db.insert_development_project(data)
                
                if result:
                    project_name = data.get('property_name', data.get('project_name', 'N/A'))
                    developer = data.get('developer', 'N/A')
                    units = data.get('unit_count', 'N/A')
                    
                    print(f"   ✓ DEVELOPMENT: {project_name}")
                    print(f"      Developer: {developer} | Units: {units}")
                    successful += 1
                else:
                    print(f"   ⊘ 이미 존재")
            
            else:
                # M&A deal (includes Financing)
                if 'deal_type' not in data:
                    if transaction_type == 'Financing':
                        data['deal_type'] = 'Financing'
                    else:
                        data['deal_type'] = 'Acquisition'
                
                result = db.insert_deal(data)
                
                if result:
                    deal_type = data.get('deal_type', 'Acquisition')
                    
                    if deal_type == 'Acquisition':
                        property_name = data.get('property_name', 'N/A')
                        buyer = data.get('buyer', 'N/A')
                        seller = data.get('seller', 'N/A')
                        broker = data.get('broker', 'N/A')
                        
                        print(f"   ✓ M&A: {property_name}")
                        print(f"      {buyer} ← {seller}")
                        if broker != 'N/A':
                            print(f"      Broker: {broker}")
                    
                    elif deal_type == 'Financing':
                        borrower = data.get('borrower', 'N/A')
                        lender = data.get('lender', 'N/A')
                        
                        print(f"   ✓ FINANCING: {borrower} from {lender}")
                    
                    successful += 1
                else:
                    print(f"   ⊘ 이미 존재")
        
        except Exception as e:
            print(f"   ✗ 오류: {str(e)[:60]}")
            failed += 1
        
        if i < len(new_urls):
            print(f"   ⏳ 5초 대기...\n")
            time.sleep(5)
    
    # Summary
    print("\n" + "="*70)
    print("완료")
    print("="*70)
    print(f"✓ 성공: {successful}")
    print(f"✗ 실패: {failed}")
    
    stats = db.get_stats()
    print(f"\n데이터베이스:")
    print(f"  M&A Deals: {stats['ma_deals']}")
    print(f"  Development Projects: {stats['dev_projects']}")
    print(f"  Combined Total: {stats['total_records']} records")
    print("="*70 + "\n")

if __name__ == "__main__":
    process_urls_from_file()
