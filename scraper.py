import os
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import sys
import time

LOGIN_URL = "https://vn.e-svitlo.com.ua/site/login"
# URL для перевірки авторизації (може бути головна сторінка після логіну або будь-яка сторінка яка вимагає сесію)
CHECK_URL = "https://vn.e-svitlo.com.ua/"  

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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": LOGIN_URL,
    "X-Requested-With": "XMLHttpRequest",
}

def debug_write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def extract_csrf_from_soup(soup):
    # Common names/places for CSRF in Yii and other frameworks
    # 1) hidden input named _csrf
    inp = soup.find("input", {"name": "_csrf"})
    if inp and inp.get("value"):
        return inp["value"]
    # 2) hidden input with name containing csrf
    for i in soup.find_all("input", type="hidden"):
        name = i.get("name", "")
        if "csrf" in name.lower() and i.get("value"):
            return i["value"]
    # 3) meta tag
    meta = soup.find("meta", {"name": "csrf-token"}) or soup.find("meta", {"name": "_csrf"})
    if meta and meta.get("content"):
        return meta["content"]
    return None

def login(session, login_val, password_val):
    print("GET login page...")
    r = session.get(LOGIN_URL, headers=HEADERS, timeout=30)
    print("Login page status:", r.status_code)
    debug_write(Path("debug") / "login_page.html", r.text[:200000])  # save first chunk for debugging

    soup = BeautifulSoup(r.text, "lxml")
    csrf = extract_csrf_from_soup(soup)
    if not csrf:
        # try cookie
        csrf = session.cookies.get("YII_CSRF_TOKEN") or session.cookies.get("_csrf")
        print("CSRF from cookie (if any):", bool(csrf))

    print("CSRF token detected:", bool(csrf))
    if not csrf:
        print("Warning: no CSRF found in page or cookies. Server may use JS-based or different protection.")
        # still attempt without csrf if no token found
        payload = {
            "LoginForm[username]": login_val,
            "LoginForm[password]": password_val,
        }
    else:
        # include both typical field and _csrf just in case
        payload = {
            "_csrf": csrf,
            "YII_CSRF_TOKEN": csrf,
            "LoginForm[username]": login_val,
            "LoginForm[password]": password_val,
        }

    # There are sites that expect form to be sent as if from the original page:
    headers = HEADERS.copy()
    headers["Referer"] = LOGIN_URL
    # POST the form
    print("POSTing login form...")
    r2 = session.post(LOGIN_URL, data=payload, headers=headers, allow_redirects=True, timeout=30)
    print("POST status:", r2.status_code)
    debug_write(Path("debug") / "login_response.html", r2.text[:200000])

    # Check cookies and a try to GET a protected page
    print("Cookies after POST:", session.cookies.get_dict())
    # Heuristic checks
    if "logout" in r2.text.lower() or login_val.lower() in r2.text.lower():
        print("Detected logout or email text on response -> login OK")
        return True

    # Try to access a known page that requires auth
    try:
        r_check = session.get(CHECK_URL, headers=HEADERS, timeout=30)
        print("Check page status:", r_check.status_code)
        if "logout" in r_check.text.lower() or login_val.lower() in r_check.text.lower():
            print("Access to check page shows logged-in content -> login OK")
            debug_write(Path("debug") / "check_page.html", r_check.text[:200000])
            return True
        else:
            debug_write(Path("debug") / "check_page.html", r_check.text[:200000])
    except Exception as e:
        print("Error while checking authenticated page:", e)

    return False


def fetch():
    login_val = os.getenv("ESVITLO_LOGIN")
    pass_val = os.getenv("ESVITLO_PASSWORD")

    if not login_val or not pass_val:
        raise SystemExit("Missing ESVITLO_LOGIN or ESVITLO_PASSWORD environment variables")

    session = requests.Session()
    session.headers.update(HEADERS)

    ok = login(session, login_val, pass_val)
    if not ok:
        # print helpful hints in the Action log
        print("Login failed. Debug files saved to debug/*.html. Possible causes:")
        print("- Incorrect secrets in repository settings")
        print("- Site uses captcha/2FA or blocks requests from GitHub Actions IPs")
        print("- CSRF token is generated by JavaScript or different field name")
        print("- Site expects additional headers (Origin) or an AJAX flow")
        raise Exception("Login failed")

    print("Login OK — fetching disconnections...")

    results = []
    for url in URLS:
        try:
            r = session.get(url, timeout=30)
            print("GET", url, "=>", r.status_code)
            # Try to parse as JSON
            try:
                data = r.json()
                for it in data.get("planned_list_cab", []):
                    results.append({
                        "acc_begin": it.get("acc_begin"),
                        "accend_plan": it.get("accend_plan"),
                        "url": url
                    })
            except ValueError:
                print("Non-JSON response for", url)
                # save for debugging
                debug_write(Path("debug") / f"response_{url.split('=')[-1]}.html", r.text[:200000])
        except Exception as e:
            print("Error fetching", url, e)

        # be polite
        time.sleep(1)

    Path("data").mkdir(exist_ok=True)
    with open("data/disconnections.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("Saved", len(results), "records to data/disconnections.json")


if __name__ == "__main__":
    try:
        fetch()
    except Exception as e:
        print("Fatal:", e)
        sys.exit(1)
