# Eleven Multilingual v2 через Lumean

## Контракт адаптера

Сверка источников — 22 ноября 2026.

Базовый URL `https://api.lumean.app/api/public/`. Каждый успешный ответ имеет оболочку `{"success":true,"data":{…}}`.

| Метод | Поля запроса | Поля внутри data |
| --- | --- | --- |
| GET voices | provider=elevenlabs, page, per_page=20 и необязательные search/voice_id, language, gender | items[] с voice_id и метаданными, has_more (boolean) |
| POST templates | name, service_key=elevenlabs, config.tts_settings (см. ниже) | id (UUID) |
| POST orders | template_id, input_text, name (UUID попытки), config_override.tts_settings.voice_id | id (UUID) |
| GET orders/{id} | ID заказа | status, files_expired, result.files[] (пути) |
| POST storage/url | path из result.files[0], download=false | url (HTTPS) |

```json
{"mode":"mode_v1","model_id":"eleven_multilingual_v2","voice_id":"<voice_id>","advanced_voice_settings":true,"voice_settings":{"stability":0.5,"similarity_boost":0.75,"use_speaker_boost":true,"speed":1.0}}
```

Финальные статусы с результатом — completed и result_delivered. Для реплики ролика ограничиваем скачивание 16 МиБ. Lumean проверяет максимум 1500 фрагментов на заказ, 500 пауз, 10 секунд на паузу и 3600 секунд суммарной тишины. При превышении возвращает 422. Ограничения частоты и числа одновременных заказов зависят от подписки. [Текст и разбиение](https://lumean.app/en/developers/docs/guide/text) · [Квоты](https://lumean.app/en/developers/docs/guide/limits)

## Ограничения и эксплуатация

Активный адаптер для каталога ElevenLabs и модели `eleven_multilingual_v2`. Контракт проверен по документации 20 ноября 2026 года. Используем серверный X-API-KEY с правами voices.read, templates.write, orders.write, orders.read и orders.download. Доступ зависит от рабочего аккаунта.

GET /voices принимает provider=elevenlabs, поиск, язык, пол и страницы с 1. Запрашиваем 20 записей, продолжение определяем по has_more. Каталог возвращает метаданные и необязательное HTTPS-превью. [Каталог](https://lumean.app/developers/docs/api/get-voices)

При первой озвучке карточки создаём шаблон POST /templates. POST /orders принимает template_id, текст и переопределение голоса для конкретного заказа. Отдельный максимум символов input_text для шаблонного заказа в справочнике Lumean не указан. Приложение принимает до 4 000 символов текста за заказ. Входных файлов и системного промпта нет. Общий предел HTTP-запроса и ответа в битах не опубликован. Фактические квоты, доступность и стоимость зависят от аккаунта и текста. [Шаблоны](https://lumean.app/developers/docs/guide/templates) · [Быстрый старт](https://lumean.app/developers/docs/start)

Готовность проверяется через GET /orders/{id}. Временную HTTPS-ссылку на итоговый трек выдаёт POST /storage/url. После истечения ссылки можно запросить новую, пока файл существует у провайдера (обычно семь дней). Длительность и объём трека зависят от текста. Контент проходит проверки провайдера. [Хранение](https://lumean.app/developers/docs/guide/files)

Повтор POST /orders может списать средства повторно. Перед отправкой резервируем локальный UUID. При потере ответа передаём этот же UUID как имя заказа для сверки в кабинете Lumean. Платный запрос автоматически не повторяется. Отмену в интерфейсе не предоставляем. Перед рабочим запуском проверьте доступ к каталогу и одну короткую озвучку со своего аккаунта. [Повторы](https://lumean.app/developers/docs/guide/retries) · [Адаптер](lumean.py)

При сборке ролика карточка показывает причину ошибки заказа и отдельно сохраняет HTTP-статус при ошибке запроса. [Диагностика генерации](../../../../docs/decisions/0024-video-failures.md)
