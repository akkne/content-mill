import base64
from collections.abc import Callable
from uuid import UUID

GuideReader = Callable[[UUID, str], bytes | None]


def attach_style_guide(
    reader: GuideReader | None,
    project: UUID,
    style: str,
    payload: dict,
    previews: list[str],
):
    if reader and (sheet := reader(project, style)):
        previews.append(base64.b64encode(sheet).decode())
        payload["style_reference"] = {
            "image": len(previews),
            "reading_order": "Chronological, left to right, top row first.",
            "use": "Study framing changes, presenter returns, editorial image placement and typography. Match their function to actual words in this script. Never copy the reference people, claims or subject into the story.",
        }
