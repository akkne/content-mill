# Kling 2.6 через Polza AI

Контракт проверен 22 ноября 2026 года. Адаптер использует серверный Bearer POLZA_API_KEY. Один запрос создаёт один платный заказ.

```http
POST https://polza.ai/api/v1/media
Authorization: Bearer <key>
Content-Type: application/json

{"model":"kling/v2.6","async":true,"input":{"prompt":"…","duration":"10","aspect_ratio":"9:16","sound":"true","images":[{"type":"base64","data":"data:image/png;base64,…"}]}}
```

Модель принимает один стартовый кадр, промпт до 1000 символов и длительность 5 или 10 секунд. При переданном изображении соотношение сторон определяется кадром. Приложение всегда запрашивает 10 секунд. Раскадровщик выделяет до 850 символов под движение, речь и камеру. Бэкенд добавляет точную границу действия из keep_ms и указание удерживать завершение до конца дубля. Максимум входного PNG в приложении — 8 000 000 байт, кодирование base64 занимает 4 × ceil(n/3) символов. [Каталог и схема модели](https://polza.ai/api/v1/models) · [Страница модели и тариф](https://polza.ai/models/kling/v2.6)

Ответ отправки содержит строковый id. Бэкенд записывает polza:<id>, затем выполняет GET /api/v1/media/{id}. Статусы pending и processing означают ожидание. При completed берётся data.url или data[0].url. MP4 скачивается по HTTPS с домена Polza без заголовка авторизации, лимит — 64 МиБ. При failed или cancelled сохраняется диагностика провайдера. Ошибки доступа, баланса и квоты обрабатывает общий адаптер Polza. Повтор опроса использует сохранённый заказ. [Создание](https://polza.ai/docs/api-reference/media/create) · [Статус](https://polza.ai/docs/api-reference/media/status) · [Адаптер](polza_kling_26.py)

При потере ответа на отправку заказа см. [восстановление по истории Polza](../../../../../../docs/decisions/0031-recover-media-order.md).
