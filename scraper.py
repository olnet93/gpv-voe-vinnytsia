import json
import os
import time
import requests

# URLs to parse
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

def fetch():
    cf_clearance = os.getenv("CF_CLEARANCE")
    ci_session = os.getenv("CI_SESSION")

    if not cf_clearance or not ci_session:
        raise Exception("Missing CF_CLEARANCE or CI_SESSION in environment!")

    session = requests.Session()
    session.cookies.set("cf_clearance", cf_clearance, domain="vn.e-svitlo.com.ua")
    session.cookies.set("ci_session", ci_session, domain="vn.e-svitlo.com.ua")

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    all_results = []

    for url in URLS:
        print(f"Fetching: {url}")
        r = session.get(url, headers=headers)

        if r.status_code != 200:
            print("Error:", r.status_code)
            continue

        try:
            data = r.json()
        except:
            print("Invalid JSON")
            continue

        if "planned_list_cab" in data and isinstance(data["planned_list_cab"], list):
            for item in data["planned_list_cab"]:
                all_results.append({
                    "acc_begin": item.get("acc_begin"),
                    "accend_plan": item.get("accend_plan"),
                    "queue": url,
                    "timestamp": int(time.time())
                })

    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=4, ensure_ascii=False)

    print("Saved to result.json")

if __name__ == "__main__":
    fetch()
