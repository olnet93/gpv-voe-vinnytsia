# gpv-voe-vinnytsia

Проєкт для парсингу планових відключень електроенергії для Вінницької області з сайту [vn.e-svitlo.com.ua](https://vn.e-svitlo.com.ua).

## Що робить

- Авторизується на сайті `vn.e-svitlo.com.ua` з логіном/паролем із GitHub Secrets.
- Парсить 12 URL-адрес (черги 1.1–6.2).
- Витягує тільки `acc_begin` та `accend_plan` з блоку `planned_list_cab`.
- Ігнорує `current_list_cab`.
- Оновлюється кожні 10 хвилин через GitHub Actions.

## Вихідні дані

Результат зберігається у файлі `outages.json`:

