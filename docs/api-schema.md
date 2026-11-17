# Проект API: первый этап Content Mill

> Предлагаемый контракт, 17 ноября 2026 года. Реализован только `GET /health`; остальные маршруты ниже не существуют. Первый этап охватывает сессию с access/refresh токенами, контекст проекта клиента, документы и создание контента. Типы генерации и модели будут уточнены позже. [План сервера](backend-foundation.md) и [роадмап фронтенда](frontend-roadmap.md) задают границы.

## Общие правила

- Базовый путь — `/api/v1`; таблицы ниже показывают его полностью. JSON в `snake_case`, ID — UUID, время — UTC ISO 8601.
- Все маршруты, кроме входа и обновления токена, требуют действующий access токен и серверную проверку доступа к проекту. Роль из тела запроса не принимается. Пользователь видит только свои проекты и связанные с ними ресурсы.
- Для изменяемых ресурсов ответ содержит `revision`; изменение отправляет `If-Match`. Устаревшая ревизия даёт `409 revision_conflict`.
- Списки возвращают `{items, next_cursor}`; запрос принимает `limit` и `cursor`. Ошибки: `{error: {code, message, request_id, fields?}}`; ожидаемые статусы — `400`, `401`, `403`, `404`, `409`, `422`, `429`, `503`.
- PostgreSQL хранит пользовательские записи и метаданные; все байты документов и медиа лежат в S3. API никогда не раскрывает постоянный объектный ключ. Временный URL выдаётся после проверки доступа.
- Для генерации `Idempotency-Key` обязателен. Повтор с тем же ключом и телом возвращает прежнюю задачу; другое тело с тем же ключом даёт `409`.

## Сессия и пользователь

| Метод и путь | Вход → результат |
| --- | --- |
| `POST /api/v1/auth/login` | После выбранного способа проверки личности → `{access_token, access_expires_at, refresh_token, refresh_expires_at}`. Конкретные поля запроса определяются с механизмом входа; Google/Microsoft в демо не являются выбранными провайдерами. |
| `POST /api/v1/auth/refresh` | Действующий refresh → новая пара токенов с ротацией и отзывом прежнего refresh. Повторное использование отозванного refresh отзывает семейство сессий. |
| `POST /api/v1/auth/logout` | Отзыв текущей refresh сессии → `204`. |
| `GET /api/v1/me` | `{id, display_name, projects: [{id, name, role}]}`. |

Формат access и способ доставки токенов в браузере уточняются до реализации. Refresh хранится на сервере только как хеш; в логах токены не появляются.

## Проекты и контекст клиента

| Метод и путь | Вход → результат |
| --- | --- |
| `GET /api/v1/projects` / `POST /api/v1/projects` | Список; создание `{name}` → `201 Project` и корень базы знаний. |
| `GET /api/v1/projects/{project_id}` / `PATCH /api/v1/projects/{project_id}` | Сведения и переименование по `If-Match`. |
| `GET /api/v1/projects/{project_id}/context` / `PUT /api/v1/projects/{project_id}/context` | Структурированный контекст: `{description, audiences[], products[], facts[], tone_of_voice, forbidden_terms[], source_version_ids[]}`. `PUT` с `If-Match` создаёт новую ревизию. Точный состав полей уточняется перед реализацией. |

`Project` содержит `id`, `name`, `owner_id`, `revision`, `created_at`. Контекст и принадлежность к проекту находятся в PostgreSQL; ссылки на документ фиксируют конкретную готовую версию. Права первого этапа: владелец управляет проектом, редактор меняет контекст и контент, наблюдатель читает. Состав команды и приглашения будут определены отдельно.

## База знаний и файлы

Все пути в таблице начинаются с `/api/v1/projects/{project_id}`.

| Метод и суффикс | Вход → результат |
| --- | --- |
| `GET /nodes?parent_id={id}` / `POST /nodes` | Содержимое папки; создание `{parent_id?, name, kind: folder/document}` → `201 Node`. |
| `GET /nodes/{node_id}` / `PATCH /nodes/{node_id}` | Метаданные; `{name}` с `If-Match` для переименования. |
| `POST /nodes/{node_id}/move` / `DELETE /nodes/{node_id}` | `{new_parent_id}` с `If-Match`; архивирование узла. Перенос в собственного потомка отклоняется. |
| `GET /nodes/{node_id}/versions` | Готовые версии с автором, MIME-типом, размером и датой. |
| `GET /nodes/{node_id}/content` / `PUT /nodes/{node_id}/content` | Текстовый документ; `PUT {content, format}` с `If-Match` создаёт неизменяемую версию в S3. |
| `POST /files/uploads` | `{parent_id?, node_id?, name, mime_type, size_bytes, sha256}` → `{upload_id, upload_url, expires_at}`. Для нового файла указан `parent_id`, для новой версии — `node_id`. |
| `POST /files/uploads/{upload_id}/complete` | Проверяет загруженный объект → готовые `Node` и `FileVersion`. |
| `GET /nodes/{node_id}/download?version={n}` | Короткоживущий URL для просмотра или скачивания после проверки доступа. |
| `GET /search?q=...` | Поиск по названиям, метаданным и извлечённому тексту проекта → узлы с вычисляемым путём. |

`Node` содержит `id`, `project_id`, `parent_id`, `kind`, `name`, `revision`, `archived_at`. `FileVersion` содержит `id`, `node_id`, `version`, `mime_type`, `size_bytes`, `sha256`, `state`, `created_at`. Документ в S3 остаётся источником содержимого; извлечённый текст в PostgreSQL служит поисковым индексом. Ограничения размера, форматы редактора и допустимые MIME-типы задаются при реализации.

## Создание контента

| Метод и путь | Вход → результат |
| --- | --- |
| `GET /api/v1/projects/{project_id}/contents` / `POST /api/v1/projects/{project_id}/contents` | Список; `{goal, content_type, brief, context_revision, source_version_ids[], options}` → `201 ContentDraft`. Допустимые `content_type` и `options` утверждаются после выбора первого сценария и моделей. |
| `GET /api/v1/projects/{project_id}/contents/{content_id}` / `PATCH /api/v1/projects/{project_id}/contents/{content_id}` | Черновик, использованные источники и результат; изменение задания по `If-Match` до запуска. |
| `POST /api/v1/projects/{project_id}/contents/{content_id}/generations` | `Idempotency-Key` и `{instructions?}` → `202 GenerationRun`. Запись сохраняет снимок версий контекста и источников. |
| `GET /api/v1/projects/{project_id}/contents/{content_id}/generations` / `GET /api/v1/projects/{project_id}/contents/{content_id}/generations/{run_id}` | История и состояние попытки: `queued/running/succeeded/failed`, этап, ошибки, ID документов и медиа результата. |

`ContentDraft` и `GenerationRun` хранятся в PostgreSQL. Полученные документы, исходники и медиа — в S3 с версиями; сервер записывает фактическую модель и её выходы. Конкретные шаги генерации, структура результата, длительность ролика и формат кадра будут закреплены после описания моделей. План прежнего полного видеоконвейера остаётся в [общем роадмапе](implementation-roadmap.md), но не задаёт эндпоинты первого этапа.

## Проверки контракта при реализации

Права на чужой проект и файл, отзыв и повтор refresh токена, конфликт ревизий, повтор `Idempotency-Key`, незавершённая загрузка, подмена S3-объекта, сохранение версий источников при повторной генерации.
