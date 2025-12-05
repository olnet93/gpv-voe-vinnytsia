#!/usr/bin/env python3
"""
E-svitlo Parser - витягує дані про плановані відключення
Для 12 черг Вінниця регіон (6 груп по 2 черги)
EIC значення прикриті через GitHub Secrets
"""
import json
import os
import time
import sys
from datetime import datetime, timezone, timedelta

def log(msg):
    print(msg)
    sys.stdout.flush()

try:
    import cloudscraper
    log("OK: cloudscraper")
except ImportError:
    log("ERROR: cloudscraper not installed")
    exit(1)

# 12 черг Вінниця (6 груп по 2 черги)
QUEUE_MAPPING = {
    "1.1": "queue 1.1",
    "1.2": "queue 1.2",
    "2.1": "queue 2.1",
    "2.2": "queue 2.2",
    "3.1": "queue 3.1",
    "3.2": "queue 3.2",
    "4.1": "queue 4.1",
    "4.2": "queue 4.2",
    "5.1": "queue 5.1",
    "5.2": "queue 5.2",
    "6.1": "queue 6.1",
    "6.2": "queue 6.2"
}

# EIC значення з GitHub Secrets (прикриті)
EICS = {
    "1.1": os.getenv("ESVITLO_EIC_1_1"),
    "1.2": os.getenv("ESVITLO_EIC_1_2"),
    "2.1": os.getenv("ESVITLO_EIC_2_1"),
    "2.2": os.getenv("ESVITLO_EIC_2_2"),
    "3.1": os.getenv("ESVITLO_EIC_3_1"),
    "3.2": os.getenv("ESVITLO_EIC_3_2"),
    "4.1": os.getenv("ESVITLO_EIC_4_1"),
    "4.2": os.getenv("ESVITLO_EIC_4_2"),
    "5.1": os.getenv("ESVITLO_EIC_5_1"),
    "5.2": os.getenv("ESVITLO_EIC_5_2"),
    "6.1": os.getenv("ESVITLO_EIC_6_1"),
    "6.2": os.getenv("ESVITLO_EIC_6_2"),
}

# Перевірити що всі EIC задані
missing_eics = [k for k, v in EICS.items() if not v]
if missing_eics:
    log("ERROR: Missing EIC secrets: " + str(missing_eics))
    exit(1)

# Побудувати QUEUE_URLS з прикритими EIC
QUEUE_URLS = [
    f"https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic={EICS['1.1']}&type_user=1&a=290637",
    f"https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic={EICS['1.2']}&type_user=1&a=290637",
    f"https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic={EICS['2.1']}&type_user=1&a=290637",
    f"https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic={EICS['2.2']}&type_user=1&a=290637",
    f"https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic={EICS['3.1']}&type_user=1&a=290637",
    f"https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic={EICS['3.2']}&type_user=1&a=290637",
    f"https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic={EICS['4.1']}&type_user=1&a=290637",
    f"https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic={EICS['4.2']}&type_user=1&a=290637",
    f"https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic={EICS['5.1']}&type_user=1&a=290637",
    f"https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic={EICS['5.2']}&type_user=1&a=290637",
    f"https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic={EICS['6.1']}&type_user=1&a=290637",
    f"https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic={EICS['6.2']}&type_user=1&a=290637",
]

LOGIN = os.getenv("ESVITLO_LOGIN")
PASSWORD = os.getenv("ESVITLO_PASSWORD")

log("LOGIN: " + str(bool(LOGIN)))
log("PASSWORD: " + str(bool(PASSWORD)))
log("EICs loaded: " + str(len([v for v in EICS.values() if v])) + "/12")

if not LOGIN or not PASSWORD:
    log("ERROR: No credentials provided")
    exit(1)

# Kyiv timezone (UTC+2 in winter, UTC+3 in summer)
KYIV_TZ = timezone(timedelta(hours=2))

def create_scraper():
    """Створити scraper з anti-Cloudflare headers"""
    scraper = cloudscraper.create_scraper()
    scraper.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'uk,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    })
    return scraper

