from app.domain.project import ProjectContext
from app.domain.video import VideoSource


class MockVideoGenerator:
    def prepare(
        self,
        title: str,
        settings: dict,
        context: ProjectContext,
        sources: list[VideoSource],
    ) -> tuple[str, str, list[str]]:
        product = next(
            (p.description for p in context.products if p.name == settings["product"]),
            "",
        )
        idea = settings["brief"] or product or context.description or title
        script = f"1. Хук — {title}\n2. Основная мысль — {idea}"
        for source in sources:
            script += f"\nМатериал — {source.name} (v{source.version}): {source.excerpt[:200]}"
        script += (
            "\n3. Покажите результат на примере.\n4. Предложите зрителю задать вопрос."
        )
        return (
            script[:6000],
            title,
            [
                f"Выбран формат «{settings['method']}».",
                f"Материалы базы знаний: {len(sources)}.",
                f"Стиль бренда: {context.tone_of_voice or 'не задан'}.",
                f"Подготовлен макет сценария на {settings['duration']} секунд.",
                "Озвучка, сцены и монтаж представлены серверным моком.",
            ],
        )
