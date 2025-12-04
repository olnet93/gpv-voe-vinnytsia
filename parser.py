#!/usr/bin/env python3
"""
E-svitlo Parser - спроба логіну БЕЗ CSRF
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
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'uk,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    })
    return scraper

def login_attempt_1(scraper):
    """Спроба 1: POST БЕЗ CSRF, використовуючи JSON"""
    log("[LOGIN_1] Спроба 1: POST JSON без CSRF")
    
    try:
        cf = scraper.get("https://vn.e-svitlo.com.ua/", timeout=30)
        log("[LOGIN_1] CF: " + str(cf.status_code))
    except:
        pass
    
    time.sleep(1)
    
    # POST з JSON content-type
    headers = {
        "Origin": "https://vn.e-svitlo.com.ua",
        "Referer": "https://vn.e-svitlo.com.ua/user_register",
        "Content-Type": "application/json",
    }
    
    data = {
        "login": LOGIN,
        "password": PASSWORD,
    }
    
    resp = scraper.post(
        "https://vn.e-svitlo.com.ua/registr_all_user/login_all_user",
        json=data,
        headers=headers,
        allow_redirects=True,
        timeout=30,
    )
    
    log("[LOGIN_1] Status: " + str(resp.status_code))
    log("[LOGIN_1] URL: " + resp.url)
    is_logged = "Вихід" in resp.text or "logout" in resp.text.lower()
    log("[LOGIN_1] Success: " + str(is_logged))
    log("[LOGIN_1] Size: " + str(len(resp.text)))
    
    return is_logged, scraper

def login_attempt_2(scraper):
    """Спроба 2: POST form-data БЕЗ CSRF"""
    log("[LOGIN_2] Спроба 2: POST form-data без CSRF")
    
    try:
        cf = scraper.get("https://vn.e-svitlo.com.ua/", timeout=30)
        log("[LOGIN_2] CF: " + str(cf.status_code))
    except:
        pass
    
    time.sleep(1)
    
    headers = {
        "Origin": "https://vn.e-svitlo.com.ua",
        "Referer": "https://vn.e-svitlo.com.ua/user_register",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    
    data = {
        "login": LOGIN,
        "password": PASSWORD,
    }
    
    resp = scraper.post(
        "https://vn.e-svitlo.com.ua/registr_all_user/login_all_user",
        data=data,
        headers=headers,
        allow_redirects=True,
        timeout=30,
    )
    
    log("[LOGIN_2] Status: " + str(resp.status_code))
    log("[LOGIN_2] URL: " + resp.url)
    is_logged = "Вихід" in resp.text or "logout" in resp.text.lower()
    log("[LOGIN_2] Success: " + str(is_logged))
    log("[LOGIN_2] Size: " + str(len(resp.text)))
    
    return is_logged, scraper

def activate_session(scraper):
    """Активувати сесію"""
    log("[SESSION] Activating...")
    try:
        cabinet = scraper.get("https://vn.e-svitlo.com.ua/account_household", timeout=30, allow_redirects=True)
        log("[SESSION] Status: " + str(cabinet.status_code))
        log("[SESSION] URL: " + cabinet.url)
        is_cabinet = "account_household" in cabinet.url or "Вихід" in cabinet.text
        log("[SESSION] In cabinet: " + str(is_cabinet))
        time.sleep(1)
        return is_cabinet
    except Exception as e:
        log("[SESSION] Error: " + str(e))
        return False

def extract_json_from_pre(html_content, queue_num):
    """Витягти JSON з <pre>"""
    try:
        match = re.search(r'<pre>(.*?)</pre>', html_content, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
            data = json.loads(json_str)
            return data
    except:
        pass
    return None

def parse_queue(scraper, url, queue_num):
    """Парсити чергу"""
    try:
        time.sleep(1)
        log("[Q" + str(queue_num) + "] Fetching...")
        
        response = scraper.get(url, timeout=30, allow_redirects=True)
        log("[Q" + str(queue_num) + "] Status: " + str(response.status_code))
        
        if response.status_code != 200:
            return []
        
        data = extract_json_from_pre(response.text, queue_num)
        
        if not data:
            log("[Q" + str(queue_num) + "] No JSON")
            return []
        
        planned_list = data.get('planned_list_cab', [])
        log("[Q" + str(queue_num) + "] Found: " + str(len(planned_list)) + " outages")
        
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
        
        log("[Q" + str(queue_num) + "] Parsed: " + str(len(outages)))
        return outages
        
    except Exception as e:
        log("[Q" + str(queue_num) + "] Error: " + str(e)[:80])
        return []

def main():
    log("=" * 70)
    log("E-SVITLO PARSER - СПРОБА БЕЗ CSRF")
    log("=" * 70)
    
    scraper = create_scraper()
    
    # Спроба 1: JSON
    is_logged_1, scraper = login_attempt_1(scraper)
    
    if is_logged_1:
        log("\n✓ Спроба 1 (JSON) ПРАЦЮЄ!")
        if activate_session(scraper):
            log("[MAIN] Parsing queues...")
            all_outages = []
            for idx, url in enumerate(QUEUE_URLS[:2], 1):
                log("[MAIN] Queue " + str(idx) + "/2 (TEST)")
                outages = parse_queue(scraper, url, idx)
                all_outages.extend(outages)
            log("[MAIN] Total: " + str(len(all_outages)))
            return
    
    # Спроба 2: Form-data
    log("\n" + "=" * 70)
    scraper = create_scraper()
    is_logged_2, scraper = login_attempt_2(scraper)
    
    if is_logged_2:
        log("\n✓ Спроба 2 (Form-data) ПРАЦЮЄ!")
        if activate_session(scraper):
            log("[MAIN] Parsing queues...")
            all_outages = []
            for idx, url in enumerate(QUEUE_URLS[:2], 1):
                log("[MAIN] Queue " + str(idx) + "/2 (TEST)")
                outages = parse_queue(scraper, url, idx)
                all_outages.extend(outages)
            log("[MAIN] Total: " + str(len(all_outages)))
            return
    
    log("\n✗ Обидві спроби не працюють!")
    log("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("FATAL: " + str(e))
        import traceback
        traceback.print_exc()
