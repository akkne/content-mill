# Проект API Content Mill

> **Статус:** проект контракта, 16 ноября 2026 года. Эндпоинты ещё не реализованы. Документ конкретизирует [роадмап](implementation-roadmap.md) и [функциональную спецификацию](features-description.md), не вводя отдельные сервисы: все маршруты принадлежат одному Python-монолиту. Точный способ входа пользователя, фреймворк и провайдеры внешних API выбираются при реализации.

## 1. Общие правила

- Базовый путь: `/api/v1`. Таблицы показывают маршруты без этого префикса; `{p}` означает `{project_id}`. Исключение — публичный короткий адрес `/r/{code}` на отдельном домене переходов. JSON в `snake_case`, даты в UTC ISO 8601, идентификаторы — UUID; человекочитаемый номер ролика вида `CM-000123` хранится отдельно.
- Все маршруты, кроме перехода по трекинговой ссылке, проверенных webhook-входов и OAuth-callback, требуют установленной личности пользователя и доступа к проекту. Callback проверяет одноразовый `state` от начатого пользователем подключения. Способ аутентификации браузера пока не закреплён. OAuth-токены соцсетей никогда не возвращаются клиенту.
- Коллекции принимают `limit` (по умолчанию 30, максимум 100) и `cursor`; ответ: `{ "items": [], "next_cursor": null }`. Фильтры задаются в query, например `status`, `channel`, `from`, `to`.
- Создание дорогих задач и публикации требует заголовка `Idempotency-Key`. Повтор с тем же ключом и телом возвращает тот же результат; ключ с другим телом даёт `409`.
- Изменение версионируемого ресурса требует `If-Match: <revision>`; конфликт версий даёт `409 revision_conflict`. Редактирование создаёт новую версию, а исходники завершённых генераций не перезаписываются.
- Обычное создание: `201` и ресурс. Длительная операция: `202` и `{ "job_id", "status": "queued", "result_url" }`. Удаление связи или архивирование: `204`; физическое удаление медиа выполняется отдельно согласно политике хранения.
- Ошибка: `{ "error": { "code": "validation_error", "message": "...", "fields": { "duration_seconds": "15..35" }, "request_id": "..." } }`. Основные коды: `400`, `401`, `403`, `404`, `409`, `422`, `429`, `502`, `503`.
- Файлы лежат в S3-совместимом хранилище; API возвращает метаданные и короткоживущие подписанные URL после проверки прав. В PostgreSQL находятся дерево, версии, связи, статусы и журналы. Отображаемый путь папки не является S3-ключом.
- Для `POST` ниже указаны ключевые поля тела, а не полная JSON Schema каждого вложенного объекта. Неуказанные поля отклоняются на границе API; ограничения размеров и допустимые MIME-типы фиксируются при реализации загрузки.

### Единые ресурсы

| Ресурс | Основные поля |
| --- | --- |
| `Project` | `id`, `name`, `owner_id`, `created_at`, `revision`. |
| `Node` | `id`, `project_id`, `parent_id`, `name`, `kind: folder/document/asset/video`, `display_path`, `revision`, `archived_at`. Путь вычисляемый; уникальность имени — среди соседних узлов. |
| `FileVersion` | `id`, `node_id`, `version`, `mime_type`, `size_bytes`, `sha256`, `created_by`, `created_at`, `state: uploading/ready/failed`. S3-ключ в публичном ответе отсутствует. |
| `Video` | `id`, `code`, `folder_node_id`, `product_id`, `formula_id?`, `target_duration_seconds`, `aspect_ratio`, `status: draft/generating/in_review/approved/archived`, `selected_variant_id`, `selected_render_id?`, `revision`. Публикации имеют отдельные статусы по каналам. |
| `Formula` | `id`, `title`, `status: draft/approved/archived`, `reference_ids`, `revision`, `created_at`. |
| `StageRun` | `id`, `video_id`, `variant_id`, `stage_key`, `status: queued/running/succeeded/failed/cancelled`, `input_versions`, `output_node_ids`, `provider`, `model`, `prompt_version_ids`, `cost: {amount,currency}`, `started_at`, `finished_at`, `error?`. |
| `Job` | `id`, `kind`, `resource_id`, `status`, `progress_percent`, `step`, `result_url`, `error?`. |
| `Publication` | `id`, `video_id`, `render_id`, `channel_id`, `status: scheduled/processing/published/failed/cancelled`, `platform_media_id?`, `platform_url?`, `scheduled_at?`, `published_at?`. |

