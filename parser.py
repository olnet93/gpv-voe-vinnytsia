#!/ur/bin/env python3
"""
Debug parser - find API endpoint
"""
import json
import os
import time
import re
import sys
from datetime import datetime

def log(msg):
    print(msg)
    sys.stdout.flush()

try:
    import cloudscraper
    log("OK: cloudscraper")
except ImportError:
    log("ERROR: cloudscraper not installed")
    exit(1)

QUEUE_URLS = [
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z7056418802433&type_user=1&a=290637",
]

LOGIN = os.getenv("ESVITLO_LOGIN")
PASSWORD = os.getenv("ESVITLO_PASSWORD")

log("LOGIN: " + str(bool(LOGIN)))
log("PASSWORD: " + str(bool(PASSWORD)))

if not LOGIN or not PASSWORD:
    log("ERROR: No credentials")
    exit(1)

def create_scraper():
    scraper = cloudscraper.create_scraper()
    scraper.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'uk,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    })
    return scraper

def login(scraper):
    log("Login: starting")
    
    try:
        cf = scraper.get("https://vn.e-svitlo.com.ua/", timeout=30)
        log("CF: " + str(cf.status_code))
    except Exception as e:
        log("CF error: " + str(e))
    
    time.sleep(2)
    
    data = {"login": LOGIN, "password": PASSWORD}
    headers = {
        "Origin": "https://vn.e-svitlo.com.ua",
        "Referer": "https://vn.e-svitlo.com.ua/user_register",
    }
    
    resp = scraper.post(
        "https://vn.e-svitlo.com.ua/registr_all_user/login_all_user",
        data=data,
        headers=headers,
        allow_redirects=True,
        timeout=30,
    )
    
    log("Login response: " + str(resp.status_code))
    log("Login OK")
    return scraper

def main():
    log("=" * 70)
    log("PARSER - FIND API")
    log("=" * 70)
    
    scraper = create_scraper()
    login(scraper)
    
    url = QUEUE_URLS[0]
    
    response = scraper.get(url, timeout=30)
    log("Response: " + str(response.status_code))
    log("Content length: " + str(len(response.text)))
    
    # Save FULL HTML
    with open("debug_full.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    log("Saved full HTML to debug_full.html (" + str(len(response.text)) + " bytes)")
    
    # Search for API endpoints
    log("\nSearching for API endpoints...")
    
    # Look for fetch/ajax calls
    patterns = [
        r'fetch\s*\(\s*["\']([^"\']+)["\']',
        r'ajax\s*\(\s*\{\s*url\s*:\s*["\']([^"\']+)["\']',
        r'POST|GET|PUT|DELETE\s+([^\s]+)',
        r'\.php\?[^\s"\'<>]+',
        r'/api/[^\s"\'<>]+',
        r'/account_[^\s"\'<>]+',
    ]
    
    for idx, pattern in enumerate(patterns):
        log("Pattern " + str(idx) + ":")
        matches = re.findall(pattern, response.text, re.IGNORECASE)
        unique_matches = list(set(matches))
        log("  Found " + str(len(unique_matches)) + " unique matches")
        for match in unique_matches[:5]:
            log("    - " + str(match)[:100])
    
    # Search for XML HttpRequest
    log("\nSearching for XMLHttpRequest...")
    xhr_matches = re.findall(r'XMLHttpRequest[^}]*?\}', response.text, re.DOTALL)
    log("Found: " + str(len(xhr_matches)))
    
    # Search for keywords related to outages
    log("\nSearching for outage keywords...")
    keywords = ['disconnection', 'outage', 'planned', 'schedule', 'acc_begin', 'accend_plan', 'disable', 'block']
    for keyword in keywords:
        count = len(re.findall(keyword, response.text, re.IGNORECASE))
        if count > 0:
            log("  " + keyword + ": " + str(count))
    
    # Print first 2000 chars of body
    log("\nFirst 2000 chars of HTML:")
    print(response.text[:2000])
    
    log("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("FATAL: " + str(e))
        import traceback
        traceback.print_exc()
        exit(1)
