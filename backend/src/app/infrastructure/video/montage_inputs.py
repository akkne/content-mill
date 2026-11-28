import json
import os
from collections.abc import Iterable
from pathlib import Path


def stage_montage(
    directory: Path,
    text: str,
    clips: list[bytes],
    materials: Iterable[tuple[str, str, bytes]],
) -> list[str]:
    directory.mkdir()
    for index, clip in enumerate(clips, start=1):
        (directory / f"scene-{index:02}.mp4").write_bytes(clip)
    catalog = {}
    for version, fmt, data in materials:
        (directory / version).write_bytes(data)
        catalog[version] = fmt
    (directory / "catalog.json").write_text(json.dumps(catalog))

    tools = ["inspect_material"] if catalog or clips else []
    if clips:
        tools.extend(["inspect_frame", "listen"])
        try:
            template = json.loads(text).get("motion_template")
        except (ValueError, AttributeError):
            template = None
        if template:
            (directory / "openmotion.json").write_text(
                json.dumps(
                    {
                        "template": template,
                        "url": os.getenv("OPENMOTION_URL", "http://localhost:4173"),
                    }
                )
            )
            tools.append("openmotion_get_template")
    return tools
