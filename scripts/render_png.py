#!/usr/bin/env python3
"""
Schedule PNG Renderer - таблиця як HTML дизайн
"""

import json
import argparse
from pathlib import Path
import sys

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
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

SLOTS = [str(i) for i in range(1, 25)]
HOURS = ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
         '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
         '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
         '18:00', '19:00', '20:00', '21:00', '22:00', '23:00']

def draw_cell(ax, x, y, w, h, state):
    """Малювати клітинку з заливкою"""
    
    if state == 'no':
        bg = ORANGE
    elif state == 'first':
        bg = LIGHT_GRAY  # ліва половина буде оранжева
    elif state == 'second':
        bg = LIGHT_GRAY  # права половина буде оранжева
    else:
        bg = WHITE
    
    # Основна клітинка
    rect = Rectangle((x, y), w, h, linewidth=1, edgecolor=DARK_GRAY, facecolor=bg)
    ax.add_patch(rect)
    
    # Половинки для first/second
    if state == 'first':
        # Ліва половина оранжева
        rect_left = Rectangle((x, y), w/2, h, linewidth=0, facecolor=ORANGE)
        ax.add_patch(rect_left)
    elif state == 'second':
        # Права половина оранжева
        rect_right = Rectangle((x + w/2, y), w/2, h, linewidth=0, facecolor=ORANGE)
        ax.add_patch(rect_right)

def render_schedule(json_path, gpv_key=None, day_arg=None, out_path=None):
    """Рендерити розклад у вигляді таблиці"""
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fact_data = data.get('fact', {}).get('data', {})
    sch_names = data.get('preset', {}).get('sch_names', {})
    last_updated = data.get('fact', {}).get('update', '')
    today_ts = str(data.get('fact', {}).get('today'))
    
    day_ts = str(int(today_ts) + 86400) if day_arg == 'tomorrow' else today_ts
    day_data = fact_data[day_ts]
    
    gpv_keys = [gpv_key] if gpv_key else sorted([k for k in day_data if k.startswith('GPV')])
    
    for gkey in gpv_keys:
        slots = day_data[gkey]
        queue_name = sch_names.get(gkey, gkey)
        
        # Таблична фігура
        fig, ax = plt.subplots(figsize=(14, 4), dpi=100)
        fig.patch.set_facecolor(WHITE)
        ax.set_facecolor(WHITE)
        
        cell_w = 1
        cell_h = 1
        
        # Малювати слоти
        for i, slot in enumerate(SLOTS):
            state = slots.get(slot, 'yes')
            draw_cell(ax, i, 0, cell_w, cell_h, state)
        
        ax.set_xlim(-0.5, 24)
        ax.set_ylim(-0.8, 1.2)
        ax.set_aspect('equal')
        
        # Верхня вісь - години
        ax.set_xticks(np.arange(24) + 0.5)
        ax.set_xticklabels(HOURS, fontsize=8, rotation=0)
        ax.tick_params(axis='x', top=True, labeltop=True, bottom=False, labelbottom=False)
        
        # Видалити ліву вісь
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Заголовок
        title = f"Графік відключень ({queue_name})"
        if day_arg == 'tomorrow':
            title += " — завтра"
        else:
            title += " — сьогодні"
        
        fig.suptitle(title, fontsize=13, fontweight='bold', y=0.97)
        
        if last_updated:
            fig.text(0.5, 0.90, f"Дата та час: {last_updated}", 
                    ha='center', fontsize=8, color='#666666')
        
        # Легенда внизу
        ax_leg = fig.add_axes([0.08, 0.02, 0.84, 0.12])
        ax_leg.set_xlim(0, 10)
        ax_leg.set_ylim(0, 1)
        ax_leg.axis('off')
        
        # Елементи легенди
        legends = [
            (0.3, 'yes', 'Світло є'),
            (2.2, 'no', 'Світла нема'),
            (4.2, 'first', 'Світла нема перші 30 хв.'),
            (7.0, 'second', 'Світла нема другі 30 хв.')
        ]
        
        cell_size = 0.25
        
        for x, state, label in legends:
            draw_cell(ax_leg, x, 0.3, cell_size, cell_size, state)
            ax_leg.text(x + cell_size + 0.15, 0.425, label, fontsize=7.5, va='center')
        
        plt.tight_layout(rect=[0, 0.14, 1, 0.88])
        
        # Зберегти
        if out_path:
            out_p = Path(out_path)
            if out_p.suffix == '.png':
                output_file = out_p
            else:
                out_p.mkdir(parents=True, exist_ok=True)
                day_suffix = '_tomorrow' if day_arg == 'tomorrow' else '_today'
                output_file = out_p / f"{gkey}{day_suffix}.png"
        else:
            day_suffix = '_tomorrow' if day_arg == 'tomorrow' else '_today'
            output_file = Path(f"{gkey}{day_suffix}.png")
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_file, facecolor=WHITE, dpi=150, bbox_inches='tight', pad_inches=0.05)
        print(f"[OK] {output_file}")
        plt.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', required=True)
    parser.add_argument('--gpv', default=None)
    parser.add_argument('--day', default='today', choices=['today', 'tomorrow'])
    parser.add_argument('--out', default=None)
    args = parser.parse_args()
    
    render_schedule(args.json, args.gpv, args.day, args.out)
