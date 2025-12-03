import os
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

LOGIN_URL = "https://vn.e-svitlo.com.ua/site/login"

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


def login(session, login, password):
    # GET login page to get CSRF token
    r = session.get(LOGIN_URL)
    soup = BeautifulSoup(r.text, "lxml")

    token_input = soup.find("input", {"name": "_csrf"})
    if not token_input:
        return False

    csrf = token_input["value"]

    payload = {
        "_csrf": csrf,
        "LoginForm[username]": login,
        "LoginForm[password]": password,
    }

    r = session.post(LOGIN_URL, data=payload, allow_redirects=True)

    return "logout" in r.text.lower()


def fetch():
    session = requests.Session()

    login_ok = login(
        session,
        os.getenv("ESVITLO_LOGIN"),
        os.getenv("ESVITLO_PASSWORD")
    )

    if not login_ok:
        raise Exception("Login failed: incorrect credentials or CSRF")

    results = []

    for url in URLS:
        r = session.get(url)
        try:
            data = r.json()
            for it in data.get("planned_list_cab", []):
                results.append({
                    "acc_begin": it.get("acc_begin"),
                    "accend_plan": it.get("accend_plan"),
                    "url": url
                })
        except Exception as e:
            print("Error parsing URL", url, e)

    Path("data").mkdir(exist_ok=True)
    with open("data/disconnections.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    fetch()
