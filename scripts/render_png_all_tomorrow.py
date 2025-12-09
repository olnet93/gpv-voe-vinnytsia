#!/usr/bin/env python3
"""
Schedule PNG Renderer - таблиця усіх графіків на завтра
Шукає дані строго за календарною датою "завтра" (Київський час).
"""

import json
import argparse
from pathlib import Path
import sys
from datetime import datetime, timezone, timedelta
import hashlib

try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    import numpy as np
except ImportError:
    print("ERROR: pip install matplotlib")
    sys.exit(1)

ORANGE = '#FF8C00'
WHITE = '#FFFFFF'
GRAY_HEADER = '#E7E6E6'
GRAY_LABEL = '#D9D9D9'
BORDER = '#808080'

SLOTS = list(range(1, 25))
HOURS = [f'{i:02d}-{i+1:02d}' for i in range(24)]

# Таймзона Київ (зимовий UTC+2, літній UTC+3)
# Для простоти беремо UTC+2 (зимовий), оскільки нам важлива лише дата
KYIV_OFFSET = timedelta(hours=2)
KYIV_TZ = timezone(KYIV_OFFSET)

def calculate_all_tomorrow_hash(tomorrow_data):
    """Розраховує SHA256 хеш всіх даних на завтра"""
    data_str = json.dumps(tomorrow_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(data_str.encode()).hexdigest()

def load_previous_hash(hash_dir):
    """Завантажує попередній хеш з папки hash/"""
    hash_file = hash_dir / 'gpv-all-tomorrow.hash'
    if hash_file.exists():
        try:
            with open(hash_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception:
            pass
    return None

def save_hash(hash_dir, data_hash):
    """Зберігає хеш даних у папку hash/"""
    hash_dir.mkdir(parents=True, exist_ok=True)
    hash_file = hash_dir / 'gpv-all-tomorrow.hash'
    try:
        with open(hash_file, 'w', encoding='utf-8') as f:
            f.write(data_hash)
    except Exception as e:
        print(f"[WARN] Could not save hash: {e}")

def find_tomorrow_key(data_dict):
    """
    Шукає в словнику ключ (timestamp), який відповідає ЗАВТРАШНІЙ даті
    відносно реального часу в Київі.
    Впорається з науковою нотацією ключів (1.7652312e+09).
    """
    now_utc = datetime.now(timezone.utc)
    now_kyiv = now_utc + KYIV_OFFSET
    tomorrow_kyiv = now_kyiv + timedelta(days=1)
    
    target_day = tomorrow_kyiv.day
    target_month = tomorrow_kyiv.month

    for key in data_dict.keys():
        # Спробуємо конвертувати ключ у число, незалежно від формату
        try:
            ts = int(float(key))  # Впорається з "1.7652312e+09" та "1765231200"
        except (ValueError, TypeError):
            continue
        
        key_date = datetime.fromtimestamp(ts, KYIV_TZ)
        
        if key_date.day == target_day and key_date.month == target_month:
            return key, key_date

    return None, None

def render_all_tomorrow_schedules(json_path, out_path=None):
    """Рендерити всі графіки на завтра в одну таблицю"""
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fact_data = data.get('fact', {}).get('data', {})
    sch_names = data.get('preset', {}).get('sch_names', {})
    last_updated = data.get('fact', {}).get('update', '')
    
    # === ГОЛОВНА ЗМІНА: Шукаємо ключ для завтра ===
    tomorrow_ts, tomorrow_date = find_tomorrow_key(fact_data)
    
    if not tomorrow_ts:
        print(f"[SKIP] gpv-all-tomorrow.png (No data found for tomorrow yet)")
        return

    tomorrow_data = fact_data.get(tomorrow_ts, {})
    
    # Перевіряємо, чи є всередині графіки GPV (а не просто пустий об'єкт)
    gpv_keys = sorted([k for k in tomorrow_data if k.startswith('GPV')])
    if not gpv_keys:
        print(f"[SKIP] gpv-all-tomorrow.png (Timestamp {tomorrow_ts} exists but represents empty data)")
        return
    
    # Налаштування шляхів
    if out_path:
        out_p = Path(out_path)
        out_p.mkdir(parents=True, exist_ok=True)
        hash_dir = out_p / 'hash'
    else:
        out_p = Path('.')
        hash_dir = out_p / 'hash'
    
    # === ПЕРЕВІРКА ХЕШУ ===
    new_hash = calculate_all_tomorrow_hash(tomorrow_data)
    prev_hash = load_previous_hash(hash_dir)
    output_file = out_p / 'gpv-all-tomorrow.png'
    
    if new_hash == prev_hash and output_file.exists():
        print(f"[SKIP] gpv-all-tomorrow.png (Data for tomorrow unchanged)")
        return
    
    print(f"[GENERATE] gpv-all-tomorrow.png for {tomorrow_date.strftime('%d.%m')}")
    
    # === ДАЛІ ЙДЕ КОД РЕНДЕРИНГУ ===
    # Форматуємо дату для заголовка
    months_uk = {
        1: 'січня', 2: 'лютого', 3: 'березня', 4: 'квітня',
        5: 'травня', 6: 'червня', 7: 'липня', 8: 'серпня',
        9: 'вересня', 10: 'жовтня', 11: 'листопада', 12: 'грудня'
    }
    tomorrow_str = f'{tomorrow_date.day:02d} {months_uk[tomorrow_date.month]}'
    
    num_schedules = len(gpv_keys)
    
    # Розміри та налаштування графіку
    cell_w = 1.0
    cell_h = 0.5
    label_w = 2.0
    header_h = 1.2
    
    table_width = label_w + 24 * cell_w
    table_height = header_h + num_schedules * cell_h
    fig_height = 1.5 + (num_schedules * 0.5)
    
    fig, ax = plt.subplots(figsize=(20, fig_height), dpi=100)
    fig.patch.set_facecolor(WHITE)
    ax.set_facecolor(WHITE)
    
    y_pos = 0
    
    # Заголовок таблиці
    rect = Rectangle((0, y_pos), label_w, header_h, linewidth=1, edgecolor=BORDER, facecolor=GRAY_HEADER)
    ax.add_patch(rect)
    ax.text(label_w/2, y_pos + header_h/2, 'Черга', fontsize=12, ha='center', va='center', fontweight='bold')
    
    for i in range(24):
        x = label_w + i * cell_w
        rect = Rectangle((x, y_pos), cell_w, header_h, linewidth=1, edgecolor=BORDER, facecolor=GRAY_HEADER)
        ax.add_patch(rect)
        ax.text(x + cell_w/2, y_pos + header_h/2, HOURS[i], fontsize=10, ha='center', va='center', fontweight='bold')
    
    y_pos += header_h
    
    # Рядки графіків
    for gpv_key in gpv_keys:
        slots = tomorrow_data.get(gpv_key, {str(i): 'yes' for i in range(1, 25)})
        queue_name = sch_names.get(gpv_key, gpv_key)
        
        rect = Rectangle((0, y_pos), label_w, cell_h, linewidth=1, edgecolor=BORDER, facecolor=GRAY_LABEL)
        ax.add_patch(rect)
        ax.text(label_w/2, y_pos + cell_h/2, queue_name, fontsize=10, ha='center', va='center', fontweight='bold')
        
        for i, slot_num in enumerate(SLOTS):
            x = label_w + i * cell_w
            slot_key = str(slot_num)
            state = slots.get(slot_key, 'yes')
            
            # Фон (білий = світло є)
            rect = Rectangle((x, y_pos), cell_w, cell_h, linewidth=1, edgecolor=BORDER, facecolor=WHITE)
            ax.add_patch(rect)
            
            if state == 'no':
                rect_fill = Rectangle((x, y_pos), cell_w, cell_h, linewidth=0, facecolor=ORANGE)
                ax.add_patch(rect_fill)
            elif state == 'first':
                rect_left = Rectangle((x, y_pos), cell_w/2, cell_h, linewidth=0, facecolor=ORANGE)
                ax.add_patch(rect_left)
            elif state == 'second':
                rect_right = Rectangle((x + cell_w/2, y_pos), cell_w/2, cell_h, linewidth=0, facecolor=ORANGE)
                ax.add_patch(rect_right)
                
            # Повторний бордюр
            rect_border = Rectangle((x, y_pos), cell_w, cell_h, linewidth=1, edgecolor=BORDER, facecolor='none')
            ax.add_patch(rect_border)
        
        y_pos += cell_h
    
    # Налаштування осей
    ax.set_xlim(0, table_width)
    ax.set_ylim(0, table_height)
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.margins(0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Текст заголовка
    fig.text(0.15, 0.97, f'Графік відключень для Вінницька область на {tomorrow_str}', 
            fontsize=18, fontweight='bold')
            
    # Легенда
    legend_y = 0.005
    legend_x_center = 0.35
    table_fig_width = 0.9 - 0.05
    cell_w_fig = table_fig_width / table_width
    cell_h_fig = (0.85 - 0.15) / table_height * cell_h
    spacing = 0.09
    
    # Легенда 1: Білий (світло є)
    x1 = legend_x_center - 1.8 * spacing
    rect = Rectangle((x1 - cell_w_fig/2, legend_y - cell_h_fig/2), cell_w_fig, cell_h_fig, 
                    linewidth=0.5, edgecolor=BORDER, facecolor=WHITE, transform=fig.transFigure, clip_on=False)
    fig.patches.append(rect)
    fig.text(x1 + cell_w_fig/2 + 0.005, legend_y, 'Світло є', fontsize=11, va='center')
    
    # Легенда 2: Повністю оранжева (світла нема)
    x2 = legend_x_center - 0.6 * spacing
    rect = Rectangle((x2 - cell_w_fig/2, legend_y - cell_h_fig/2), cell_w_fig, cell_h_fig, 
                    linewidth=0.5, edgecolor=BORDER, facecolor=ORANGE, transform=fig.transFigure, clip_on=False)
    fig.patches.append(rect)
    fig.text(x2 + cell_w_fig/2 + 0.005, legend_y, 'Світла нема', fontsize=11, va='center')
    
    # Легенда 3: Ліва половина оранжева (перші 30 хв)
    x3 = legend_x_center + 0.6 * spacing
    fig.patches.append(Rectangle((x3 - cell_w_fig/2, legend_y - cell_h_fig/2), cell_w_fig/2, cell_h_fig, linewidth=0, facecolor=WHITE, transform=fig.transFigure, clip_on=False))
    fig.patches.append(Rectangle((x3, legend_y - cell_h_fig/2), cell_w_fig/2, cell_h_fig, linewidth=0, facecolor=ORANGE, transform=fig.transFigure, clip_on=False))
    fig.patches.append(Rectangle((x3 - cell_w_fig/2, legend_y - cell_h_fig/2), cell_w_fig, cell_h_fig, linewidth=0.5, edgecolor=BORDER, facecolor='none', transform=fig.transFigure, clip_on=False))
    fig.text(x3 + cell_w_fig/2 + 0.005, legend_y, 'Світла нема\nперші 30 хв.', fontsize=11, va='center')

    # Легенда 4: Права половина оранжева (другі 30 хв)
    x4 = legend_x_center + 1.8 * spacing
    fig.patches.append(Rectangle((x4 - cell_w_fig/2, legend_y - cell_h_fig/2), cell_w_fig/2, cell_h_fig, linewidth=0, facecolor=ORANGE, transform=fig.transFigure, clip_on=False))
    fig.patches.append(Rectangle((x4, legend_y - cell_h_fig/2), cell_w_fig/2, cell_h_fig, linewidth=0, facecolor=WHITE, transform=fig.transFigure, clip_on=False))
    fig.patches.append(Rectangle((x4 - cell_w_fig/2, legend_y - cell_h_fig/2), cell_w_fig, cell_h_fig, linewidth=0.5, edgecolor=BORDER, facecolor='none', transform=fig.transFigure, clip_on=False))
    fig.text(x4 + cell_w_fig/2 + 0.005, legend_y, 'Світла нема\nдругі 30 хв.', fontsize=11, va='center')

    # Дата оновлення
    if last_updated:
        fig.text(0.8, 0.001, f'Опубліковано {last_updated}', fontsize=11, ha='right', style='italic')

    # Збереження
    plt.savefig(output_file, facecolor=WHITE, dpi=150, bbox_inches='tight', pad_inches=0.13)
    print(f"[OK] Saved {output_file}")
    
    save_hash(hash_dir, new_hash)
    plt.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', required=True)
    parser.add_argument('--out', default=None)
    args = parser.parse_args()
    
    render_all_tomorrow_schedules(args.json, args.out)
