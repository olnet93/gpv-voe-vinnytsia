import asyncio
from playwright.async_api import async_playwright
import json
import time

URLS = [
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
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z029828840776V&type_user=1&a=290637",
]

async def fetch_page(page, url):
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)
        text = await page.inner_text("body")
        return json.loads(text)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

async def main():
    all_results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.117 Safari/537.36"
        )
        page = await context.new_page()

        # ✅ Ручний stealth для Cloudflare
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
        """)

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
