import os
import json
import requests

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

LOGIN_URL = "https://vn.e-svitlo.com.ua/site/login"

def login(session, login, password):
    session.get(LOGIN_URL)
    payload = {"LoginForm[username]": login, "LoginForm[password]": password}
    r = session.post(LOGIN_URL, data=payload)
    return "logout" in r.text.lower()

def fetch():
    session = requests.Session()
    if not login(session, os.getenv("ESVITLO_LOGIN"), os.getenv("ESVITLO_PASSWORD")):
        raise Exception("Login failed")

    result = []

    for url in URLS:
        r = session.get(url)
        try:
            data = r.json()
            for it in data.get("planned_list_cab", []):
                result.append({
                    "acc_begin": it.get("acc_begin"),
                    "accend_plan": it.get("accend_plan"),
                    "url": url
                })
        except:
            pass

    Path("data").mkdir(exist_ok=True)
    with open("data/disconnections.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    fetch()
