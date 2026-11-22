# HeyGen Lipsync Precision

Статус — отложено. Адаптер отключён от текущей сборки роликов.

## Контракт адаптера

Сверка источников — 22 ноября 2026.

| Метод и путь на api.heygen.com | Вход адаптера | Используемые поля ответа |
| --- | --- | --- |
| POST /v3/assets (для каждого файла) | multipart `file`, имя и MIME | `data.asset_id: string` |
| POST /v3/lipsyncs | JSON ниже | `data.lipsync_id: string` |
| GET /v3/lipsyncs/{lipsync_id} | ID из предыдущего шага | `data.status: string`, при completed — `data.video_url: string` |

```json
{"mode":"precision","video":{"type":"asset_id","asset_id":"<video>"},"audio":{"type":"asset_id","asset_id":"<audio>"}}
```

Ожидание при pending/running. Таймаут API 120 секунд. Документация допускает заголовок Idempotency-Key на 1–255 символов с окном 24 часа. Адаптер его не задаёт. При 429 учитывать Retry-After. [Создание и ошибки](https://developers.heygen.com/reference/create-lipsync)

## Ограничения и эксплуатация

Серверный ключ HEYGEN_API_KEY авторизует запросы заголовком X-Api-Key. Операция нужна для сцен с выбранным голосом и видимым говорящим. Бэкенд загружает MP4 и WAV по отдельности multipart-запросами POST /v3/assets. Ограничение HeyGen составляет 50 MB на загрузку этих типов. POST /v3/lipsyncs принимает ссылки по asset_id и режим precision. Промпт и текст в эту операцию не передаются. Состояние задания сохраняется по lipsync_id. GET /v3/lipsyncs/{id} возвращает статус и подписанный URL результата. Общий предел HTTP-запроса и ответа в битах не опубликован. Адаптер ограничивает скачивание 64 МиБ и проверяет длительность в составе производственного процесса.

Каждый новый заказ расходует квоту аккаунта. Перед повторной отправкой после обрыва необходимо сверить списание у провайдера. Фактическое качество совпадения губ проверяется на первом рабочем дубле. При недоступности синхронизации сборка останавливается.

[Создание](https://developers.heygen.com/reference/create-lipsync) · [Проверка результата](https://developers.heygen.com/reference/get-lipsync) · [Загрузка файлов](https://developers.heygen.com/reference/upload-asset) · [Адаптер](heygen_lipsync.py)

При сборке ролика карточка показывает причину ошибки заказа и отдельно сохраняет HTTP-статус при ошибке запроса. [Диагностика генерации](../../../../docs/decisions/0024-video-failures.md)
