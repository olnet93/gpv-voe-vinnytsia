#!/usr/bin/env python3
"""
Парсер e-svitlo з збереженням HTML для дебагу
"""
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
    log("Login URL: " + resp.url)
    log("Login OK")
    return scraper

def find_data_in_html(html_content):
    """Найти все возможные структуры данных в HTML"""
    log("Searching for data in HTML")
    log("HTML length: " + str(len(html_content)))
    
    # Ищем JSON блоки
    log("Looking for JSON blocks...")
    json_pattern = r'\{[^{}]*"acc_begin"[^{}]*\}'
    matches = re.findall(json_pattern, html_content)
    log("Found JSON-like blocks: " + str(len(matches)))
    
    # Ищем массивы
    log("Looking for arrays...")
    array_pattern = r'\[\s*\{[^}]*"acc_begin"[^}]*\}'
    matches = re.findall(array_pattern, html_content)
    log("Found arrays: " + str(len(matches)))
    
    # Ищем переменные JavaScript
    log("Looking for JS variables...")
    var_pattern = r'var\s+\w+\s*=\s*(\[.*?\]);'
    matches = re.findall(var_pattern, html_content, re.DOTALL)
    log("Found JS vars: " + str(len(matches)))
    
    # Ищем строки с временем (формат HH:MM)
    log("Looking for time patterns...")
    time_pattern = r'\d{1,2}:\d{2}'
    matches = re.findall(time_pattern, html_content)
    log("Found time patterns: " + str(len(matches)))
    if matches:
        log("Sample times: " + str(matches[:5]))
    
    # Ищем даты
    log("Looking for date patterns...")
    date_pattern = r'\d{4}-\d{2}-\d{2}'
    matches = re.findall(date_pattern, html_content)
    log("Found date patterns: " + str(len(matches)))
    if matches:
        log("Sample dates: " + str(matches[:5]))
    
    # Ищем тег <table>
    log("Looking for tables...")
    if '<table' in html_content.lower():
        log("Found: <table>")
        # Ищем <td> 
        td_matches = re.findall(r'<td[^>]*>(.*?)</td>', html_content, re.IGNORECASE)
        log("Found <td>: " + str(len(td_matches)))
        if td_matches:
            log("Sample TD: " + str(td_matches[:5]))
    
    # Ищем <div> с данными
    log("Looking for divs...")
    div_pattern = r'<div[^>]*class=["\']([^"\']*outage[^"\']*)["\'][^>]*>(.*?)</div>'
    matches = re.findall(div_pattern, html_content, re.IGNORECASE)
    log("Found outage divs: " + str(len(matches)))
    
    # Сохраняем HTML для ручного анализа
    with open("debug_queue1.html", "w", encoding="utf-8") as f:
        f.write(html_content[:10000])
    log("Saved first 10KB to debug_queue1.html")

def main():
    log("=" * 70)
    log("PARSER - DEBUG MODE")
    log("=" * 70)
    
    scraper = create_scraper()
    login(scraper)
    
    log("Fetching first queue for analysis")
    url = QUEUE_URLS[0]
    
    response = scraper.get(url, timeout=30)
    log("Response: " + str(response.status_code))
    log("Content length: " + str(len(response.text)))
    
    find_data_in_html(response.text)
    
    # Попытаемся найти и распарсить данные
    log("\nTrying to extract data...")
    patterns = [
        r'var\s+planned_list_cab\s*=\s*(\[.*?\]);',
        r'planned_list_cab\s*:\s*(\[.*?\]),',
        r'"planned_list_cab"\s*:\s*(\[.*?\])(?:\s*,|\s*})',
        r'var\s+\w*\s*=\s*(\[.*?"acc_begin".*?\]);'
    ]
    
    for idx, pattern in enumerate(patterns):
        log("Pattern " + str(idx) + ":")
        matches = re.findall(pattern, response.text, re.DOTALL | re.IGNORECASE)
        log("  Found: " + str(len(matches)))
        
        for match_idx, match in enumerate(matches[:1]):
            log("  Match " + str(match_idx) + " length: " + str(len(match)))
            try:
                data = json.loads(match)
                log("  Parsed OK, type: " + str(type(data)))
                if isinstance(data, list):
                    log("  List length: " + str(len(data)))
                    if len(data) > 0:
                        log("  First item: " + str(data[0])[:100])
            except json.JSONDecodeError as e:
                log("  JSON error: " + str(e))
    
    log("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("FATAL: " + str(e))
        import traceback
        traceback.print_exc()
        exit(1)
