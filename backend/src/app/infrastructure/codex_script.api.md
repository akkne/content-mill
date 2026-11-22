# OpenAI GPT-5.3-Codex

## Контракт адаптера

Сверка источников — 22 ноября 2026.

```http
POST https://api.openai.com/v1/responses
Authorization: Bearer <key>
Content-Type: application/json

{"model":"gpt-5.3-codex","store":false,"instructions":"…","input":[{"role":"user","content":[{"type":"input_text","text":"…"},{"type":"input_image","image_url":"data:image/jpeg;base64,…"}]}],"max_output_tokens":6000}
```

Ответ — объект со status и массивом output. Из completed берём output[].type=message, исключаем phase=commentary, объединяем content[].text блоков output_text. Таймаут HTTP 90 секунд. Вариант CLI получает те же инструкции через developer_instructions, текст через stdin и каждое JPEG через --image. Читает UTF-8 из --output-last-message.

Контекст 400 000 токенов, выход модели до 128 000. Для HTTP-запроса с изображениями OpenAI указывает до 512 MB полезной нагрузки и 1500 изображений, в пределах контекста. [Паспорт модели](https://developers.openai.com/api/docs/models/gpt-5.3-codex) · [Визуальный ввод](https://developers.openai.com/api/docs/guides/images-vision)

## Ограничения и эксплуатация

Активный адаптер операции подготовки сценария использует модель `gpt-5.3-codex`, HTTPS POST /v1/responses и серверный API-ключ OpenAI. Запрос содержит инструкции и сообщения с текстом и JPEG в data URL. Из завершённого ответа читаются блоки output_text. Content Mill задаёт max_output_tokens=6000 и store=false.

Лимит всего HTTP-обмена с заголовками в битах и отдельный предел символов не опубликованы. Base64 занимает четыре символа на три байта. Доступ и квоты зависят от API-проекта, тарификация по токенам. При отказе задача завершается с ошибкой. Повторный запуск делает новый оплачиваемый запрос. Условия хранения служебных журналов определяет провайдер.

[Модель и тариф](https://developers.openai.com/api/docs/models/gpt-5.3-codex) · [Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create) · [Изменения API](https://developers.openai.com/api/docs/changelog) · [Адаптер](codex_script.py)

Проверено 20 ноября 2026. OpenAI объявил о завершении обслуживания 1 апреля 2027. До этой даты потребуется подключить преемника отдельным адаптером. [График OpenAI](https://developers.openai.com/api/docs/deprecations)

До перехода на [Astra](../../../../docs/integrations/openai-gpt-6.2-astra.md) значение `CONTENT_MILL_SCRIPT_PROVIDER=codex` выбирало `codex exec` версии 0.170.0 с той же моделью. Сервер передаёт свой ключ как CODEX_API_KEY и JPEG через --image. [Выбор CLI](../../../../docs/decisions/0015-script-cli-provider.md)