### Задачи и прогресс

| Метод и путь | Назначение и результат |
| --- | --- |
| `GET /jobs/{job_id}` | Текущий статус, этап, процент и ошибка. Только участники проекта задачи. |
| `GET /jobs/{job_id}/events` | Поток событий прогресса для интерфейса; при разрыве клиент продолжает через `GET /jobs/{job_id}`. |
| `POST /jobs/{job_id}/cancel` | Запрос отмены, если провайдер/рендер ещё допускает её; результат `202`, уже завершённая задача — `409`. |
| `GET /projects/{project_id}/videos/{video_id}/stage-runs?variant_id=...` | История всех 14 этапов с моделями, входными версиями, артефактами и расходами. |
| `GET /projects/{project_id}/videos/{video_id}/stage-runs/{run_id}` | Подробности попытки, включая ссылки на файлы документов и разрешённый журнал без секретов. |
| `GET /projects/{project_id}/videos/{video_id}/costs` | Фактические расходы по этапам и попыткам, валюта, провайдер и отдельно оценка распределённой стоимости подписок. |

## 2. Проекты, команда и база знаний — этап 0

### 2.1. Проекты и права

| Метод и путь | Вход → результат |
| --- | --- |
| `GET /me` | Личность, список доступных проектов и роль в каждом. |
| `GET /projects` / `POST /projects` | Список; создание по `{name}` возвращает проект и корневые папки `brand/`, `avatars/`, `references/`, `formulas/`, `prompts/`, `videos/`. В `prompts/` создаются `common/` и папки поддерживаемых площадок из роадмапа. |
| `GET /projects/{project_id}` / `PATCH /projects/{project_id}` | Сведения; изменение названия и настроек при `If-Match`. |
| `GET /projects/{project_id}/members` / `POST /projects/{project_id}/members` | Список; приглашение по `{email, role}`. Роли: `owner`, `editor`, `publisher`, `analyst`, `viewer`. |
| `PATCH /projects/{project_id}/members/{member_id}` / `DELETE /projects/{project_id}/members/{member_id}` | Смена роли или отзыв доступа. `owner` управляет составом команды; нельзя удалить последнего владельца. |

`viewer` читает материалы; `analyst` также видит отчёты и заявки по разрешению проекта; `editor` редактирует знания и генерирует контент; `publisher` дополнительно управляет публикациями; `owner` управляет проектом, каналами, бюджетом и ролями. Точная матрица разрешений фиксируется вместе с реализацией авторизации.

### 2.2. Дерево Finder/Notion и файлы

Все пути в этой таблице начинаются с `/api/v1/projects/{project_id}`.

| Метод и суффикс | Вход → результат |
| --- | --- |
| `GET /nodes?parent_id={id}` | Содержимое папки с типом, иконкой, превью, размером, датой и `revision`. Для корня `parent_id` не передаётся. |
| `POST /nodes` | `{parent_id, name, kind: folder/document}` → новый узел. Системные папки защищены от переименования/удаления. |
| `GET /nodes/{node_id}` / `PATCH /nodes/{node_id}` | Свойства; изменение `{name, tags, properties}` с проверкой версии. |
| `POST /nodes/{node_id}/move` | `{new_parent_id, new_name?}` → новый вычисляемый путь; API отклоняет перенос папки в собственного потомка. Ссылки по ID остаются действительны. |
| `DELETE /nodes/{node_id}` / `POST /nodes/{node_id}/restore` | Архивирование и восстановление. Папка с зависимыми записями ролика сохраняет связи; физический S3-объект не удаляется немедленно. |
| `GET /nodes/{node_id}/versions` | История содержимого и редакторов. |
| `GET /nodes/{node_id}/content` / `PUT /nodes/{node_id}/content` | Для текстового документа: `PUT {content, format}` (`markdown` или `blocks`) с `If-Match` создаёт версию в S3 и обновляет индексируемый текст PostgreSQL. |
| `POST /files/uploads` | `{parent_id?, node_id?, name, mime_type, size_bytes, sha256}` → `{upload_id, upload_url, expires_at}`. Нужен ровно один из `parent_id` (новый файл) и `node_id` (новая версия). Загрузка байтов напрямую в S3 по подписанному URL. |
| `POST /files/uploads/{upload_id}/complete` | Проверка объекта, хэша и MIME-типа → готовый `Node` и `FileVersion`; незавершённые загрузки не показываются в дереве. |
| `GET /nodes/{node_id}/download?version={n}` | Короткоживущий URL после проверки доступа, без открытого S3-ключа. |
| `GET /search?q=...&kind=...&folder_id=...` | Поиск по названиям, тегам, содержимому документов и метаданным; результат содержит `node_id` и путь. |

