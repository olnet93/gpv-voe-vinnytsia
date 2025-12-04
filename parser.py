import requests
import json
import os
import time
import re
from datetime import datetime
from urllib.parse import urlparse

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
    """Створюємо сесію з браузерними заголовками"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'uk,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    return session

def login(session):
    """Авторизація через API endpoint"""
    print("🔐 Авторизація через /registr_all_user/login_all_user...")
    
    # Формуємо multipart/form-data майже так само, як браузер
    data = {
        "login": (None, LOGIN),
        "password": (None, PASSWORD),
    }
    
    headers = {
        "Origin": "https://vn.e-svitlo.com.ua",
        "Referer": "https://vn.e-svitlo.com.ua/user_register",
    }
    
    try:
        login_resp = session.post(
            "https://vn.e-svitlo.com.ua/registr_all_user/login_all_user",
            files=data,
            headers=headers,
            allow_redirects=True,
            timeout=30,
        )
        
        print(f"Статус логіну: {login_resp.status_code}")
        print(f"URL після логіну: {login_resp.url}")
        
        if login_resp.status_code not in (200, 302, 303):
            raise Exception(f"Login failed with status {login_resp.status_code}")
        
        cookies = session.cookies.get_dict()
        print(f"Cookies отримано: {list(cookies.keys())}")
        
        # Критичний cookie – session_id_ip_cabinet
        if "session_id_ip_cabinet" not in cookies:
            raise Exception("Login failed — no session_id_ip_cabinet cookie received")
        
        print("✅ Login OK (session_id_ip_cabinet отримано)")
        return True
        
    except Exception as e:
        print(f"❌ Помилка логіну: {e}")
        raise

def extract_planned_data(html_content):
    """Витягуємо planned_list_cab з HTML"""
    patterns = [
        r'var\s+planned_list_cab\s*=\s*(\[.*?\]);',
        r'planned_list_cab\s*:\s*(\[.*?\]),',
        r'"planned_list_cab"\s*:\s*(\[.*?\])(?:\s*,|\s*})'
    ]
    
    planned_data = []
    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                data = json.loads(match)
                if isinstance(data, list):
                    planned_data.extend(data)
            except json.JSONDecodeError:
                continue
    
    return planned_data

def parse_queue(session, url, queue_num):
    """Парсинг однієї черги"""
    try:
        time.sleep(1)
        response = session.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"  ❌ HTTP {response.status_code}")
            return []
        
        print(f"  ✅ HTTP {response.status_code}")
        
        # Витягуємо planned_list_cab
        planned_list = extract_planned_data(response.text)
        outages = []
        
        for item in planned_list:
            if isinstance(item, dict):
                acc_begin = item.get('acc_begin', '').strip()
                accend_plan = item.get('accend_plan', '').strip()
                
                if acc_begin and accend_plan:
                    outages.append({
                        'queue': queue_num,
                        'eic': urlparse(url).query.split('eic=')[1].split('&')[0],
                        'acc_begin': acc_begin,
                        'accend_plan': accend_plan
                    })
        
        print(f"  📊 {len(outages)} відключень")
        return outages
        
    except Exception as e:
        print(f"  ❌ Помилка: {str(e)[:50]}")
        return []

def main():
    print("🚀 gpv-voe-vinnytsia парсер (multipart login)")
    session = create_session()
    
    try:
        # Авторизація
        login(session)
        
        # Перевіряємо доступ до кабінету
        print("\n📋 Перевіряємо доступ до кабінету...")
        test_url = "https://vn.e-svitlo.com.ua/account_household"
        test_resp = session.get(test_url, timeout=10)
        print(f"Кабінет доступний: {test_resp.status_code}")
        
        # Парсимо черги
        print("\n🔍 Парсимо черги...")
        all_outages = []
        for idx, url in enumerate(QUEUE_URLS, 1):
            print(f"\n⏳ Черга {idx}/12")
            queue_outages = parse_queue(session, url, idx)
            all_outages.extend(queue_outages)
        
        # Зберігаємо результат
        result = {
            "last_updated": datetime.now().isoformat(),
            "total_outages": len(all_outages),
            "outages": all_outages
        }
        
        with open("outages.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 Збережено {len(all_outages)} відключень!")
        print(f"📄 outages.json оновлено")
        
    except Exception as e:
        print(f"\n💥 Помилка: {e}")
        exit(1)

if __name__ == "__main__":
    main()
