#!/usr/bin/env python3
"""
Schedule PNG Renderer - генерує PNG графіки відключень для кожної черги
Читає JSON файли і створює PNG картинки з дизайном, що відповідає HTML шаблону

Usage:
    python render_png.py --json data/Vinnytsiaoblenerho.json --out images/
    python render_png.py --json data/kyiv.json --gpv GPV1.2 --out images/gpv-1-2.png
    python render_png.py --json data/odesa.json --day today --out images/
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta
import sys

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import Rectangle, Polygon
    import numpy as np
except ImportError:
    print("ERROR: matplotlib not installed. Install with: pip install matplotlib")
    sys.exit(1)

# Кольори
ORANGE = '#ff8c00'
WHITE = '#ffffff'
BLACK = '#000000'
BORDER_COLOR = '#cccccc'

SLOT_LABELS = [str(i) for i in range(1, 25)]
HOUR_LABELS = [
    '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
    '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
    '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
    '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'
]

def load_json(json_path):
    """Завантажити JSON файл"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Cannot load JSON: {e}")
        sys.exit(1)

def get_day_timestamp(data, day_arg):
    """Отримати Unix timestamp для дня ('today' або 'tomorrow')"""
    today_ts = data.get('fact', {}).get('today')
    
    if today_ts is None:
        print("ERROR: 'today' timestamp not found in JSON")
        sys.exit(1)
    
    if day_arg == 'tomorrow':
        return str(int(today_ts) + 86400)
    else:
        return str(today_ts)

def draw_cell(ax, x, y, width, height, state):
    """Малювати клітинку в залежності від стану"""
    
    # Білий фон для всіх клітинок
    rect = Rectangle((x, y), width, height, 
                    linewidth=1, edgecolor=BORDER_COLOR, 
                    facecolor=WHITE)
    ax.add_patch(rect)
    
    if state == 'no':
        # Повністю залита оранжевим
        rect_fill = Rectangle((x, y), width, height, 
                             linewidth=0, 
                             facecolor=ORANGE)
        ax.add_patch(rect_fill)
    
    elif state == 'first':
        # Ліва половина залита оранжевим (перші 30 хв)
        poly = Polygon([
            (x, y),                    # нижній лівий
            (x + width/2, y),          # нижній середина
            (x + width/2, y + height), # верхній середина
            (x, y + height)            # верхній лівий
        ], facecolor=ORANGE, edgecolor='none')
        ax.add_patch(poly)
    
    elif state == 'second':
        # Права половина залита оранжевим (другі 30 хв)
        poly = Polygon([
            (x + width/2, y),          # нижній середина
            (x + width, y),            # нижній правий
            (x + width, y + height),   # верхній правий
            (x + width/2, y + height)  # верхній середина
        ], facecolor=ORANGE, edgecolor='none')
        ax.add_patch(poly)
    
    # Бордюр для всіх
    rect_border = Rectangle((x, y), width, height, 
                           linewidth=1, edgecolor=BORDER_COLOR, 
                           facecolor='none')
    ax.add_patch(rect_border)