### 2.3. Бренд, товары, аватары и промпты

| Метод и путь | Вход → результат |
| --- | --- |
| `GET /projects/{p}/brand` / `PUT /projects/{p}/brand` | `{description, audience, tone_of_voice, claims, forbidden_terms, languages}`. Факты могут ссылаться на `Node` и конкретную версию источника. |
| `GET /projects/{p}/products` / `POST /projects/{p}/products` | Товары; создание `{name, description, usp, facts[], media_node_ids[]}`. |
| `GET /projects/{p}/products/{product_id}` / `PATCH /projects/{p}/products/{product_id}` / `DELETE /projects/{p}/products/{product_id}` | Просмотр, версия изменений и архивирование; старые ролики хранят использованную ревизию товара. |
| `GET /projects/{p}/avatars` / `POST /projects/{p}/avatars` | Профили аватара. Создание `{name, photo_node_id, consent_node_id?, provider_profile?}`; исходные фото остаются в `avatars/`. |
| `PATCH /projects/{p}/avatars/{avatar_id}` / `DELETE /projects/{p}/avatars/{avatar_id}` | Изменение образа и архивирование; связанные ролики сохраняют снимок использованной версии. |
| `GET /projects/{p}/prompts?channel=...&purpose=...` / `POST /projects/{p}/prompts` | Шаблоны из `prompts/common/` и папок площадок; `{title, channel, purpose, content}` создаёт документ и первую версию. |
| `GET /projects/{p}/prompts/{prompt_id}` / `PUT /projects/{p}/prompts/{prompt_id}` | Просмотр и новая версия шаблона. Генерация сохраняет ID версии и снимок фактического запроса без токенов в `scripts/prompts-used.json`. |

## 3. Референсы и формулы — этап 1

| Метод и путь | Вход → результат |
| --- | --- |
| `GET /projects/{p}/references` / `POST /projects/{p}/references` | Список; создание `{source_url?, video_node_id?, author, source, observed_at, usage_rights}`. Нужен URL или загруженный файл. |
| `GET /projects/{p}/references/{reference_id}` / `PATCH /projects/{p}/references/{reference_id}` / `DELETE /projects/{p}/references/{reference_id}` | Метаданные, связанные файлы, анализы и архивирование. |
| `POST /projects/{p}/references/{reference_id}/analyses` | `{scope, instructions?}`, где `scope` равен `transcript`, `visual` или `full` → `202`. Извлекает доступные кадры, речь, хук, планы, монтаж и тайминги; каждое утверждение связывает с источником. |
| `GET /projects/{p}/references/{reference_id}/analyses` / `GET /projects/{p}/references/{reference_id}/analyses/{analysis_id}` | Версии разборов, статусы, раскадровка, транскрипт, оценки уверенности. |
| `PATCH /projects/{p}/references/{reference_id}/analyses/{analysis_id}` | Редакторские исправления с `If-Match`; AI-версия сохраняется. |
| `GET /projects/{p}/formulas` / `POST /projects/{p}/formulas` | Список; создание `{title, hook_pattern, scene_pattern[], applicability, reference_ids[]}` → формула в `formulas/`. |
| `GET /projects/{p}/formulas/{formula_id}` / `PATCH /projects/{p}/formulas/{formula_id}` / `DELETE /projects/{p}/formulas/{formula_id}` | Просмотр источников и версий, редактирование, архивирование. |
| `POST /projects/{p}/formulas/{formula_id}/approve` | Утверждение редактором конкретной ревизии формулы перед использованием в генерации. |
| `POST /projects/{p}/formulas/from-analysis` | `{reference_id, analysis_id, title}` → черновик формулы; подтверждение редактором отдельно. |
| `POST /projects/{p}/formulas/{formula_id}/video-drafts` | `{product_id, target_duration_seconds, aspect_ratio, target_channel?}` → черновик `Video` со снимком утверждённой версии формулы. |

## 4. Генератор ролика — этап 2

Префикс суффиксов в таблицах этого раздела: `/api/v1/projects/{project_id}/videos/{video_id}`; создание ролика использует коллекцию `/api/v1/projects/{project_id}/videos`. Генерация на этапе возвращает `Job` и затем создаёт `StageRun`, документ с типовым именем в `scripts/`, активы в `assets/` и новую ревизию проекта ролика. В запросе к генерации допустимы `variant_id`, `instructions`, `provider_preference`, `budget_limit`; сервер фиксирует реально выбранную модель и стоимость. Повтор создаёт новую попытку. Изменение входной версии помечает зависимые выходы как требующие пересборки; утверждённая старая версия сохраняется.

