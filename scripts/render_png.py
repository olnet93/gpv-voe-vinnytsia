#!/usr/bin/env python3
"""
Schedule PNG Renderer - таблиця з 3 стрічками (сьогодні, завтра)
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta
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

KYIV_TZ = timezone(timedelta(hours=2))

def draw_cell(ax, x, y, w, h, state):
    """Малювати клітинку з заливкою"""
    
    if state == 'no':
        bg = ORANGE
    elif state == 'first':
        bg = LIGHT_GRAY
    elif state == 'second':
        bg = LIGHT_GRAY
    else:
        bg = WHITE
    
    rect = Rectangle((x, y), w, h, linewidth=1, edgecolor=DARK_GRAY, facecolor=bg)
    ax.add_patch(rect)
    
    if state == 'first':
        rect_left = Rectangle((x, y), w/2, h, linewidth=0, facecolor=ORANGE)
        ax.add_patch(rect_left)
    elif state == 'second':
        rect_right = Rectangle((x + w/2, y), w/2, h, linewidth=0, facecolor=ORANGE)
        ax.add_patch(rect_right)

def format_date(unix_ts):
    """Форматувати дату у форматі '6 грудня'"""
    months = ['січня', 'лютого', 'березня', 'квітня', 'травня', 'червня',
              'липня', 'серпня', 'вересня', 'жовтня', 'листопада', 'грудня']
    dt = datetime.fromtimestamp(int(unix_ts), tz=KYIV_TZ)
    day = dt.day
    month = months[dt.month - 1]
    return f"{day} {month}"

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
        
        # Таблична фігура з 3 стрічками
        fig, ax = plt.subplots(figsize=(16, 5), dpi=100)
        fig.patch.set_facecolor(WHITE)
        ax.set_facecolor(WHITE)
        
        cell_w = 1
        cell_h = 0.9
        row_gap = 0.15
        
        # Рядки: 0 - заголовки часів, 1 - сьогодні, 2 - завтра
        rows = [
            ('Часові проміжки', HOURS, 'header', None),
            (f"6 грудня", None, 'data', today_slots),
            (f"7 грудня", None, 'data', tomorrow_slots),
        ]
        
        y_pos = 2
        
        for row_label, row_data, row_type, slots_data in rows:
            # Лівий лейбл (назва рядку)
            rect_label = Rectangle((-1, y_pos), 0.95, cell_h, 
                                  linewidth=1, edgecolor=DARK_GRAY, 
                                  facecolor=HEADER_BG if row_type == 'header' else LIGHT_GRAY)
            ax.add_patch(rect_label)
            ax.text(-0.525, y_pos + cell_h/2, row_label, fontsize=8, 
                   ha='center', va='center', fontweight='bold', color=BLACK)
            
            if row_type == 'header':
                # Заголовок з часами
                for i, hour_label in enumerate(HOURS):
                    draw_cell(ax, i, y_pos, cell_w, cell_h, 'yes')
                    ax.text(i + 0.5, y_pos + cell_h/2, hour_label, fontsize=6.5, 
                           ha='center', va='center', color=BLACK)
            else:
                # Данні слотів
                for i, slot in enumerate(SLOTS):
                    state = slots_data.get(slot, 'yes')
                    draw_cell(ax, i, y_pos, cell_w, cell_h, state)
            
            y_pos -= (cell_h + row_gap)
        
        ax.set_xlim(-1.2, 24)
        ax.set_ylim(y_pos - 0.5, 2.8)
        ax.set_aspect('equal')
        
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Заголовок
        title = f"Графік відключень: {queue_name}"
        fig.suptitle(title, fontsize=13, fontweight='bold', y=0.97)
        
        if last_updated:
            fig.text(0.5, 0.92, f"Дата та час останнього оновлення інформації на графіку: {last_updated}", 
                    ha='center', fontsize=8, color='#666666')
        
        # Легенда
        ax_leg = fig.add_axes([0.08, 0.02, 0.84, 0.1])
        ax_leg.set_xlim(0, 10)
        ax_leg.set_ylim(0, 1)
        ax_leg.axis('off')
        
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
        
        plt.tight_layout(rect=[0, 0.12, 1, 0.90])
        
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
        plt.savefig(output_file, facecolor=WHITE, dpi=150, bbox_inches='tight', pad_inches=0.05)
        print(f"[OK] {output_file}")
        plt.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', required=True)
    parser.add_argument('--gpv', default=None)
    parser.add_argument('--out', default=None)
    args = parser.parse_args()
    
    render_schedule(args.json, args.gpv, args.out)