def login(scraper):
    """Залогінитися на e-svitlo.com.ua"""
    log("[LOGIN] Starting authentication")
    
    try:
        cf = scraper.get("https://vn.e-svitlo.com.ua/", timeout=30)
        log("[LOGIN] CF challenge: " + str(cf.status_code))
    except Exception as e:
        log("[LOGIN] CF error: " + str(e))
    
    time.sleep(1)
    
    data = {
        "email": LOGIN,
        "password": PASSWORD,
    }
    
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
    
    is_logged_in = "Вихід" in resp.text or "logout" in resp.text.lower()
    log("[LOGIN] Authenticated: " + str(is_logged_in))
    
    time.sleep(2)
    return scraper

def activate_session(scraper):
    """Активувати сесію перед парсингом черг"""
    log("[SESSION] Activating session")
    try:
        cabinet_response = scraper.get("https://vn.e-svitlo.com.ua/account_household", timeout=30, allow_redirects=True)
        log("[SESSION] Cabinet status: " + str(cabinet_response.status_code))
        
        cookies_dict = scraper.cookies.get_dict()
        log("[SESSION] Cookies: " + str(len(cookies_dict)))
        
        time.sleep(1)
    except Exception as e:
        log("[SESSION] Error: " + str(e))

def get_queue_name(queue_key):
    """Отримати назву черги за ключем"""
    return QUEUE_MAPPING.get(queue_key, "unknown")

def parse_queue(scraper, url, queue_key, queue_idx):
    """Парсити одну чергу"""
    try:
        time.sleep(1)
        
        queue_name = get_queue_name(queue_key)
        
        log("[Q" + str(queue_idx) + "] " + queue_name + " Fetching...")
        
        response = scraper.get(url, timeout=30, allow_redirects=True)
        
        log("[Q" + str(queue_idx) + "] Status: " + str(response.status_code))
        
        if response.status_code != 200:
            log("[Q" + str(queue_idx) + "] ERROR: Status " + str(response.status_code))
            return []
        
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as e:
            log("[Q" + str(queue_idx) + "] JSON decode error: " + str(e))
            return []
        
        planned_list = data.get('planned_list_cab', [])
        log("[Q" + str(queue_idx) + "] Found: " + str(len(planned_list)) + " outages")
        
        outages = []
        for item in planned_list:
            if isinstance(item, dict):
                outages.append({
                    'queue': queue_name,
                    'acc_begin': item.get('acc_begin', ''),
                    'accend_plan': item.get('accend_plan', ''),
                    'typeid': item.get('typeid', '')
                })
        
        log("[Q" + str(queue_idx) + "] Parsed: " + str(len(outages)) + " records")
        return outages
        
    except Exception as e:
        log("[Q" + str(queue_idx) + "] EXCEPTION: " + str(e)[:100])
        return []

def save_results(all_outages):
    """Зберегти результати у JSON"""
    log("[SAVE] Writing Vinnytsiaoblenerho.json")
    
    # Отримати поточний час у Kyiv timezone для last_updated
    kyiv_now = datetime.now(KYIV_TZ)
    
    # Форматуємо як строку без таймзони (YYYY-MM-DDTHH:MM:SS)
    last_updated_str = kyiv_now.strftime('%Y-%m-%dT%H:%M:%S')
    
    result = {
        "last_updated": last_updated_str,
        "total_outages": len(all_outages),
        "outages": all_outages
    }
    
    # Створити папку data якщо не існує
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        log("[SAVE] Created directory: " + data_dir)
    
    # Записати файл у папку data
    file_path = os.path.join(data_dir, "Vinnytsiaoblenerho.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    log("[SAVE] Success: " + str(len(all_outages)) + " outages saved to " + file_path)

def main():
    log("=" * 70)
    log("E-SVITLO PARSER - START")
    log("=" * 70)
    
    scraper = create_scraper()
    login(scraper)
    activate_session(scraper)
    
    log("[MAIN] Parsing 12 queues...")
    all_outages = []
    
    queue_keys = ["1.1", "1.2", "2.1", "2.2", "3.1", "3.2", "4.1", "4.2", "5.1", "5.2", "6.1", "6.2"]
    
    for idx, (queue_key, url) in enumerate(zip(queue_keys, QUEUE_URLS), 1):
        queue_outages = parse_queue(scraper, url, queue_key, idx)
        all_outages.extend(queue_outages)
    
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
