#!/usr/bin/env python3
import json
import os
import time
import re
import sys
from datetime import datetime
from urllib.parse import urlparse

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
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z3790933130321&type_user=1&a=290637",
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z8643921175882&type_user=1&a=290637",
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z6908816145370&type_user=1&a=290637",
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z122797640622H&type_user=1&a=290637",
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z923769103674C&type_user=1&a=290637",
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z595315443877G&type_user=1&a=290637",
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z1881561967951&type_user=1&a=290637",
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z7896315479246&type_user=1&a=290637",
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z2780989447998&type_user=1&a=290637",
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z9499016055016&type_user=1&a=290637",
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z029828840776V&type_user=1&a=290637"
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
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'uk,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    })
    return scraper

def login(scraper):
    log("[LOGIN] Starting")
    
    try:
        cf = scraper.get("https://vn.e-svitlo.com.ua/", timeout=30)
        log("[LOGIN] CF: " + str(cf.status_code))
    except Exception as e:
        log("[LOGIN] CF error: " + str(e))
    
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
    
    log("[LOGIN] Response: " + str(resp.status_code))
    log("[LOGIN] OK")
    return scraper

def extract_json_from_html(html_content):
    """Extract JSON from <pre> tag"""
    try:
        # Find content between <pre> and </pre>
        match = re.search(r'<pre>(.*?)</pre>', html_content, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
            data = json.loads(json_str)
            return data
    except Exception as e:
        log("[EXTRACT] Error: " + str(e))
    
    return None

def parse_queue(scraper, url, queue_num):
    try:
        time.sleep(1)
        log("[Q" + str(queue_num) + "] GET")
        response = scraper.get(url, timeout=30)
        
        log("[Q" + str(queue_num) + "] Status: " + str(response.status_code))
        
        if response.status_code != 200:
            log("[Q" + str(queue_num) + "] Error status")
            return []
        
        # Extract JSON from HTML
        data = extract_json_from_html(response.text)
        
        if not data:
            log("[Q" + str(queue_num) + "] No JSON found")
            return []
        
        planned_list = data.get('planned_list_cab', [])
        log("[Q" + str(queue_num) + "] Found: " + str(len(planned_list)) + " planned outages")
        
        outages = []
        for item in planned_list:
            if isinstance(item, dict):
                outages.append({
                    'queue': queue_num,
                    'eic': item.get('eic', ''),
                    'acc_begin': item.get('acc_begin', ''),
                    'accend_plan': item.get('accend_plan', ''),
                    'typeid': item.get('typeid', ''),
                    'address': item.get('address', '')
                })
        
        log("[Q" + str(queue_num) + "] Extracted: " + str(len(outages)) + " outages")
        return outages
        
    except Exception as e:
        log("[Q" + str(queue_num) + "] ERROR: " + str(e)[:80])
        return []

def main():
    log("=" * 70)
    log("PARSER START")
    log("=" * 70)
    
    scraper = create_scraper()
    login(scraper)
    
    log("[MAIN] Parsing queues")
    all_outages = []
    
    for idx, url in enumerate(QUEUE_URLS, 1):
        log("[MAIN] Queue " + str(idx) + "/12")
        queue_outages = parse_queue(scraper, url, idx)
        all_outages.extend(queue_outages)
    
    log("[MAIN] Total: " + str(len(all_outages)) + " outages")
    log("[MAIN] Saving to outages.json")
    
    result = {
        "last_updated": datetime.now().isoformat(),
        "total_outages": len(all_outages),
        "outages": all_outages
    }
    
    with open("outages.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    log("[MAIN] SUCCESS: saved " + str(len(all_outages)) + " outages")
    log("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("FATAL: " + str(e))
        import traceback
        traceback.print_exc()
        exit(1)
