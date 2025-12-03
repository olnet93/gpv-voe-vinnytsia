import requests
import json
import os
import time
from datetime import datetime

# URL логіну
LOGIN_URL = "https://vn.e-svitlo.com.ua/user/login"
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

# Отримуємо логін і пароль з оточення (GitHub Secrets)
LOGIN = os.getenv("ESVITLO_LOGIN")
PASSWORD = os.getenv("ESVITLO_PASSWORD")

if not LOGIN or not PASSWORD:
    raise Exception("ESVITLO_LOGIN або ESVITLO_PASSWORD не встановлені в оточенні")

def login(session):
    """Авторизація на сайті"""
    login_data = {
        "login": LOGIN,
        "password": PASSWORD,
        "remember": "on"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://vn.e-svitlo.com.ua/user/login",
        "Origin": "https://vn.e-svitlo.com.ua"
    }
    response = session.post(LOGIN_URL, data=login_data, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Помилка логіну: {response.status_code}")
    if "logout" not in response.text.lower():
        raise Exception("Логін не виконано: немає logout у відповіді")
    print("Авторизація успішна")

def parse_outages(session):
    """Парсинг всіх черг і збір даних planned_list_cab"""
    all_outages = []

    for idx, url in enumerate(QUEUE_URLS, start=1):
        try:
            response = session.get(url)
            if response.status_code != 200:
                print(f"Помилка завантаження черги {idx}: {response.status_code}")
                continue

            # Припустимо, що сторінка повертає JSON або має JSON у відповіді
            # Якщо це HTML, потрібно парсити через BeautifulSoup
            # Тут приклад для JSON-відповіді (адаптуйте під реальну структуру)
            try:
                data = response.json()
            except json.JSONDecodeError:
                # Якщо це HTML, можна шукати JSON у тегах <script> або використовувати BeautifulSoup
                # Поки просто пропускаємо
                print(f"Черга {idx}: не вдалося розібрати JSON")
                continue

            # Витягуємо planned_list_cab
            planned_list = data.get("planned_list_cab", [])
            for item in planned_list:
                acc_begin = item.get("acc_begin")
                accend_plan = item.get("accend_plan")
                if acc_begin and accend_plan:
                    all_outages.append({
                        "queue": idx,
                        "acc_begin": acc_begin,
                        "accend_plan": accend_plan
                    })

            print(f"Черга {idx}: знайдено {len(planned_list)} планових відключень")
            time.sleep(1)  # Маленька пауза між запитами

        except Exception as e:
            print(f"Помилка при обробці черги {idx}: {e}")

    return all_outages

def main():
    session = requests.Session()
    try:
        login(session)
        outages = parse_outages(session)

        # Додаємо час останнього оновлення
        result = {
            "last_updated": datetime.now().isoformat(),
            "outages": outages
        }

        # Зберігаємо у файл
        with open("outages.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"Дані збережено: {len(outages)} відключень")

    except Exception as e:
        print(f"Помилка: {e}")
        exit(1)

if __name__ == "__main__":
    main()
