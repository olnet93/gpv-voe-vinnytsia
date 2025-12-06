#!/usr/bin/env python3
"""
Schedule PNG Renderer - таблиця 3x24 без пробілів
"""

import json
import argparse
from pathlib import Path
import sys

try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    import numpy as np
except ImportError:
    print("ERROR: pip install matplotlib")
    sys.exit(1)

ORANGE = '#ff8c00'
WHITE = '#ffffff'
LIGHT_GRAY = '#f5f5f5'
DARK_GRAY = '#cccccc'
BLACK = '#000000'
HEADER_BG = '#eeeeee'

SLOTS = [str(i) for i in range(1, 25)]
HOURS = [f'{i:02d}:00-{i+1:02d}:00' for i in range(24)]

def render_schedule(json_path, gpv_key=None, out_path=None):
    """Рендерити розклад з 3 стрічками"""
    
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
        today_slots = today_data.get(gkey, {k: 'yes' for k in SLOTS})
        tomorrow_slots = tomorrow_data.get(gkey, {k: 'yes' for k in SLOTS})
        queue_name = sch_names.get(gkey, gkey)
        
        # Розміри в координатах
        cell_w = 1.0      # Звичайна ширина клітинки
        cell_h = 1.0      # Звичайна висота клітинки
        label_w = 3.0     # Ліва колонка в 3 рази ширше
        header_h = 3.0    # Верхня стрічка в 3 рази вища
        
        # Загальні розміри таблиці
        table_width = label_w + 24 * cell_w  # 27 одиниць
        table_height = header_h + 2 * cell_h  # 5 одиниць
        
        # figsize має відповідати пропорціям таблиці
        fig_width = 27  # 27 одиниці ширини
        fig_height = 5   # 5 одиниць висоти
        
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=100)
        fig.patch.set_facecolor(WHITE)
        ax.set_facecolor(WHITE)
        
        # Y позиція (зверху вниз, але в matplotlib це перевернуто)
        # Тому розраховуємо від низу вгору
        y = table_height - header_h  # Стрічка часів починається внизу (у matplotlib координатах)
        
        # === РЯДОК 0: Заголовки часів (ВЕРХНЯ стрічка) ===
        # Ліва клітинка (лейбл "Часові проміжки")
        rect = Rectangle((0, y), label_w, header_h, linewidth=1, edgecolor=DARK_GRAY, facecolor=HEADER_BG)
        ax.add_patch(rect)
        ax.text(label_w/2, y + header_h/2, 'Часові проміжки', fontsize=10, ha='center', va='center',
               fontweight='bold', color=BLACK)
        
        # Години (колонки 1-24)
        for i in range(24):
            x = label_w + i * cell_w
            rect = Rectangle((x, y), cell_w, header_h, linewidth=1, edgecolor=DARK_GRAY, facecolor=HEADER_BG)
            ax.add_patch(rect)
            ax.text(x + cell_w/2, y + header_h/2, HOURS[i], fontsize=6, ha='center', va='center',
                   color=BLACK, rotation=90, fontweight='bold')
        
        y -= header_h  # Переходимо нижче
        
        # === РЯДОК 1: Сьогодні ===
        # Ліва клітинка (лейбл "6 грудня")
        rect = Rectangle((0, y), label_w, cell_h, linewidth=1, edgecolor=DARK_GRAY, facecolor=LIGHT_GRAY)
        ax.add_patch(rect)
        ax.text(label_w/2, y + cell_h/2, '6 грудня', fontsize=10, ha='center', va='center',
               fontweight='bold', color=BLACK)
        
        # Слоти сьогодні
        for i, slot in enumerate(SLOTS):
            x = label_w + i * cell_w
            state = today_slots.get(slot, 'yes')
            
            # Визначимо колір
            if state == 'no':
                bg_color = ORANGE
            else:
                bg_color = WHITE
            
            rect = Rectangle((x, y), cell_w, cell_h, linewidth=1, edgecolor=DARK_GRAY, facecolor=bg_color)
            ax.add_patch(rect)
            
            # Половинки для first/second
            if state == 'first':
                # Ліва половина оранжева
                rect_half = Rectangle((x, y), cell_w/2, cell_h, linewidth=0, facecolor=ORANGE)
                ax.add_patch(rect_half)
            elif state == 'second':
                # Права половина оранжева
                rect_half = Rectangle((x + cell_w/2, y), cell_w/2, cell_h, linewidth=0, facecolor=ORANGE)
                ax.add_patch(rect_half)
        
        y -= cell_h
        
        # === РЯДОК 2: Завтра ===
        # Ліва клітинка (лейбл "7 грудня")
        rect = Rectangle((0, y), label_w, cell_h, linewidth=1, edgecolor=DARK_GRAY, facecolor=LIGHT_GRAY)
        ax.add_patch(rect)
        ax.text(label_w/2, y + cell_h/2, '7 грудня', fontsize=10, ha='center', va='center',
               fontweight='bold', color=BLACK)
        
        # Слоти завтра
        for i, slot in enumerate(SLOTS):
            x = label_w + i * cell_w
            state = tomorrow_slots.get(slot, 'yes')
            
            # Визначимо колір
            if state == 'no':
                bg_color = ORANGE
            else:
                bg_color = WHITE
            
            rect = Rectangle((x, y), cell_w, cell_h, linewidth=1, edgecolor=DARK_GRAY, facecolor=bg_color)
            ax.add_patch(rect)
            
            # Половинки для first/second
            if state == 'first':
                # Ліва половина оранжева
                rect_half = Rectangle((x, y), cell_w/2, cell_h, linewidth=0, facecolor=ORANGE)
                ax.add_patch(rect_half)
            elif state == 'second':
                # Права половина оранжева
                rect_half = Rectangle((x + cell_w/2, y), cell_w/2, cell_h, linewidth=0, facecolor=ORANGE)
                ax.add_patch(rect_half)
        
        # Встановлюємо межі координат
        ax.set_xlim(0, table_width)
        ax.set_ylim(0, table_height)
        ax.invert_yaxis()  # Перевернемо вісь Y щоб верхня стрічка була зверху
        
        ax.set_xticks([])
        ax.set_yticks([])
        ax.margins(0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Заголовок
        fig.text(0.5, 0.97, f"Графік відключень: {queue_name}", 
                fontsize=13, fontweight='bold', ha='center')
        
        if last_updated:
            fig.text(0.5, 0.92, f"Дата та час останнього оновлення інформації на графіку: {last_updated}", 
                    ha='center', fontsize=8, color='#666666')
        
        # Легенда
        fig.text(0.08, 0.02, "█ Світло є", fontsize=8, color=BLACK)
        fig.text(0.3, 0.02, "█ Світла нема", fontsize=8, color=BLACK)
        fig.text(0.52, 0.02, "■█ Перші 30 хв.", fontsize=8, color=BLACK)
        fig.text(0.73, 0.02, "█■ Другі 30 хв.", fontsize=8, color=BLACK)
        
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
        plt.savefig(output_file, facecolor=WHITE, dpi=150, bbox_inches='tight', pad_inches=0.02)
        print(f"[OK] {output_file}")
        plt.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', required=True)
    parser.add_argument('--gpv', default=None)
    parser.add_argument('--out', default=None)
    args = parser.parse_args()
    
    render_schedule(args.json, args.gpv, args.out)