### 4.1. Ролик, контекст и хуки — подэтапы 2.1–2.3

| Подэтап; метод и суффикс | Вход → результат |
| --- | --- |
| 2.1 `GET /projects/{p}/videos` / `POST /projects/{p}/videos` | Список; `{product_id, goal, target_channel?, formula_id?, avatar_id?, target_duration_seconds: 15..35, aspect_ratio: "9:16", quality_profile?}` → `201 Video`, папка `videos/CM-.../` и `scripts/01-brief.md`. `aspect_ratio` выбирает пользователь, `9:16` — значение по умолчанию. |
| 2.1 `GET /projects/{p}/videos/{video_id}` / `PATCH /projects/{p}/videos/{video_id}` | Состояние, выбранная версия и ссылки на документы; изменение задания с `If-Match`, пока ролик не опубликован. |
| 2.2 `POST /context/selections` / `GET /context` | `{product_revision, formula_revision?, brand_revision, reference_ids[], media_node_version_ids[], prompt_version_ids[]}` → снимок источников в `02-sources.md`. Нельзя передать чужой проект или неготовый файл. |
| 2.3 `POST /hooks/generations` / `GET /hooks` | `{count: 2..10, instructions?}` → задача/варианты в `03-hooks.md` с критериями оценки; оценки не являются прогнозом просмотров. |
| 2.3 `PUT /hooks/selection` | `{hook_id?, custom_text?}` → выбранный хук и новая ревизия; нужен ровно один из двух вариантов. |

### 4.2. Сценарий, раскадровка, голос — подэтапы 2.4–2.6

| Подэтап; метод и суффикс | Вход → результат |
| --- | --- |
| 2.4 `POST /scripts/generations` | `{hook_revision, language, instructions?}` → задача; текст озвучки, фразы аватара/закадрового голоса и проверка фактов в `04-script.md`. |
| 2.4 `GET /script` / `PUT /script` | Сценарий и новая версия после ручной правки `{text, segments[], factual_claims[]}`. Сервер оценивает длительность по речи, затем подтверждает её по готовому аудио. |
| 2.5 `POST /storyboards/generations` | `{script_revision, reference_ids?}` → задача; сцены с `start_ms`, `end_ms`, `visual_kind`, `source_node_version_id?`, `on_screen_text` в `05-storyboard.md`. |
| 2.5 `GET /storyboard` / `PUT /storyboard` | Просмотр и редактирование массива сцен; интервалы должны покрывать выбранную длительность без недопустимых наложений. |
| 2.6 `POST /voice-takes/generations` | `{script_revision, voice_profile_id, provider_preference?, pronunciation_overrides?}` → задача; полное аудио, стоимость и тайминги слов в `06-voice.md` и `assets/audio/`. |
| 2.6 `GET /voice-takes` / `PUT /voice-takes/selection` | Все дубли; `{take_id}` утверждает один дубль, после чего зависимые аватарные клипы и субтитры проверяются на актуальность. |

### 4.3. Аватар, медиа, анимация — подэтапы 2.7–2.9

| Подэтап; метод и суффикс | Вход → результат |
| --- | --- |
| 2.7 `POST /avatar-clips/generations` | `{avatar_id, voice_take_id, intervals: [{start_ms,end_ms}], provider_preference?, mode}`, где `mode` — `manual_import` или `api` → задача или ожидаемый ручной импорт. Генерируются только нужные фрагменты; результат и провайдер в `07-avatar.md`. |
| 2.7 `POST /avatar-clips/imports` | `{node_version_id, voice_take_id, start_ms, end_ms, provider: "heygen_web"}` → `clip_id` для клипа, вручную созданного по подписке и загруженного через файловый API. Проверяются доступ к файлу и длительность. |
| 2.7 `GET /avatar-clips` / `PUT /avatar-clips/selection` | Все попытки; `{clip_ids[]}` выбирает совместимые с утверждённым голосом клипы. Ручной экспорт HeyGen загружается через файловый API и привязывается к той же попытке. |
| 2.8 `POST /media/generations` | `{scene_ids[], reuse_first: true, max_new_images?, provider_preference?}` → задача; подбор исходников прежде генерации. Новые файлы и их происхождение в `08-media.md`. |
| 2.8 `GET /media` / `PUT /media/selection` | Кандидаты по сценам; `{scenes: [{scene_id, node_version_id}]}` фиксирует выбор и права на исходник. |
| 2.9 `POST /animations/generations` | `{storyboard_revision, style_reference_ids?}` → задача; движения камеры, карточек и титров в `09-animation.md`. |
| 2.9 `GET /animations` / `PUT /animations` | Таймкоды и параметры эффектов; проверяются выбранное соотношение сторон и безопасные зоны. |

