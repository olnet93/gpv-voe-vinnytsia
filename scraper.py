import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth
import json
import time

URLS = [
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z7056418802433&type_user=1&a=290637",
    "https://vn.e-svitlo.com.ua/account_household/show_only_disconnections?eic=62Z3790933130321&type_user=1&a=290637",
    # додайте інші URLи сюди
]

async def fetch_page(page, url):
    await page.goto(url, wait_until="networkidle")
    text = await page.inner_text("body")
    try:
        return json.loads(text)
    except:
        print("Error parsing JSON from", url)
        return None

async def main():
    all_results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # ✅ правильний виклик stealth
        await stealth(page)

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

    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)

    print("Saved to result.json")

if __name__ == "__main__":
    asyncio.run(main())
