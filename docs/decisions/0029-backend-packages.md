# 0029. Организация пакетов FastAPI-монолита

Дата решения — 22 ноября 2026 года.

Раньше проверка пользователя находилась в маршрутах авторизации, а разбор If-Match — в маршрутах проектов. Остальным маршрутам приходилось импортировать эти модули. Внешние адаптеры генерации текста, речи и видео лежали рядом с инструментами монтажа.

FastAPI поддерживает разбиение API на тематические `APIRouter` и повторное использование зависимостей через `Depends`. В Content Mill используем эти возможности в слое HTTP. Для остальных слоёв сохраняем принятую в проекте чистую архитектуру. [Многофайловые приложения FastAPI](https://fastapi.tiangolo.com/tutorial/bigger-applications/) · [Зависимости FastAPI](https://fastapi.tiangolo.com/tutorial/dependencies/)

| Что меняется | Где искать в [backend/src/app](../../backend/src/app/) |
| --- | --- |
| Адрес или поведение HTTP-метода | `presentation/http/routers/<область>.py`. Порядок подключения задан в `presentation/http/router.py`. |
| Схема HTTP-запроса или ответа | `presentation/http/schemas/<область>.py` |
| Общая авторизация, зависимости HTTP и ошибки | `presentation/http/dependencies.py` и `presentation/http/errors.py` |
| Сценарий и контракт доступа к данным | `application/<область>/`. Например, сценарии проектов и контракты их транзакций находятся в `application/projects/`. |
| Сущности и предметные правила | `domain/` |
| SQLAlchemy и транзакции | `infrastructure/database/models.py`, `repositories/` и `transactions/` внутри `infrastructure/database/` |
| Внешняя модель | `infrastructure/providers/text/`, `speech/` или `media/`. Контракт модели лежит рядом с адаптером. |
| Локальная обработка видео и монтаж | `infrastructure/video/` |
| Сборка и запуск приложения | `container.py` собирает зависимости, `lifespan.py` управляет фоновыми задачами и MCP, `main.py` создаёт приложение. |
