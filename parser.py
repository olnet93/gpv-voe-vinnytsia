import requests
import json
import os
import time
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
import warnings
warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

# URL логіну та головна сторінка
LOGIN_URL = "https://vn.e-svitlo.com.ua/user/login"
MAIN_URL = "https://vn.e-svitlo.com.ua/"
# Список URL черг
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

if not LOGIN or not PASSWORD:
    raise Exception("ESVITLO_LOGIN або ESVITLO_PASSWORD не встановлені")

def create_session():
    """Створюємо сесію з реалістичними заголовками"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'uk-UA,uk;q=0.9,ru;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    session.verify = False  # Ігноруємо SSL для GitHub Actions
    return session

def login(session):
    """Багатостадійна авторизація"""
    print("Крок 1: Завантажуємо сторінку логіну...")
    
    # Крок 1: Отримуємо сторінку логіну для CSRF токена
    login_page = session.get(LOGIN_URL, timeout=30)
    if login_page.status_code != 200:
        raise Exception(f"Не вдалося завантажити сторінку логіну: {login_page.status_code}")
    
    print(f"Статус сторінки логіну: {login_page.status_code}")
    
    # Шукаємо CSRF токен (якщо є)
    csrf_token = re.search(r'name="_token"[^>]*value="([^"]*)"', login_page.text)
    token = csrf_token.group(1) if csrf_token else ""
    
    print("Крок 2: Виконуємо логін...")
    
    # Крок 2: Відправляємо дані логіну
    login_data = {
        'login': LOGIN,
        'password': PASSWORD,
        'remember': 'on'
    }
    if token:
        login_data['_token'] = token
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://vn.e-svitlo.com.ua',
        'Referer': LOGIN_URL,
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    login_response = session.post(LOGIN_URL, data=login_data, headers=headers, timeout=30, allow_redirects=True)
    print(f"Статус відповіді логіну: {login_response.status_code}")
    
    # Перевіряємо успішність логіну
    if "cabinet" in login_response.url or "account" in login_response.url:
        print("✅ Авторизація успішна!")
        return True
    elif "logout" in login_response.text.lower():
        print("✅ Авторизація успішна (logout знайдено)")
        return True
    else:
        print("❌ Логін не вдався. Перевіряємо cookies...")
        print(f"URL після логіну: {login_response.url}")
        print(f"Cookies: {len(session.cookies)} шт.")
        return False

def extract_json_from_html(html_content):
    """Витягуємо JSON з HTML (з тегів script)"""
    # Шукаємо JSON у <script> тегах
    json_matches = re.findall(r'var\s+(planned_list_cab|current_list_cab)\s*=\s*(\[.*?\]);?\s*</script>', html_content, re.DOTALL)
    
    planned_data = []
    for var_name, json_str in json_matches:
        if var_name == 'planned_list_cab':
            try:
                data = json.loads(json_str)
                planned_data.extend(data)
            except json.JSONDecodeError:
                continue
    
    return planned_data

def parse_outages(session):
    """Парсинг черг"""
    all_outages = []
    
    # Перевіряємо доступ до кабінету
    print("Перевіряємо доступ до кабінету...")
    check_page = session.get(MAIN_URL, timeout=30)
    print(f"Статус головної сторінки: {check_page.status_code}")
    
    for idx, url in enumerate(QUEUE_URLS, 1):
        print(f"\nОбробляємо чергу {idx}/12: {url.split('eic=')[1][:12]}...")
        
        try:
            time.sleep(2)  # Пауза між запитами
            response = session.get(url, timeout=30)
            
            if response.status_code != 200:
                print(f"  ❌ Помилка: {response.status_code}")
                continue
            
            print(f"  ✅ Статус: {response.status_code}")
            
            # Витягуємо JSON з HTML
            planned_list = extract_json_from_html(response.text)
            
            queue_outages = []
            for item in planned_list:
                acc_begin = item.get('acc_begin', '')
                accend_plan = item.get('accend_plan', '')
                
                if acc_begin and accend_plan:
                    queue_outages.append({
                        'queue': idx,
                        'acc_begin': acc_begin,
                        'accend_plan': accend_plan,
                        'eic': url.split('eic=')[1].split('&')[0]
                    })
            
            all_outages.extend(queue_outages)
            print(f"  📊 Знайдено {len(queue_outages)} планових відключень")
            
        except Exception as e:
            print(f"  ❌ Помилка черги {idx}: {str(e)[:100]}")
            continue
    
    print(f"\n🎉 Загалом знайдено {len(all_outages)} відключень")
    return all_outages

def main():
    session = create_session()
    
    try:
        # Авторизація
        if not
