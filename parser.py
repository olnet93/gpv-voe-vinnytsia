#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
from datetime import datetime
from pathlib import Path

# Конфігурація
LOGIN = os.getenv('ESVITLO_LOGIN')
PASSWORD = os.getenv('ESVITLO_PASSWORD')
EICS = os.getenv('ESVITLO_EICS', '').split(',')

BASE_URL = 'https://vn.e-svitlo.com.ua'
API_ENDPOINT = f'{BASE_URL}/api/planned_list_cab'

DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = DATA_DIR / 'Vinnytsiaoblenerho.json'

session = requests.Session()

def authenticate():
    """Авторизація через multipart/form-data"""
    auth_url = f'{BASE_URL}/api/auth'
    
    data = {
        'login': LOGIN,
        'password': PASSWORD
    }
    
    try:
        response = session.post(auth_url, data=data)
        if response.status_code == 200:
            print("✅ Авторизація успішна")
            return True
        else:
            print(f"❌ Помилка авторизації: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Помилка підключення: {e}")
        return False

def fetch_schedules(eic):
    """Отримати графік для конкретного EIC"""
    try:
        params = {'eic': eic}
        response = session.get(API_ENDPOINT, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and 'planned_list_cab' in data:
                return data['planned_list_cab']
        
        return []
    except Exception as e:
        print(f"⚠️ Помилка при отриманні даних для {eic}: {e}")
        return []

def parse_all_eics():
    """Парсити дані для всіх EIC"""
    all_data = {
        "region": "Вінницька область",
        "updated_at": datetime.now().isoformat(),
        "schedules": []
    }
    
    if not EICS or EICS == ['']:
        print("⚠️ Не задано ESVITLO_EICS. Використовую дефолтні...")
        EICS = [
            '62Z2780989447998',
        ]
    
    for eic in EICS:
        eic = eic.strip()
        if not eic:
            continue
        
        print(f"📡 Отримую дані для {eic}...")
        schedules = fetch_schedules(eic)
        
        if schedules:
            for schedule in schedules:
                all_data['schedules'].append({
                    'typeId': schedule.get('typeId'),
                    'accBegin': schedule.get('accBegin'),
                    'accEndPlan': schedule.get('accEndPlan')
                })
            print(f"✅ {eic}: {len(schedules)} записів")
        else:
            print(f"⚠️ {eic}: немає даних")
    
    return all_data

def save_data(data):
    """Зберегти дані у JSON"""
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Дані збережені: {OUTPUT_FILE}")
        return True
    except Exception as e:
        print(f"❌ Помилка запису файлу: {e}")
        return False

def main():
    print("🔌 Вінниця e-svitlo Parser")
    print("=" * 50)
    
    if not LOGIN or not PASSWORD:
        print("❌ Не задано ESVITLO_LOGIN або ESVITLO_PASSWORD")
        return
    
    if not authenticate():
        return
    
    print("\n📊 Отримування графіків...")
    data = parse_all_eics()
    
    print(f"\n💾 Всього записів: {len(data['schedules'])}")
    
    if save_data(data):
        print("✅ Парсинг завершено успішно!")
    else:
        print("❌ Помилка під час збереження")

if __name__ == '__main__':
    main()
