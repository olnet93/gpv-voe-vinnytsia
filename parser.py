import json
import os
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

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

def main():
    print("🚀 gpv-voe-vinnytsia Playwright парсер")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='uk-UA',
            timezone_id='Europe/Kiev'
        )
        page = context.new_page()

        try:
            print("🔐 Авторизація...")
            page.goto("https://vn.e-svitlo.com.ua/user/login", wait_until="domcontentloaded")
            
            # Спробуємо різні селектори для логіну
            login_selectors = ['input[name="login"]', 'input[type="email"]', 'input[placeholder*="логін"]']
            password_selectors = ['input[name="password"]', 'input[type="password"]']
            
            login_input = None
            for selector in login_selectors:
                if page.locator(selector).count() > 0:
                    login_input = page.locator(selector)
                    print(f"Знайдено поле логіну: {selector}")
                    break
            
            password_input = None
            for selector in password_selectors:
                if page.locator(selector).count() > 0:
                    password_input = page.locator(selector)
                    print(f"Знайдено поле паролю: {selector}")
                    break
            
            if not login_input or not password_input:
                print("❌ Не знайдено поля для логіну/паролю")
                page.screenshot(path="error_login.png")
                return
            
            login_input.fill(LOGIN)
            time.sleep(1)
            password_input.fill(PASSWORD)
            time.sleep(1)
            
            # Шукаємо кнопку входу
            submit = page.locator('button[type="submit"], input[type="submit"], button:has-text("Вхід")')
            submit.click()
            
            print("⏳ Чекаємо авторизацію...")
            page.wait_for_timeout(5000)
            
            print(f"URL після логіну: {page.url}")
            page.screenshot(path="after_login.png")
            
            all_outages = []
            for idx, url in enumerate(QUEUE_URLS, 1):
                print(f"⏳ Черга {idx}/12")
                page.goto(url, wait_until="domcontentloaded")
                time.sleep(2)
                
                # Шукаємо planned_list_cab у скриптах
                scripts = page.locator('script').all()
                for script in scripts:
                    content = script.inner_text()
                    if 'planned_list_cab' in content:
                        print(f"Знайдено planned_list_cab у черзі {idx}")
                
                print(f"Черга {idx} оброблена")
            
            # Зберігаємо результат (поки порожній)
            result = {
                "last_updated": datetime.now().isoformat(),
                "total_outages": len(all_outages),
                "outages": all_outages,
                "status": "Авторизація пройшла"
            }
            
            with open("outages.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print("✅ Дані збережено!")
            
        except Exception as e:
            print(f"💥 Помилка: {e}")
            page.screenshot(path="error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    main()