### 4.4. Монтаж, рендер, проверка — подэтапы 2.10–2.12

| Подэтап; метод и суффикс | Вход → результат |
| --- | --- |
| 2.10 `POST /edit-projects/generations` | `{variant_id, editor_provider, reference_ids?, instructions?}`, где `editor_provider` — `gpt` или `claude` → задача. Модель получает сценарий, тайминги, ключевые кадры и выбранные активы; создаёт `10-edit.md` и `edit-project.json` с дорожками, склейками, субтитрами, музыкой и эффектами. |
| 2.10 `GET /edit-projects` / `GET /edit-projects/{edit_id}` | Версии монтажных решений, входные ревизии, обоснование и стоимость каждой итерации. |
| 2.10 `PUT /edit-projects/{edit_id}` | Редактор меняет проект при `If-Match`; валидируются длительности, доступные файлы, поддерживаемые операции и безопасные зоны. |
| 2.10 `POST /edit-projects/{edit_id}/previews` | Рендер предварительной версии → задача, короткоживущий превью-файл и кадры для проверки GPT/Claude. Следующая итерация создаёт новый `edit_id`. |
| 2.11 `POST /renders` / `GET /renders` | `{edit_id, output_profile?, create_cover: true}` → задача финального MP4 и обложки; все версии в `assets/video/`, `assets/images/` и `11-render.md`. |
| 2.11 `PUT /renders/selection` | `{render_id, cover_node_version_id?}` → утверждённый `final.mp4` для плеера; старые рендеры доступны. |
| 2.12 `POST /reviews/checks` / `GET /reviews` | `{render_id}` → автоматическая проверка длительности, аудио, титров, визуальных артефактов, фактов и совместимости площадки; отчёт в `12-review.md`. |
| 2.12 `POST /reviews/decisions` | `{render_id, decision, notes?, issue_codes[]}`, где `decision` — `approve` или `reject` → решение редактора. `approve` допускается только после автоматической проверки и создаёт разрешение на публикацию данной ревизии. |

### 4.5. Варианты и подготовка публикаций — подэтапы 2.13–2.14

| Подэтап; метод и суффикс | Вход → результат |
| --- | --- |
| 2.13 `GET /variants` / `POST /variants` | `{from_variant_id, restart_from_stage, instructions?}` → новая ветка с сохранением исходной; запись в `13-variants.md`. `restart_from_stage`: `hooks`, `script`, `storyboard`, `voice`, `avatar`, `media`, `animation`, `edit` или `render`. |
| 2.13 `GET /variants/{variant_id}` | Граф версий, отличия, использованные документы/медиа и фактическая стоимость каждой попытки. |
| 2.14 `POST /publication-packages/generations` | `{render_id, channel_ids[], cta?, tracking_target?}` → задача: варианты подписей, ссылок и параметров площадок в `14-publication.md`. |
| 2.14 `GET /publication-packages` / `PUT /publication-packages/{package_id}` | Проверка и правка `{caption, hashtags[], cover_node_version_id?, channel_options}`; пакет не публикует ролик сам. |

### Пример создания ролика

```http
POST /api/v1/projects/{project_id}/videos
Idempotency-Key: 75f0b7c0-...
Content-Type: application/json

{"product_id":"uuid","goal":"лиды","formula_id":"uuid","target_channel":"instagram","target_duration_seconds":30,"aspect_ratio":"9:16","avatar_id":"uuid"}
```

```json
{"id":"uuid","code":"CM-000123","folder_node_id":"uuid","status":"draft","target_duration_seconds":30,"aspect_ratio":"9:16","selected_variant_id":"uuid","revision":1}
```

`target_duration_seconds` — целевое значение пользователя от 15 до 35; итоговый рендер проверяется по фактической длительности. Выбор другого формата не меняет требования площадки: несовместимость возвращается в проверке до публикации.

### Пример задачи монтажа и проекта

