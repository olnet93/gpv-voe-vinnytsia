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
        
        # Створимо NumPy масив для таблиці
        # 3 рядки, 25 колонок (перша - лейбли, потім 24 слоти)
        table = np.zeros((3, 25, 3), dtype=np.uint8)  # RGB для кожної клітинки
        
        # Функція для конвертування кольору RGB у numpy значення
        def color_to_rgb(color_hex):
            color_hex = color_hex.lstrip('#')
            return tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        
        colors = {
            'yes': color_to_rgb(WHITE),
            'no': color_to_rgb(ORANGE),
            'first': color_to_rgb(LIGHT_GRAY),
            'second': color_to_rgb(LIGHT_GRAY),
            'header': color_to_rgb(HEADER_BG),
            'label': color_to_rgb(LIGHT_GRAY)
        }
        
        # РЯДОК 0: Заголовки
        # Колонка 0: Лейбл "Часові проміжки"
        table[0, 0] = colors['header']
        
        # Колонки 1-24: Години
        for i in range(24):
            table[0, i+1] = colors['header']
        
        # РЯДОК 1: Сьогодні
        # Колонка 0: Лейбл "6 грудня"
        table[1, 0] = colors['label']
        
        # Колонки 1-24: Слоти
        for i, slot in enumerate(SLOTS):
            state = today_slots.get(slot, 'yes')
            if state == 'first':
                # Ліва половина оранжева
                table[1, i+1] = colors['first']  # буде переписано для візуалізації
            elif state == 'second':
                # Права половина оранжева
                table[1, i+1] = colors['second']  # буде переписано для візуалізації
            else:
                table[1, i+1] = colors[state]
        
        # РЯДОК 2: Завтра
        # Колонка 0: Лейбл "7 грудня"
        table[2, 0] = colors['label']
        
        # Колонки 1-24: Слоти
        for i, slot in enumerate(SLOTS):
            state = tomorrow_slots.get(slot, 'yes')
            if state == 'first':
                table[2, i+1] = colors['first']
            elif state == 'second':
                table[2, i+1] = colors['second']
            else:
                table[2, i+1] = colors[state]
        
        # Створимо фігуру з точною висотою/шириною
        cell_size = 40  # пікселі
        fig_width = (25 * cell_size) / 100
        fig_height = (3 * cell_size) / 100
        
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=100)
        fig.patch.set_facecolor(WHITE)
        ax.set_facecolor(WHITE)
        
        # Малюємо таблицю без пробілів
        for row in range(3):
            for col in range(25):
                x = col
                y = 3 - row - 1  # Перевернемо Y
                
                # Визначимо кольір
                if col == 0:
                    # Ліва колонка з лейблами
                    color = HEADER_BG if row == 0 else LIGHT_GRAY
                    rect = Rectangle((x, y), 2.0, 1, linewidth=1, edgecolor=DARK_GRAY, facecolor=color)
                    ax.add_patch(rect)
                    
                    # Текст лейблу
                    if row == 0:
                        text = 'Часові проміжки'
                    elif row == 1:
                        text = '6 грудня'
                    else:
                        text = '7 грудня'
                    
                    ax.text(x + 1, y + 0.5, text, fontsize=9, ha='center', va='center', 
                           fontweight='bold', color=BLACK)
                    x += 1.0  # Компенсація за ширшу колонку
                    col_offset = 1.0
                else:
                    col_offset = 1.0
                    state_key = f"{row}_{col-1}"
                    
                    # Визначимо стан клітинки
                    if row == 0:
                        color = HEADER_BG
                        text = HOURS[col-1]
                    elif row == 1:
                        state = today_slots.get(str(col), 'yes')
                        if state == 'no':
                            color = ORANGE
                        elif state == 'first':
                            color = LIGHT_GRAY  # буде розділена
                        elif state == 'second':
                            color = LIGHT_GRAY  # буде розділена
                        else:
                            color = WHITE
                        text = None
                    else:  # row == 2
                        state = tomorrow_slots.get(str(col), 'yes')
                        if state == 'no':
                            color = ORANGE
                        elif state == 'first':
                            color = LIGHT_GRAY  # буде розділена
                        elif state == 'second':
                            color = LIGHT_GRAY  # буде розділена
                        else:
                            color = WHITE
                        text = None
                    
                    rect = Rectangle((x, y), 1, 1, linewidth=1, edgecolor=DARK_GRAY, facecolor=color)
                    ax.add_patch(rect)
                    
                    # Половинки для first/second
                    if row > 0:
                        if row == 1:
                            state = today_slots.get(str(col), 'yes')
                        else:
                            state = tomorrow_slots.get(str(col), 'yes')
                        
                        if state == 'first':
                            # Ліва половина оранжева
                            rect_half = Rectangle((x, y), 0.5, 1, linewidth=0, facecolor=ORANGE)
                            ax.add_patch(rect_half)
                        elif state == 'second':
                            # Права половина оранжева
                            rect_half = Rectangle((x + 0.5, y), 0.5, 1, linewidth=0, facecolor=ORANGE)
                            ax.add_patch(rect_half)
                    
                    # Текст години
                    if row == 0:
                        ax.text(x + 0.5, y + 0.5, text, fontsize=6, ha='center', va='center',
                               color=BLACK, rotation=90, fontweight='bold')
        
        ax.set_xlim(0, 26)
        ax.set_ylim(0, 3)
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Заголовок і дата
        fig.text(0.5, 0.97, f"Графік відключень: {queue_name}", 
                fontsize=12, fontweight='bold', ha='center')
        
        if last_updated:
            fig.text(0.5, 0.92, f"Дата та час: {last_updated}", 
                    ha='center', fontsize=8, color='#666666')
        
        # Легенда
        legend_text = "Світло є  |  Світла нема  |  Перші 30 хв.  |  Другі 30 хв."
        fig.text(0.5, 0.05, legend_text, ha='center', fontsize=8)
        
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
