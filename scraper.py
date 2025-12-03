#!/usr/bin/env python3
import os, json, requests
from datetime import datetime

LOGIN = os.getenv("ESVITLO_LOGIN")
PASSWORD = os.getenv("ESVITLO_PASSWORD")

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

def fetch():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    })

    login_resp = session.post(
        "https://vn.e-svitlo.com.ua/registr_all_user/login_all_user",
        data={"login": LOGIN, "password": PASSWORD},
        allow_redirects=True
    )

    if login_resp.status_code not in (200,302,303):
        raise Exception(f"Login failed: {login_resp.status_code}")

    if "ci_session" not in session.cookies.get_dict():
        raise Exception("Login failed — session cookie missing")

    results = []
    for url in URLS:
        r = session.get(url)
        if r.status_code != 200:
            continue
        data = r.json()
        planned = data.get("planned_list_cab", [])
        for item in planned:
            results.append({
                "url": url,
                "acc_begin": item.get("acc_begin"),
                "accend_plan": item.get("accend_plan"),
            })

    os.makedirs("data", exist_ok=True)
    with open("data/output.json", "w", encoding="utf-8") as f:
        json.dump({
            "updated": datetime.now().isoformat(),
            "items": results
        }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    fetch()
