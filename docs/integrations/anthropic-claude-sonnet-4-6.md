# Anthropic Claude Sonnet 4.6

Активный адаптер операции подготовки сценария использует `claude-sonnet-4-6`, HTTPS POST /v1/messages, версию API 2023-06-01 и серверный ключ Anthropic. Запрос содержит системную инструкцию и сообщения с текстом и JPEG в base64. При stop_reason=end_turn адаптер читает текстовые блоки. Content Mill ограничивает ответ 6000 токенами.

Для Messages API предел тела обычного запроса 32 MiB (268435456 бит). Полный обмен с заголовками и отдельный лимит символов не опубликованы. Base64 занимает четыре символа на три байта. Доступ и квоты зависят от организации. Оплата по токенам. Ошибка завершает задание, новый запуск оплачивается отдельно. Срок хранения у провайдера определяется условиями аккаунта.

[Модели](https://platform.claude.com/docs/en/about-claude/models/overview) · [Messages API](https://platform.claude.com/docs/en/api/messages/create) · [Ошибки и размеры](https://platform.claude.com/docs/en/api/errors) · [Изменения](https://platform.claude.com/docs/en/release-notes/overview) · [Адаптер](../../backend/src/app/infrastructure/claude_script.py)

На 20 ноября 2026 модель имеет статус Legacy, принимает текст и изображения, контекст до 1M токенов, выход до 128K токенов. [Спецификация модели](https://platform.claude.com/docs/en/models/sonnet-4-6/overview)

`CONTENT_MILL_SCRIPT_PROVIDER=claude` выбирает Claude Code 2.1.316 в режиме --print с той же моделью. Текст и JPEG передаются через stream-json, авторизация использует серверный ANTHROPIC_API_KEY. [Выбор CLI](../decisions/0015-script-cli-provider.md)
