# OpenAI GPT-5.3-Codex

Активный адаптер операции подготовки сценария использует модель `gpt-5.3-codex`, HTTPS POST /v1/responses и серверный API-ключ OpenAI. Запрос содержит инструкции и сообщения с текстом и JPEG в data URL. Из завершённого ответа читаются блоки output_text. Content Mill задаёт max_output_tokens=6000 и store=false.

Лимит всего HTTP-обмена с заголовками в битах и отдельный предел символов не опубликованы. Base64 занимает четыре символа на три байта. Доступ и квоты зависят от API-проекта, тарификация по токенам. При отказе задача завершается с ошибкой. Повторный запуск делает новый оплачиваемый запрос. Условия хранения служебных журналов определяет провайдер.

[Модель и тариф](https://developers.openai.com/api/docs/models/gpt-5.3-codex) · [Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create) · [Изменения API](https://developers.openai.com/api/docs/changelog) · [Адаптер](../../backend/src/app/infrastructure/codex_script.py)

Проверено 20 ноября 2026. OpenAI объявил о завершении обслуживания 1 апреля 2027. До этой даты потребуется подключить преемника отдельным адаптером. [График OpenAI](https://developers.openai.com/api/docs/deprecations)
