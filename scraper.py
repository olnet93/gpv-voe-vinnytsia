import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth
import json
import os
import time

# URLs для парсингу
URLS = [
    # 1 черга
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z7056418802433&type_user=1&a=290637",
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z3790933130321&type_user=1&a=290637",
    # 2 черга
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z8643921175882&type_user=1&a=290637",
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z6908816145370&type_user=1&a=290637",
    # 3 черга
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z122797640622H&type_user=1&a=290637",
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z923769103674C&type_user=1&a=290637",
    # 4 черга
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z595315443877G&type_user=1&a=290637",
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z1881561967951&type_user=1&a=290637",
    # 5 черга
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z7896315479246&type_user=1&a=290637",
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z2780989447998&type_user=1&a=290637",
    # 6 черга
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z9499016055016&type_user=1&a=290637",
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z029828840776V&type_user=1&a=290637",
]

async def fetch_page(page, url):
    await page.goto(url, wait_until="networkidle")
    content = await page.content()
    # Сторінка повертає JSON як текст
    text = await page.inner_text("body")
    try:
        data = json.loads(text)
        return data
    except:
        print("Error parsing JSON from", url)
        return None

async def main():
    all_results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await stealth(page)  # застосовуємо stealth для Cloudflare

        for url in URLS:
            print(f"Fetching: {url}")
            data = await fetch_page(page, url)
            if data and "planned_list_cab" in data:
                for item in data["planned_list_cab"]:
                    all_results.append({
                        "acc_begin": item.get("acc_begin"),
                        "accend_plan": item.get("accend_plan"),
                        "queue": url,
                        "timestamp": int(time.time())
                    })

        await browser.close()

    # Зберігаємо результат
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)

    print("Saved to result.json")

if __name__ == "__main__":
    asyncio.run(main())
