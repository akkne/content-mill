import json
from importlib.resources import files

from app.domain.knowledge import ExampleEntry


def example_entries() -> list[ExampleEntry]:
    root = files(__package__)
    formats = {"video": "video/mp4", "audio": "audio/mp4", "image": "image/png"}
    entries = []
    for item in json.loads(root.joinpath("tree.json").read_text(encoding="utf8")):
        kind = item["type"]
        name = item["name"] if item["parent"] else "Пример проекта"
        content, fmt = b"", ""
        if kind == "file":
            kind = "document"
            content = item["content"].encode()
            fmt = "markdown" if name.endswith(".md") else "plain"
        elif kind in formats:
            content = root.joinpath(item["src"]).read_bytes()
            fmt = formats[kind]
        entries.append(
            ExampleEntry(item["id"], item["parent"], name, kind, content, fmt)
        )
    return entries