def render_schedule(json_path, gpv_key=None, day_arg=None, out_path=None):
    """Рендерити розклад для черги"""
    
    data = load_json(json_path)
    fact_data = data.get('fact', {}).get('data', {})
    sch_names = data.get('preset', {}).get('sch_names', {})
    last_updated = data.get('fact', {}).get('update', '')
    
    if not fact_data:
        print("ERROR: No fact data found in JSON")
        sys.exit(1)
    
    # Визначити день
    day_ts = get_day_timestamp(data, day_arg)
    
    if day_ts not in fact_data:
        print(f"ERROR: No data for day {day_ts}")
        sys.exit(1)
    
    day_data = fact_data[day_ts]
    
    # Якщо gpv_key не вказаний, обробити всі черги
    if gpv_key:
        gpv_keys = [gpv_key]
    else:
        gpv_keys = sorted([k for k in day_data.keys() if k.startswith('GPV')])
    
    for gkey in gpv_keys:
        if gkey not in day_data:
            print(f"WARNING: {gkey} not found in data, skipping")
            continue
        
        slots = day_data[gkey]
        queue_name = sch_names.get(gkey, gkey)
        
        # Створити фігуру
        fig = plt.figure(figsize=(16, 8), dpi=100)
        fig.patch.set_facecolor(WHITE)
        
        # Головна сітка для таблиці
        ax_table = plt.subplot(2, 1, 1)
        ax_table.set_facecolor(WHITE)
        
        cell_width = 1
        cell_height = 1
        
        # Малювати клітини
        for i, slot_num in enumerate(SLOT_LABELS):
            state = slots.get(slot_num, 'yes')
            draw_cell(ax_table, i, 0, cell_width, cell_height, state)
            
            # Текст номера слота
            ax_table.text(i + 0.5, 0.5, slot_num, 
                         ha='center', va='center', fontsize=10,
                         color=BLACK, fontweight='bold')
        
        # Налаштування осей таблиці
        ax_table.set_xlim(-0.5, 24)
        ax_table.set_ylim(-0.3, 1.3)
        ax_table.set_aspect('equal')
        
        # Верхня вісь - години
        ax_table.set_xticks(np.arange(24) + 0.5)
        ax_table.set_xticklabels(HOUR_LABELS, fontsize=9, color=BLACK)
        ax_table.tick_params(axis='x', top=True, labeltop=True, bottom=False, labelbottom=False)
        
        # Видалити ліву вісь
        ax_table.set_yticks([])
        ax_table.spines['left'].set_visible(False)
        ax_table.spines['right'].set_visible(False)
        ax_table.spines['bottom'].set_visible(False)
        ax_table.spines['top'].set_visible(False)
        
        # Заголовок
        title = f"Графік відключень: {queue_name}"
        if day_arg == 'tomorrow':
            title += " (завтра)"
        else:
            title += " (сьогодні)"
        
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
        
        if last_updated:
            fig.text(0.5, 0.93, f"Оновлено: {last_updated}", 
                    ha='center', fontsize=10, style='italic')
        
        # Легенда в другому підграфіку
        ax_legend = plt.subplot(2, 1, 2)
        ax_legend.set_xlim(0, 10)
        ax_legend.set_ylim(0, 2)
        ax_legend.axis('off')
        
        # Елементи легенди
        legend_items = [
            (0.5, 1.2, 'yes', 'Світло є'),
            (3, 1.2, 'no', 'Світла нема'),
            (5.5, 1.2, 'first', 'Світла нема перші 30 хв.'),
            (8.5, 0.3, 'second', 'Світла нема другі 30 хв.'),
        ]
        
        legend_cell_size = 0.4
        
        for x, y, state, label in legend_items:
            # Малювати приклад клітинки
            draw_cell(ax_legend, x, y, legend_cell_size, legend_cell_size, state)
            
            # Текст легенди
            ax_legend.text(x + legend_cell_size + 0.2, y + legend_cell_size/2, label,
                          ha='left', va='center', fontsize=10, color=BLACK)
        
        plt.tight_layout(rect=[0, 0, 1, 0.92])
        
        # Визначити вихідний файл
        if out_path:
            out_p = Path(out_path)
            if out_p.suffix == '.png':
                # Конкретний файл вказаний
                output_file = out_p
            else:
                # Директорія вказана
                out_p.mkdir(parents=True, exist_ok=True)
                day_suffix = '_tomorrow' if day_arg == 'tomorrow' else '_today'
                output_file = out_p / f"{gkey}{day_suffix}.png"
        else:
            # За замовчуванням
            day_suffix = '_tomorrow' if day_arg == 'tomorrow' else '_today'
            output_file = Path(f"{gkey}{day_suffix}.png")
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        plt.savefig(output_file, facecolor=WHITE, edgecolor='none', dpi=150, bbox_inches='tight')
        print(f"[OK] Saved: {output_file}")
        plt.close()

def main():
    parser = argparse.ArgumentParser(
        description='Schedule PNG Renderer - генерує графіки відключень',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/render_png.py --json data/Vinnytsiaoblenerho.json --out images/
  python scripts/render_png.py --json data/kyiv.json --gpv GPV1.2 --out images/gpv-1-2.png
  python scripts/render_png.py --json data/odesa.json --day tomorrow --out images/
        """
    )
    
    parser.add_argument('--json', required=True, help='Шлях до JSON файлу з даними')
    parser.add_argument('--gpv', default=None, help='Конкретна черга (наприклад GPV1.2). Якщо не вказано, обробити всі')
    parser.add_argument('--day', default='today', choices=['today', 'tomorrow'], help='День для рендерингу')
    parser.add_argument('--out', default=None, help='Вихідний файл або директорія')
    
    args = parser.parse_args()
    
    render_schedule(
        json_path=args.json,
        gpv_key=args.gpv,
        day_arg=args.day,
        out_path=args.out
    )

if __name__ == '__main__':
    main()
