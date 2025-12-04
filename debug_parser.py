#!/usr/bin/env python3
"""
E-svitlo Parser - DEBUG версія
Витягує і зберігає HTML для аналізу
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
    log("DEBUG: СНІМІТ HTML")
    log("=" * 70)
    
    scraper = create_scraper()
    
    # 1. Домашня сторінка
    log("\n[1] GET /")
    resp1 = scraper.get("https://vn.e-svitlo.com.ua/", timeout=30)
    log("Status: " + str(resp1.status_code))
    with open("debug_1_home.html", "w", encoding="utf-8") as f:
        f.write(resp1.text)
    log("Saved: debug_1_home.html")
    
    time.sleep(1)
    
    # 2. Сторінка логіну
    log("\n[2] GET /user_register")
    resp2 = scraper.get("https://vn.e-svitlo.com.ua/user_register", timeout=30)
    log("Status: " + str(resp2.status_code))
    log("Size: " + str(len(resp2.text)) + " bytes")
    with open("debug_2_login.html", "w", encoding="utf-8") as f:
        f.write(resp2.text)
    log("Saved: debug_2_login.html")
    
    # Пошукати CSRF у різних способах
    log("\n[3] Пошук CSRF токену")
    
    # Спосіб 1: Наш regex
    csrf_match = re.search(r'name=["\']csrf["\'].*?value=["\']([^"\']+)["\']', resp2.text, re.IGNORECASE)
    log("Regex 1 (nossa): " + str(csrf_match is not None))
    
    # Спосіб 2: Шукаємо input з csrf
    inputs = re.findall(r'<input[^>]*>', resp2.text)
    log("Found <input> tags: " + str(len(inputs)))
    for i, inp in enumerate(inputs[:5]):  # Перші 5
        log("  [" + str(i) + "]: " + inp[:80])
        if 'csrf' in inp.lower():
            log("    ^ Contains CSRF!")
    
    # Спосіб 3: Шукаємо form
    forms = re.findall(r'<form[^>]*>.*?</form>', resp2.text, re.DOTALL)
    log("Found <form> tags: " + str(len(forms)))
    if forms:
        log("First form (first 300 chars):")
        log(forms[0][:300])
    
    # Спосіб 4: Шукаємо всі згадування 'csrf'
    csrf_mentions = re.findall(r'.{0,50}csrf.{0,50}', resp2.text, re.IGNORECASE)
    log("Mentions of 'csrf': " + str(len(csrf_mentions)))
    for mention in csrf_mentions[:3]:
        log("  - " + mention)
    
    # Спосіб 5: Шукаємо дані у JavaScript
    js_csrf = re.search(r'[\'"]([\w\-]{20,})[\'"]', resp2.text)
    log("Possible tokens in JS: " + str(js_csrf is not None))
    
    log("\n[4] Cookies після login page")
    cookies_dict = scraper.cookies.get_dict()
    log("Cookies: " + str(len(cookies_dict)))
    for name, value in cookies_dict.items():
        log("  - " + name + " = " + value[:40])
    
    log("\n=" * 70)
    log("Перевір файли: debug_1_home.html і debug_2_login.html")
    log("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("ERROR: " + str(e))
        import traceback
        traceback.print_exc()