```http
POST /api/v1/projects/{project_id}/videos/{video_id}/edit-projects/generations
Idempotency-Key: 6bf28a0d-...
Content-Type: application/json

{"variant_id":"uuid","editor_provider":"claude","reference_ids":["uuid"],"instructions":"быстрый хук, затем спокойный темп"}
```

```json
{"job_id":"uuid","status":"queued","result_url":"/api/v1/jobs/uuid"}
```

После выполнения задача создаёт `edit_id`, `10-edit.md` и `edit-project.json`. Минимальная структура проекта:

```json
{
  "variant_id": "uuid",
  "duration_ms": 30000,
  "canvas": {"aspect_ratio": "9:16", "width": 1080, "height": 1920, "fps": 30},
  "tracks": [
    {"kind": "video", "clips": [{"node_version_id": "uuid", "start_ms": 0, "end_ms": 2500, "source_in_ms": 0}]},
    {"kind": "voice", "clips": [{"node_version_id": "uuid", "start_ms": 0, "end_ms": 30000, "source_in_ms": 0}]}
  ],
  "captions": [{"start_ms": 120, "end_ms": 540, "text": "Смотрите", "emphasis": true}],
  "transitions": [{"at_ms": 2500, "kind": "crossfade", "duration_ms": 180}]
}
```

Реальная схема проекта дополнит позицию, масштаб, маску, анимацию, громкость и проверку перекрытий. `node_version_id` привязывает монтаж к неизменной версии файла. Исполнитель отклоняет неизвестные операции до рендера.

## 5. Анализ ниши и конкурентов — этап 3

| Метод и путь | Вход → результат |
| --- | --- |
| `POST /projects/{p}/niche-analyses` | `{product_id, geography, keywords[], competitor_handles[], platforms[]}` → задача. Права на доступ к чужим данным и объём сбора проверяются по площадке. |
| `GET /projects/{p}/niche-analyses` / `GET /projects/{p}/niche-analyses/{analysis_id}` | История и отчёт: источники, размер выборки, ограничения, аномалии и формулы. |
| `GET /projects/{p}/niche-analyses/{analysis_id}/steps` | Прогресс десяти ролей: профайлер, разведка, сборщик, чистильщик, скоринг, разметка, визуальный анализ, скептик, формулы, адаптация. Это шаги монолита, не микросервисы. |
| `GET /projects/{p}/niche-analyses/{analysis_id}/competitors` / `POST /projects/{p}/niche-analyses/{analysis_id}/competitors` | Кандидаты с источниками; добавление пользователем `{platform, handle, reason?}`. |
| `PATCH /projects/{p}/niche-analyses/{analysis_id}/competitors/{competitor_id}` | `{decision, reason?}`, где `decision` — `include` или `exclude`; анализ не считает неподтверждённые аккаунты доверенными. |
| `GET /projects/{p}/niche-analyses/{analysis_id}/observations` | Доступные посты и метрики с датой, автором, медианой автора, множителем и ссылкой на исходник. |
| `POST /projects/{p}/niche-analyses/{analysis_id}/formulas` | `{observation_ids[], title}` → черновик формулы для редакторского подтверждения. |

## 6. План и профильная студия — этап 4

| Метод и путь | Вход → результат |
| --- | --- |
| `GET /projects/{p}/plans?week=...` / `POST /projects/{p}/plans` | Недельные планы; `{week_start, posts_per_week: 2..7, goals[], channels[]}` → черновик с балансом рубрик. |
| `POST /projects/{p}/plans/{plan_id}/generations` | Пересобрать идеи и сетку недели → задача; старая версия сохраняется. |
| `POST /projects/{p}/plans/{plan_id}/sprints` | `{products[], channel_ids[], include_carousels, include_stories}` → задача согласованного недельного спринта из роликов, каруселей и цепочки Stories. |
| `GET /projects/{p}/plans/{plan_id}` / `PATCH /projects/{p}/plans/{plan_id}` | Стратегия недели, рубрики, объяснения выбора; изменение при `If-Match`. |
| `POST /projects/{p}/plans/{plan_id}/items` / `PATCH /projects/{p}/plans/{plan_id}/items/{item_id}` / `DELETE /projects/{p}/plans/{plan_id}/items/{item_id}` | Карточки календаря: `{date_time, format, channel_id?, product_id, formula_id?, hook?, video_id?}`. |
| `POST /projects/{p}/plans/{plan_id}/recommendations/{recommendation_id}/apply` | Применение проверенной аналитической рекомендации к черновику плана; создаётся версия с объяснением изменений. |
| `POST /projects/{p}/studio/profile-audits` | `{channel_id, scope?}` → задача и отчёт по доступным данным профиля, без выдуманных метрик. |
| `POST /projects/{p}/studio/repurposes` | `{source_node_version_id?, video_id?, target_format, instructions?}` → задача и новый материал со связью с оригиналом; нужен ровно один исходник. |
| `POST /projects/{p}/studio/carousels` / `POST /projects/{p}/studio/stories` | `{product_id, goal, formula_id?, slide_count?, instructions?}` → задачи; результат — редактируемые слайды/тексты в базе знаний. |
| `GET /projects/{p}/studio/outputs/{output_id}` / `PATCH /projects/{p}/studio/outputs/{output_id}` | Просмотр и исправление карусели, Stories, аудита или переработки. |
| `POST /projects/{p}/studio/interaction-suggestions` | `{channel_id, comment_ids[]}` → черновики ответов в голосе бренда; реальные действия выполняются отдельным разрешённым маршрутом. |
| `GET /projects/{p}/channels/{channel_id}/comments` / `POST /projects/{p}/channels/{channel_id}/comments/{comment_id}/replies` | Работа с комментариями только при подтверждённых правах и поддержке провайдера; иначе `422 capability_unavailable`. |

