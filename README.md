# Content Mill

Content Mill — платформа для подготовки, планирования, публикации и анализа короткого контента. Сейчас в репозитории есть запускаемый каркас FastAPI и Next.js, а также [автономные HTML-демо](frontend-mvp/README.md). Продуктовые возможности описаны в [функциональной спецификации](docs/features-description.md), но ещё не реализованы в новых приложениях.

## Быстрый запуск

Нужны Docker и Docker Compose. Скопируйте `.env.example` в `.env` для настройки портов (можно запускать и без копирования, тогда используются 8000 и 3000):

```bash
cp .env.example .env
docker compose up --build
```

Откройте интерфейс на <http://localhost:3000>, проверку API на <http://localhost:8000/health> или документацию FastAPI на <http://localhost:8000/docs>. Compose запускает оба приложения с автообновлением кода. PostgreSQL, S3 и продуктовые API пока не подключены.

## Запуск без Docker

Для бэкенда нужен Python 3.11+:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e './backend/src[dev]'
python -m uvicorn app.main:app --app-dir backend/src --reload
```

Для фронтенда нужен Node.js 22 LTS и npm:

```bash
cd frontend
cp .env.local.example .env.local
npm ci
npm run dev
```

`BACKEND_URL` задаётся только на сервере Next.js и по умолчанию равен `http://localhost:8000`. В Compose он настроен на имя контейнера `backend`.

## Проверки

```bash
python -m ruff check backend/src backend/tests
python -m pytest -q backend/tests
(cd frontend && npm run lint && npx tsc --noEmit && npm run build)
docker compose config
```

Для команд Python установите зависимости `backend/src[dev]` и активируйте виртуальное окружение. Новые тесты бэкенда размещайте в `backend/tests/`. `docker compose config` проверяет конфигурацию без запущенного Docker Engine; для запуска контейнеров нужен работающий Engine.

## Автономные демо

Откройте [демо mill](frontend-mvp/index.html) в браузере, сохраняя папку `frontend-mvp/` целиком: стили, скрипты и изображения находятся рядом с HTML. База знаний в нём использует дерево папок, редактирование текстовых файлов и просмотр медиа. Прежний [однофайловый MVP](frontend-mvp/legacy.html) доступен отдельно. Оба интерфейса работают на моковых данных отдельно от FastAPI и Next.js. Подробности — в [README демо](frontend-mvp/README.md).

Первый этап разработки ограничен сохранением контекста проекта клиента и созданием контента. План интерфейса — в [роадмапе фронтенда](docs/frontend-roadmap.md), серверные границы — в [плане бэкенда](docs/backend-foundation.md), предлагаемые маршруты — в [схеме API](docs/api-schema.md). В Next.js реализованы стартовая страница, базовая навигация и две темы; в FastAPI — только `/health`. Вход и продуктовые сценарии ещё не подключены.

## Структура

```text
backend/
├── src/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py       # единое FastAPI-приложение
│   ├── Dockerfile
│   └── pyproject.toml
└── tests/
    └── test_health.py

frontend/
├── src/
│   ├── app/              # страницы, layout и общие стили
│   └── lib/              # серверный доступ к API
├── Dockerfile
├── package.json
├── postcss.config.mjs
└── next.config.ts
```

| Путь | Назначение |
| --- | --- |
| `backend/src/app/main.py` | Точка входа единого FastAPI-приложения и проверка `/health`. |
| `backend/src/pyproject.toml`, `backend/src/Dockerfile` | Зависимости Python и контейнер приложения. |
| `backend/tests/` | Тесты бэкенда. |
| `frontend/src/app/` | Маршруты App Router, общий layout и стили Tailwind. |
| `frontend/src/lib/` | Общий код для обращения к API из серверного окружения Next.js. |
| `frontend/package.json`, `frontend/Dockerfile` | Сборка, проверки и контейнер интерфейса. |
| `compose.yaml`, `infra/` | Локальный запуск и место для будущих инфраструктурных конфигураций. |
| `frontend-mvp/` | Автономные HTML-демо на моковых данных. |
| `docs/` | Продуктовая и техническая документация; начните с [карты](docs/README.md). |

Необходимые папки для компонентов и новых функций добавляются вместе с их кодом; бизнес-логика остаётся внутри одного Python-приложения. Перед изменениями прочитайте [AGENTS.md](AGENTS.md).
