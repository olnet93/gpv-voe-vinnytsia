def save_results(all_outages):
    """Зберегти результати у JSON GPV формат"""
    log("[SAVE] Transforming and writing GPV format")
    
    # Отримати поточний час у Kyiv timezone
    kyiv_now = datetime.now(KYIV_TZ)
    
    # -----------------------------------------------------------
    # ЗМІНА: Використовуємо Unix timestamp (integer)
    # Це число секунд від 1970-01-01 UTC.
    # Це універсальний формат, який не залежить від таймзони сервера.
    # -----------------------------------------------------------
    last_updated_ts = int(kyiv_now.timestamp())

 - name: Debug - Check files
        run: |
          echo "=== PWD ==="
          pwd
          echo "=== LS scripts/ ==="
          ls -la scripts/
          echo "=== CONTENT of parser.py ==="
          cat scripts/parser.py
    
    # Текстова дата оновлення для відображення людям (залишається по Києву)
    update_fact_str = kyiv_now.strftime('%d.%m.%Y %H:%M')
    
    # Трансформуємо дані
    fact_data = transform_to_gpv(all_outages, kyiv_now)
    
    # Отримуємо сьогоднішню дату як Unix timestamp
    today_date = kyiv_now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=KYIV_TZ)
    today_ts = int(today_date.timestamp())
    
    # Створюємо структуру
    result = {
        "regionId": "vinnytsia",
        "lastUpdated": last_updated_ts, # Тепер це число (наприклад, 1765152072)
        "fact": {
            "data": fact_data,
            "update": update_fact_str,
            "today": today_ts
        },
        "preset": {
            "days": {
                "1": "Понеділок",
                "2": "Вівторок",
                "3": "Середа",
                "4": "Четвер",
                "5": "П'ятниця",
                "6": "Субота",
                "7": "Неділя"
            },
            "sch_names": {
                "GPV1.1": "Черга 1.1",
                "GPV1.2": "Черга 1.2",
                "GPV2.1": "Черга 2.1",
                "GPV2.2": "Черга 2.2",
                "GPV3.1": "Черга 3.1",
                "GPV3.2": "Черга 3.2",
                "GPV4.1": "Черга 4.1",
                "GPV4.2": "Черга 4.2",
                "GPV5.1": "Черга 5.1",
                "GPV5.2": "Черга 5.2",
                "GPV6.1": "Черга 6.1",
                "GPV6.2": "Черга 6.2"
            },
            "updateFact": update_fact_str
        },
        "lastUpdateStatus": {
            "status": "parsed",
            "ok": True,
            "code": 200,
            "message": None,
            "at": last_updated_ts, # Також замінили на timestamp для консистентності
            "attempt": 1
        },
        "regionAffiliation": "Вінницька область"
    }
    
    # Розраховуємо хеш контенту (факт даних)
    fact_data_str = json.dumps(result['fact']['data'], sort_keys=True, ensure_ascii=False)
    content_hash = calculate_hash(fact_data_str)
    
    # Додаємо мета інформацію
    result["meta"] = {
        "schemaVersion": "1.0.0",
        "contentHash": content_hash
    }
    
    # Створити папку data якщо не існує
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        log("[SAVE] Created directory: " + data_dir)
    
    # Записати файл у папку data
    file_path = os.path.join(data_dir, "Vinnytsiaoblenerho.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    log("[SAVE] Success: Saved to " + file_path)
    log(f"[SAVE] Total dates: {len(fact_data)}, Queues per date: {len(ALL_QUEUE_KEYS)}, Content hash: {content_hash}")
