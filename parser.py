#!/usr/bin/env python3
"""
E-svitlo Parser - детальна діагностика логіну
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
    log("ДІАГНОСТИКА")
    log("=" * 70)
    
    scraper = create_scraper()
    
    # 1. Перевіримо login page
    log("\n[1] Витягуємо сторінку логіну")
    resp = scraper.get("https://vn.e-svitlo.com.ua/user_register", timeout=30)
    
    # Шукаємо поля форми
    log("\n[2] Аналіз форми:")
    
    # Шукаємо name всіх input fields
    inputs = re.findall(r'<input[^>]*name=["\']([^"\']*)["\'][^>]*>', resp.text)
    log("Input field names: " + str(inputs))
    
    # Шукаємо action форми
    action = re.search(r'<form[^>]*action=["\']([^"\']*)["\']', resp.text)
    if action:
        log("Form action: " + action.group(1))
    
    # Шукаємо method
    method = re.search(r'<form[^>]*method=["\']([^"\']*)["\']', resp.text)
    if method:
        log("Form method: " + method.group(1))
    
    # Шукаємо attr_type (може бути user_type)
    type_match = re.search(r'type_user\s*=\s*["\']?(\d+)["\']?', resp.text)
    if type_match:
        log("Found type_user: " + type_match.group(1))
    
    # Шукаємо а параметр
    a_match = re.search(r'[?&]a=(\d+)', resp.text)
    if a_match:
        log("Found a parameter: " + a_match.group(1))
    
    # 3. Спробуємо логіниться з type_user параметром
    log("\n[3] Спроба 1: POST з type_user=1")
    data = {
        "login": LOGIN,
        "password": PASSWORD,
        "type_user": "1",
        "a": "290637"
    }
    
    resp1 = scraper.post(
        "https://vn.e-svitlo.com.ua/registr_all_user/login_all_user",
        data=data,
        allow_redirects=True,
        timeout=30,
    )
    
    log("Status: " + str(resp1.status_code))
    log("URL: " + resp1.url)
    is_logged = "Вихід" in resp1.text or "logout" in resp1.text.lower()
    log("Authenticated: " + str(is_logged))
    
    if is_logged:
        log("\n✓ ПРАЦЮЄ з type_user і a параметрами!")
        log("\n[4] Тестуємо кабінет")
        cabinet = scraper.get("https://vn.e-svitlo.com.ua/account_household", timeout=30, allow_redirects=True)
        log("Cabinet status: " + str(cabinet.status_code))
        log("Cabinet URL: " + cabinet.url)
        
        # Отримуємо cookies
        cookies = scraper.cookies.get_dict()
        log("\nCookies: " + str(len(cookies)))
        for name, value in cookies.items():
            log("  - " + name + " = " + value[:50])
        
        # Тестуємо першу чергу
        log("\n[5] Тестуємо першу чергу")
        queue_url = "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z7056418802433&type_user=1&a=290637"
        queue_resp = scraper.get(queue_url, timeout=30, allow_redirects=True)
        log("Queue status: " + str(queue_resp.status_code))
        log("Queue size: " + str(len(queue_resp.text)))
        
        # Шукаємо <pre>
        pre_match = re.search(r'<pre>(.*?)</pre>', queue_resp.text, re.DOTALL)
        if pre_match:
            log("✓ Found <pre> tag!")
            json_str = pre_match.group(1).strip()[:200]
            log("JSON (first 200 chars): " + json_str)
        else:
            log("✗ No <pre> tag found")
            # Покажемо перші 300 chars відповіді
            log("Response (first 300 chars):")
            log(queue_resp.text[:300])
        
        return True
    
    log("\n✗ Не працює")
    
    # 4. Спробуємо без параметрів
    log("\n[4] Спроба 2: POST без параметрів")
    data2 = {
        "login": LOGIN,
        "password": PASSWORD,
    }
    
    resp2 = scraper.post(
        "https://vn.e-svitlo.com.ua/registr_all_user/login_all_user",
        data=data2,
        allow_redirects=True,
        timeout=30,
    )
    
    log("Status: " + str(resp2.status_code))
    is_logged2 = "Вихід" in resp2.text
    log("Authenticated: " + str(is_logged2))
    
    log("\n=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("ERROR: " + str(e))
        import traceback
        traceback.print_exc()
