# Anthropic Claude Sonnet 4.6

## Контракт адаптера

Сверка источников — 22 ноября 2026.

```http
POST https://api.anthropic.com/v1/messages
x-api-key: <key>
anthropic-version: 2023-06-01
Content-Type: application/json

{"model":"claude-sonnet-4-6","system":"…","max_tokens":6000,"messages":[{"role":"user","content":[{"type":"text","text":"…"},{"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":"…"}}]}]}
```

Ответ содержит `stop_reason` и массив `content`; адаптер объединяет `text` из текстовых блоков после `end_turn`. Таймаут HTTP 90 секунд. Для CLI `claude -p` те же блоки обёрнуты в JSONL-событие `{"type":"user","message":{"role":"user","content":[…]}}`. Инструкция идёт через --system-prompt. Принимается последнее событие type=result с subtype=success и результатом в строке result. Локальный таймаут CLI 120 секунд. [Messages](https://platform.claude.com/docs/en/api/messages/create) · [Ограничения изображений](https://platform.claude.com/docs/en/build-with-claude/vision)

## Ограничения и эксплуатация

Активный адаптер операции подготовки сценария использует `claude-sonnet-4-6`, HTTPS POST /v1/messages, версию API 2023-06-01 и серверный ключ Anthropic. Запрос содержит системную инструкцию и сообщения с текстом и JPEG в base64. При stop_reason=end_turn адаптер читает текстовые блоки. Content Mill ограничивает ответ 6000 токенами.

Для прямого Claude API с этой моделью до 600 изображений, до 10 MB после кодирования на изображение и до 8000 × 8000 пикселей. После 20 изображений действует более строгий предел сторон. [Vision](https://platform.claude.com/docs/en/build-with-claude/vision)

Для Messages API предел тела обычного запроса 32 MiB (268435456 бит). Полный обмен с заголовками и отдельный лимит символов не опубликованы. Base64 занимает четыре символа на три байта. Доступ и квоты зависят от организации. Оплата по токенам. Ошибка завершает задание, новый запуск оплачивается отдельно. Срок хранения у провайдера определяется условиями аккаунта.

[Модели](https://platform.claude.com/docs/en/about-claude/models/overview) · [Messages API](https://platform.claude.com/docs/en/api/messages/create) · [Ошибки и размеры](https://platform.claude.com/docs/en/api/errors) · [Изменения](https://platform.claude.com/docs/en/release-notes/overview) · [Адаптер](claude_script.py)

На 20 ноября 2026 модель имеет статус Legacy, принимает текст и изображения, контекст до 1M токенов, выход до 128K токенов. [Спецификация модели](https://platform.claude.com/docs/en/models/sonnet-4-6/overview)

`CONTENT_MILL_SCRIPT_PROVIDER=claude` выбирает Claude Code 2.1.316 в режиме --print с той же моделью. Текст и JPEG передаются через stream-json, авторизация использует серверный ANTHROPIC_API_KEY. [Выбор CLI](../../../../docs/decisions/0015-script-cli-provider.md)
