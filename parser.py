import json
import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
import re

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

def login_and_parse():
    print("🚀 Запуск Playwright парсера...")
    
    # Запускаємо з XVFB для GitHub Actions
    env = os.environ.copy()
    env['DISPLAY'] = ':99'
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        context = browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='uk-UA',
            timezone_id='Europe/Kiev',
            extra_http_headers={
                'Accept-Language': 'uk-UA,uk;q=0.9,ru;q=0.8,en;q=0.7'
            }
        )
        page = context.new_page()
        
        try:
            print("🔐 Логін...")
            page.goto("https://vn.e-svitlo.com.ua/user/login", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_load_state("networkidle", timeout=30000)
            
            # Чекаємо форму логіну
            page.wait_for_selector('input[name="login"], input[type="email"], input[placeholder*="логін"]', timeout=10000)
            
            # Заповнюємо форму
            login_selector = 'input[name="login"], input[type="email"], input[placeholder*="логін"]'
            password_selector = 'input[name="password"], input[type="password"]'
            submit_selector = 'button[type="submit"], input[type="submit"], button:has-text("Вхід"), button:has-text("Увійти")'
            
            page.locator(login_selector).fill(LOGIN)
            time.sleep(1)
            page.locator(password_selector).fill(PASSWORD)
            time.sleep(1)
            page.locator(submit_selector).click()
            
            # Чекаємо успішний логін (перенаправлення)
            page.wait_for_url("**/account_household** || **/cabinet** || **/dashboard**", timeout=30000)
            print("✅ Авторизація успішна!")

            
            # Перевіряємо, що ми в кабінеті
            if page.locator('text=Вийти, logout').count() > 0:
                print("✅ Підтверджено: logout кнопка знайдена")
            
            all_outages = []
            
            # Парсимо кожну чергу
            for idx, url in enumerate(QUEUE_URLS, 1):
                print(f"\n⏳ Черга {idx}/12: {url.split('eic=')[1][:12]}...")
                
                try:
                    page.goto(url, wait_until="networkidle")
                    time.sleep(2)
                    
                    # Шукаємо JSON дані в <script> тегах
                    scripts = page.locator('script').all()
                    planned_data = []
                    
                    for script in scripts:
                        script_content = script.inner_text()
                        if 'planned_list_cab' in script_content:
                            # Витягуємо JSON з JavaScript
                            json_match = re.search(r'planned_list_cab\s*[:=]\s*(\[.*?\])', script_content, re.DOTALL)
                            if json_match:
                                try:
                                    data = json.loads(json_match.group(1))
                                    if isinstance(data, list):
                                        planned_data.extend(data)
                                except json.JSONDecodeError:
                                    continue
                    
                    # Обробляємо знайдені дані
                    queue_outages = []
                    for item in planned_data:
                        if isinstance(item, dict):
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
            print(f"💥 Помилка: {e}")
            page.screenshot(path="error.png")
            print("📸 Скріншот збережено")
            return False
        finally:
            browser.close()
            
            # Зберігаємо результат
            result = {
                "last_updated": datetime.now().isoformat(),
                "total_outages": len(all_outages),
                "outages": all_outages
            }
            
            with open("outages.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print("\n✅ Дані збережено в outages.json")
            return True
            
        except Exception as e:
            print(f"\n💥 Помилка: {e}")
            # Робимо скріншот для дебагу
            page.screenshot(path="error.png")
            print("📸 Зроблено скріншот: error.png")
            return False
        
        finally:
            browser.close()

def main():
    print("🚀 gpv-voe-vinnytsia Playwright парсер")
    success = login_and_parse()
    
    if not success:
        print("❌ Парсинг не вдалося завершити")
        exit(1)
    
    print("✅ Успішно завершено!")
    exit(0)

if __name__ == "__main__":
    main()