## 7. Каналы и публикация — этап 5

| Метод и путь | Вход → результат |
| --- | --- |
| `GET /projects/{p}/channels` | Подключённые аккаунты: площадка, имя, состояние, права, срок действия соединения; токены скрыты. |
| `POST /projects/{p}/channels/connections` | `{platform, return_url}` → URL официального OAuth/подключения и `state`. Сервер проверяет владельца проекта. |
| `GET /oauth/{platform}/callback` | Вход от площадки с проверкой `state`; сохраняет токены на сервере и возвращает пользователя в интерфейс. Точный callback зависит от провайдера. |
| `GET /projects/{p}/channels/{channel_id}/capabilities` | Поддержка Reels/Shorts/Stories/каруселей, допустимые формат/длительность, публикация и аналитика для **этого аккаунта**. |
| `POST /projects/{p}/channels/{channel_id}/check` / `DELETE /projects/{p}/channels/{channel_id}` | Диагностика прав/токена → состояние; отключение канала и отзыв доступного токена. |
| `POST /projects/{p}/publications` | `{video_id, render_id, publication_package_id, channel_id, scheduled_at?, visibility, user_confirmed: true}` → `202`. Нужны утверждённый рендер, совместимость формата и явное согласие пользователя. |
| `POST /projects/{p}/publication-batches` | `{video_id, render_id, channel_ids[], package_ids[], scheduled_at?, user_confirmed: true}` → группа отдельных публикаций по каналам. Ошибка одного канала не скрывает состояние других. |
| `GET /projects/{p}/publications` / `GET /projects/{p}/publications/{publication_id}` | Состояние `scheduled/processing/published/failed/cancelled`, ссылка/ID площадки, журнал попыток. |
| `POST /projects/{p}/publications/{publication_id}/retry` / `POST /projects/{p}/publications/{publication_id}/cancel` | Повтор временной ошибки либо отмена ещё не отправленного задания; защита от дублирования публикации. |

Для TikTok публичная публикация включается только после требуемого одобрения приложения и разрешения пользователя. Для каждой площадки проверяются её фактические возможности; универсального обещания автопостинга нет. Вебхуки площадок принимаются отдельными проверенными маршрутами `/webhooks/{platform}`, не как пользовательские JSON-запросы.

## 8. Трекинг, заявки и аналитика — этап 6

