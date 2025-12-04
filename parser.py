#!/usr/bin/env python3
"""
E-svitlo Parser - витягує дані про плановані відключення
Для 12 черг Вінниця регіон
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

# 12 черг Вінниця
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
    log("ERROR: No credentials provided")
    log("Set ESVITLO_LOGIN and ESVITLO_PASSWORD environment variables")
    exit(1)

def create_scraper():
    """Створити scraper з anti-Cloudflare headers"""
    scraper = cloudscraper.create_scraper()
    scraper.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'uk,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    })
    return scraper

def get_csrf_token(scraper):
    """Витягти CSRF токен зі сторінки реєстрації"""
    log("[CSRF] Getting token from login page")
    try:
        resp = scraper.get("https://vn.e-svitlo.com.ua/user_register", timeout=30)
        log("[CSRF] Status: " + str(resp.status_code))
        
        # Пошукати <input name="csrf" value="TOKEN">
        csrf_match = re.search(r'name=["\']csrf["\'].*?value=["\']([^"\']+)["\']', resp.text, re.IGNORECASE)
        if csrf_match:
            token = csrf_match.group(1)
            log("[CSRF] Found: " + token[:20] + "...")
            return token
        
        log("[CSRF] Not found in HTML")
    except Exception as e:
        log("[CSRF] Error: " + str(e))
    
    return None

def login(scraper):
    """Залогінитися на e-svitlo.com.ua"""
    log("[LOGIN] Starting authentication")
    
    # Крок 1: GET на домашню сторінку (Cloudflare challenge)
    try:
        cf = scraper.get("https://vn.e-svitlo.com.ua/", timeout=30)
        log("[LOGIN] CF challenge: " + str(cf.status_code))
    except Exception as e:
        log("[LOGIN] CF error: " + str(e))
    
    time.sleep(1)
    
    # Крок 2: Витягнути CSRF токен
    csrf_token = get_csrf_token(scraper)
    time.sleep(1)
    
    # Крок 3: POST логін форму
    data = {
        "login": LOGIN,
        "password": PASSWORD,
    }
    
    if csrf_token:
        data["csrf"] = csrf_token
    
    headers = {
        "Origin": "https://vn.e-svitlo.com.ua",
        "Referer": "https://vn.e-svitlo.com.ua/user_register",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    
    resp = scraper.post(
        "https://vn.e-svitlo.com.ua/registr_all_user/login_all_user",
        data=data,
        headers=headers,
        allow_redirects=True,
        timeout=30,
    )
    
    log("[LOGIN] Response: " + str(resp.status_code))
    log("[LOGIN] URL: " + resp.url)
    
    # Перевірити чи залогінені (шукаємо "Вихід" - logout button)
    is_logged_in = "Вихід" in resp.text or "logout" in resp.text.lower()
    log("[LOGIN] Authenticated: " + str(is_logged_in))
    
    time.sleep(2)
    return scraper

def activate_session(scraper):
    """
    ВАЖНО: Активувати сесію перед парсингом черг
    Це потрібно щоб cookies остались валідними
    """
    log("[SESSION] Activating session - GET cabinet page with redirects")
    try:
        cabinet_response = scraper.get("https://vn.e-svitlo.com.ua/account_household", timeout=30, allow_redirects=True)
        log("[SESSION] Cabinet page status: " + str(cabinet_response.status_code))
        log("[SESSION] Cabinet URL: " + cabinet_response.url)
        
        # Показати cookies після активації
        cookies_dict = scraper.cookies.get_dict()
        log("[SESSION] Cookies after activation: " + str(len(cookies_dict)) + " cookies")
        for name, value in cookies_dict.items():
            log("[SESSION] - " + name + " = " + value[:30])
        
        time.sleep(1)
    except Exception as e:
        log("[SESSION] Error: " + str(e))

def extract_json_from_pre(html_content, queue_num):
    """Витягти JSON з <pre> тегу"""
    try:
        match = re.search(r'<pre>(.*?)</pre>', html_content, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
            data = json.loads(json_str)
            return data
        else:
            log("[Q" + str(queue_num) + "] No <pre> tag found in HTML")
    except json.JSONDecodeError as e:
        log("[Q" + str(queue_num) + "] JSON parse error: " + str(e))
    except Exception as e:
        log("[Q" + str(queue_num) + "] Error: " + str(e))
    
    return None

def parse_queue(scraper, url, queue_num):
    """Парсити одну чергу"""
    try:
        time.sleep(1)
        log("[Q" + str(queue_num) + "] Fetching...")
        
        response = scraper.get(url, timeout=30, allow_redirects=True)
        
        log("[Q" + str(queue_num) + "] Status: " + str(response.status_code) + " (" + str(len(response.text)) + "B)")
        
        if response.status_code != 200:
            log("[Q" + str(queue_num) + "] ERROR: Status " + str(response.status_code))
            return []
        
        # Витягнути JSON з <pre>
        data = extract_json_from_pre(response.text, queue_num)
        
        if not data:
            log("[Q" + str(queue_num) + "] No data extracted")
            return []
        
        # Отримати список плану
        planned_list = data.get('planned_list_cab', [])
        log("[Q" + str(queue_num) + "] Found: " + str(len(planned_list)) + " outages")
        
        # Конвертувати в наш формат
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
        
        log("[Q" + str(queue_num) + "] Parsed: " + str(len(outages)) + " records")
        return outages
        
    except Exception as e:
        log("[Q" + str(queue_num) + "] EXCEPTION: " + str(e)[:100])
        return []

def save_results(all_outages):
    """Зберегти результати у JSON"""
    log("[SAVE] Writing outages.json")
    
    result = {
        "last_updated": datetime.now().isoformat(),
        "total_outages": len(all_outages),
        "outages": all_outages
    }
    
    with open("outages.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    log("[SAVE] Success: " + str(len(all_outages)) + " outages saved")

def main():
    log("=" * 70)
    log("E-SVITLO PARSER - START")
    log("=" * 70)
    
    # Логін
    scraper = create_scraper()
    login(scraper)
    
    # ВАЖНО: Активувати сесію перед парсингом черг
    activate_session(scraper)
    
    # Парсити всі 12 черг
    log("[MAIN] Parsing 12 queues...")
    all_outages = []
    
    for idx, url in enumerate(QUEUE_URLS, 1):
        log("[MAIN] Queue " + str(idx) + "/12")
        queue_outages = parse_queue(scraper, url, idx)
        all_outages.extend(queue_outages)
    
    # Зберегти результати
    log("[MAIN] Total outages: " + str(len(all_outages)))
    save_results(all_outages)
    
    log("=" * 70)
    log("DONE")
    log("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("[MAIN] FATAL ERROR: " + str(e))
        import traceback
        traceback.print_exc()
        exit(1)
