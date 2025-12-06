#!/usr/bin/env python3
"""
Schedule PNG Renderer - таблиця як на картинці
"""

import json
import argparse
from pathlib import Path
import sys

try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    from matplotlib.table import Table
    import numpy as np
except ImportError:
    print("ERROR: pip install matplotlib")
    sys.exit(1)

BLUE_LIGHT = '#B8D4E8'
BLUE_DARK = '#4472C4'
YELLOW = '#FFD966'
WHITE = '#FFFFFF'
GRAY_HEADER = '#EEEEEE'
BORDER = '#000000'

SLOTS = list(range(24))
HOURS = [f'{i:02d}-{i+1:02d}' for i in range(24)]

def render_schedule(json_path, gpv_key=None, out_path=None):
    """Рендерити розклад"""
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fact_data = data.get('fact', {}).get('data', {})
    sch_names = data.get('preset', {}).get('sch_names', {})
    last_updated = data.get('fact', {}).get('update', '')
    today_ts = str(data.get('fact', {}).get('today'))
    tomorrow_ts = str(int(today_ts) + 86400)
    
    today_data = fact_data.get(today_ts, {})
    tomorrow_data = fact_data.get(tomorrow_ts, {})
    
    gpv_keys = [gpv_key] if gpv_key else sorted([k for k in today_data if k.startswith('GPV')])
    
    for gkey in gpv_keys:
        today_slots = today_data.get(gkey, {str(i): 'yes' for i in range(1, 25)})
        tomorrow_slots = tomorrow_data.get(gkey, {str(i): 'yes' for i in range(1, 25)})
        queue_name = sch_names.get(gkey, gkey)
        
        fig, ax = plt.subplots(figsize=(18, 5), dpi=100)
        fig.patch.set_facecolor(WHITE)
        ax.axis('off')
        
        # Дані таблиці: 3 рядки (заголовок часів, сьогодні, завтра) + 25 колонок (дата/назва + 24 часи)
        table_data = []
        
        # Рядок 1: Заголовки (дата + години)
        header_row = ['Дата']
        for h in HOURS:
            header_row.append(h)
        table_data.append(header_row)
        
        # Рядок 2: Сьогодні
        today_row = ['06 грудня']
        for i in range(1, 25):
            slot_key = str(i)
            state = today_slots.get(slot_key, 'yes')
            today_row.append(state)
        table_data.append(today_row)
        
        # Рядок 3: Завтра
        tomorrow_row = ['07 грудня']
        for i in range(1, 25):
            slot_key = str(i)
            state = tomorrow_slots.get(slot_key, 'yes')
            tomorrow_row.append(state)
        table_data.append(tomorrow_row)
        
        # Створюємо таблицю
        table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                        colWidths=[0.08] + [0.034]*24)  # Ліва колонка ширша
        
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 2.5)  # Масштабування: ширина, висота
        
        # Форматування клітинок
        for i in range(3):  # 3 рядки
            for j in range(25):  # 25 колонок
                cell = table[(i, j)]
                cell.set_edgecolor(BORDER)
                cell.set_linewidth(0.5)
                
                if i == 0:  # Заголовок
                    cell.set_facecolor(GRAY_HEADER)
                    cell.set_text_props(weight='bold', fontsize=7)
                    cell.set_height(0.15)
                else:  # Дані
                    if j == 0:  # Лева колонка (дати)
                        cell.set_facecolor(GRAY_HEADER)
                        cell.set_text_props(weight='bold')
                    else:  # Клітинки зі станами
                        state = table_data[i][j]
                        
                        if state == 'no':
                            cell.set_facecolor(BLUE_DARK)
                        elif state == 'first':
                            cell.set_facecolor(YELLOW)
                        elif state == 'second':
                            cell.set_facecolor(BLUE_LIGHT)
                        else:
                            cell.set_facecolor(WHITE)
                    
                    cell.set_height(0.12)
                    cell.set_text_props(fontsize=6)
        
        # Заголовок
        fig.text(0.1, 0.95, 'Графік відключень:', fontsize=16, fontweight='bold')
        
        # Етикетка черги
        fig.text(0.92, 0.95, queue_name, fontsize=12, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=YELLOW, edgecolor=BORDER, linewidth=2))
        
        # Легенда
        legend_y = 0.08
        fig.text(0.05, legend_y, '□ Світло є', fontsize=8)
        fig.text(0.2, legend_y, '■ Світла нема', fontsize=8)
        fig.text(0.35, legend_y, '■ Можливе відключення', fontsize=8)
        fig.text(0.53, legend_y, '■ Світла не буде перші 30 хв.', fontsize=8)
        fig.text(0.73, legend_y, '■ Світла не буде другі 30 хв.', fontsize=8)
        
        # Дата оновлення
        if last_updated:
            fig.text(0.95, 0.01, f'Опубліковано {last_updated}', fontsize=7, ha='right', style='italic')
        
        plt.tight_layout()
        
        # Зберегти
        if out_path:
            out_p = Path(out_path)
            if out_p.suffix == '.png':
                output_file = out_p
            else:
                out_p.mkdir(parents=True, exist_ok=True)
                output_file = out_p / f"{gkey}.png"
        else:
            output_file = Path(f"{gkey}.png")
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_file, facecolor=WHITE, dpi=150, bbox_inches='tight', pad_inches=0.1)
        print(f"[OK] {output_file}")
        plt.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', required=True)
    parser.add_argument('--gpv', default=None)
    parser.add_argument('--out', default=None)
    args = parser.parse_args()
    
    render_schedule(args.json, args.gpv, args.out)