| Метод и путь | Вход → результат |
| --- | --- |
| `POST /projects/{p}/tracking-links` / `GET /projects/{p}/tracking-links` | `{video_id, publication_id?, destination_url, campaign?}` → короткий код, URL и UTM. Ссылка выдаётся лишь для проверенного домена назначения проекта. |
| `GET /r/{code}` | Публичный редирект на сохранённый URL и запись перехода; фильтрация ботов и защита от открытого редиректа. Код не раскрывает данные проекта. |
| `POST /projects/{p}/leads` | Ручная заявка или серверная интеграция `{source, external_id?, tracking_code?, contact?, occurred_at}`; повтор `external_id` не создаёт дубль. |
| `POST /webhooks/leads/{provider}` | Вход CRM/формы с проверкой подписи и повторов; связывает заявку с трекинг-кодом, если он есть. |
| `GET /projects/{p}/leads` / `GET /projects/{p}/leads/{lead_id}` / `PATCH /projects/{p}/leads/{lead_id}` | Лид-стрим, источник, атрибуция, статус и примечания команды; доступ по ролям. |
| `GET /projects/{p}/analytics/overview?from=...&to=...` | KPI с периодом, источниками данных и отметкой отсутствующих метрик. |
| `POST /projects/{p}/analytics/sync` | `{channel_ids[], from?, to?}` → задача обновления доступных метрик из подключённых площадок; статус источника сохраняется. |
| `GET /projects/{p}/analytics/funnel?from=...&to=...&channel_id=...` | Просмотры площадки → измеренные переходы → заявки; CTR/CR только при известных знаменателях. |
| `GET /projects/{p}/analytics/timeseries?metric={metric}&interval=day` | Точки для графика с платформой и периодом; `metric` — `views`, `clicks` или `leads`. |
| `GET /projects/{p}/analytics/videos` / `GET /projects/{p}/analytics/formulas` / `GET /projects/{p}/analytics/channels` | Сравнение роликов, формул и площадок по выбранной метрике, с размерами выборки. |
| `GET /projects/{p}/analytics/posting-times?channel_id=...` | Рекомендации времени публикации на основе собственной истории аккаунта, с размером выборки; при недостатке данных — пустой результат. |
| `GET /projects/{p}/analytics/recommendations?from=...&to=...` | Предложения изменить доли формул в следующем плане с указанием числа просмотров, переходов и заявок, доверия и причины. |

## 9. Автопилот, AI-маркетолог и диагностика — этап 7

| Метод и путь | Вход → результат |
| --- | --- |
| `GET /projects/{p}/autopilot` / `PUT /projects/{p}/autopilot` | `{enabled, posts_per_week: 2..7, channel_ids[], budget_limit_monthly, approval_mode, timezone}`; включение требует доступных каналов и явного действия владельца/издателя. |
| `GET /projects/{p}/autopilot/runs` / `POST /projects/{p}/autopilot/runs` | История и ручной запуск подготовки следующей недели; каждый ролик сначала создаётся как черновик. |
| `POST /projects/{p}/autopilot/pause` | Остановка новых генераций/публикаций, без удаления подготовленных материалов. |
| `GET /projects/{p}/conversations` / `POST /projects/{p}/conversations` | Диалоги AI-маркетолога; создание `{title?}`. |
| `GET /projects/{p}/conversations/{conversation_id}/messages` / `POST /projects/{p}/conversations/{conversation_id}/messages` | `{text}` → ответ с периодом, ссылками на используемые отчёты и необязательными предложениями действий. Модель получает только разрешённые функции чтения, не произвольный SQL. |
| `POST /projects/{p}/conversations/{conversation_id}/actions` | `{action: create_video_draft, proposal_id, user_confirmed: true}` → конкретный черновик. Публикация из чата проходит обычный маршрут публикаций. |
| `GET /projects/{p}/integrations/health` | Состояние LLM, TTS, HeyGen, S3, рендера, каналов и последних ошибок без раскрытия секретов. |
| `POST /projects/{p}/integrations/{provider}/check` | Проверка доступности/прав указанного подключения; результат в журнале диагностики. |
| `GET /projects/{p}/audit-log` | Кто изменил документ, выбрал рендер, включил автопилот, подключил канал или отправил публикацию. |

## 10. Сквозные проверки контракта

- Путь `videos/CM-000123/...` — представление дерева из PostgreSQL; API никогда не принимает такой путь как полномочие для чтения чужого S3-объекта.
- При `PATCH` сценария или смене озвучки зависимые тайминги, аватарные клипы, монтаж и рендер помечаются устаревшими. Старые версии остаются в истории; публикация устаревшего рендера блокируется.
- Для AI-задачи хранить шаблон и фактический запрос после удаления токенов и чувствительных данных, входные версии, провайдера, модель, цену, результат и ошибку. Бюджет ограничивает запуск до внешнего вызова.
- Внешние webhook-и проверяются подписью/секретом и `external_id`; повторное событие не дублирует публикацию, метрику или заявку.
- Утверждение редактора привязано к `render_id` и ревизии исходников. Новый рендер требует новой проверки и решения.
- Минимальный набор проверок после реализации: права на чужой проект, конфликт ревизий, повтор `Idempotency-Key`, неготовый S3-файл, отмена задачи, зависимость этапов, несовместимый формат площадки, повтор webhook и атрибуция заявки.
