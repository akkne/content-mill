from functools import lru_cache
from importlib.resources import files

from app.domain.knowledge import ExampleEntry

# Stage, project document name and packaged Markdown source.
CATALOG = (
    ("Бриф и источники", "Проверка фактов.md", "01-facts.md"),
    ("Сценарий и хуки", "Первый кадр и хук.md", "02-hook.md"),
    ("Сценарий и хуки", "Сценарий и реплики.md", "03-script.md"),
    ("Голос", "Подготовка речи.md", "04-speech.md"),
    ("Аватар", "Образ персонажа и одежда.md", "10-character-look.md"),
    ("Раскадровка", "Персонажи и сцены.md", "05-scenes.md"),
    ("Медиаматериалы", "Подбор кадров.md", "06-assets.md"),
    ("Анимации", "Задание на движение.md", "07-motion.md"),
    ("Монтаж и субтитры", "Монтажный лист.md", "08-edit.md"),
    ("Рендер и проверка", "Проверка рендера.md", "09-review.md"),
)


@lru_cache(maxsize=1)
def starter_prompts() -> tuple[ExampleEntry, ...]:
    root = files(__package__)
    return tuple(
        ExampleEntry(
            filename,
            f"Промпты/{stage}",
            name,
            "document",
            root.joinpath(filename).read_bytes(),
            "markdown",
        )
        for stage, name, filename in CATALOG
    )
