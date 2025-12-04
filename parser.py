#!/usr/bin/env python3
"""
E-svitlo Parser - зберігаємо першу чергу для аналізу
"""
import json
import os
import time
import re
import sys

def log(msg):
    print(msg)
    sys.stdout.flush()

try:
    import cloudscraper
    log("OK: cloudscraper")
except ImportError:
    log("ERROR: cloudscraper not installed")
    exit(1)

LOGIN = os.getenv("ESVITLO_LOGIN")
PASSWORD = os.getenv("ESVITLO_PASSWORD")

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

def main():
    log("=" * 70)
    log("DEBUG: АНАЛІЗ ВІДПОВІДІ ЧЕРГИ")
    log("=" * 70)
    
    scraper = create_scraper()
    
    # Логін
    log("\n[1] Login...")
    data = {
        "email": LOGIN,
        "password": PASSWORD,
    }
    
    resp = scraper.post(
        "https://vn.e-svitlo.com.ua/registr_all_user/login_all_user",
        data=data,
        allow_redirects=True,
        timeout=30,
    )
    log("Status: " + str(resp.status_code))
    is_logged = "Вихід" in resp.text
    log("Authenticated: " + str(is_logged))
    
    time.sleep(1)
    
    # Активуємо сесію
    log("\n[2] Activate session...")
    cabinet = scraper.get("https://vn.e-svitlo.com.ua/account_household", timeout=30, allow_redirects=True)
    log("Status: " + str(cabinet.status_code))
    
    time.sleep(1)
    
    # Отримуємо першу чергу
    log("\n[3] Get first queue...")
    queue_url = "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z7056418802433&type_user=1&a=290637"
    queue_resp = scraper.get(queue_url, timeout=30, allow_redirects=True)
    
    log("Status: " + str(queue_resp.status_code))
    log("Size: " + str(len(queue_resp.text)) + " bytes")
    log("Content-Type: " + queue_resp.headers.get('Content-Type', 'unknown'))
    
    # Зберігаємо весь вміст
    with open("debug_queue.html", "w", encoding="utf-8") as f:
        f.write(queue_resp.text)
    log("Saved to: debug_queue.html")
    
    # Показуємо першу частину
    log("\n[4] Response preview (first 500 chars):")
    log(queue_resp.text[:500])
    
    # Спробуємо парсити як JSON
    log("\n[5] Try to parse as JSON...")
    try:
        json_data = json.loads(queue_resp.text)
        log("✓ Valid JSON!")
        log("Keys: " + str(list(json_data.keys())))
        
        # Перевіримо структуру
        if 'planned_list_cab' in json_data:
            log("✓ Found planned_list_cab!")
            log("Items: " + str(len(json_data['planned_list_cab'])))
        else:
            log("Structure:")
            for key, value in json_data.items():
                if isinstance(value, list):
                    log("  - " + key + ": [list with " + str(len(value)) + " items]")
                elif isinstance(value, dict):
                    log("  - " + key + ": {dict with keys: " + str(list(value.keys())[:5]) + "}")
                else:
                    log("  - " + key + ": " + str(type(value).__name__))
    except json.JSONDecodeError as e:
        log("✗ Not JSON: " + str(e))
    
    # Шукаємо <pre>
    log("\n[6] Search for <pre> tag...")
    if '<pre>' in queue_resp.text:
        log("✓ Found <pre> tag!")
    else:
        log("✗ No <pre> tag")
    
    # Шукаємо масиви
    log("\n[7] Search for arrays in response...")
    arrays = re.findall(r'\[\s*\{', queue_resp.text)
    log("Array patterns found: " + str(len(arrays)))
    
    log("\n=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("ERROR: " + str(e))
        import traceback
        traceback.print_exc()
