# gpv-voe-vinnytsia
Автоматичний парсинг планових відключень Вінниця (e-svitlo).

## Дані:
Парситься блок `planned_list_cab`, ігнорується `current_list_cab`.

## Автооновлення:
GitHub Actions запускається кожні 10 хвилин.

## secrets:
- `ESVITLO_LOGIN`
- `ESVITLO_PASSWORD`
