"""An editable script format shared by the writer and the storyboard planner."""

import re
from typing import Literal

from pydantic import BaseModel, Field


class ScriptLine(BaseModel):
    speaker: str = Field(min_length=1, max_length=180, pattern=r"^[^\r\n]+$")
    delivery: Literal["on_screen", "off_screen"]
    text: str = Field(min_length=1, max_length=1500, pattern=r"^[^\r\n]+$")


class ScriptScene(BaseModel):
    duration_ms: int = Field(gt=0, le=10000)
    lines: list[ScriptLine] = Field(max_length=20)


def stamp(ms: int) -> str:
    return f"{ms // 60000:02}:{ms // 1000 % 60:02}.{ms % 1000:03}"


def format_script(scenes: list[ScriptScene], language: str) -> str:
    english = language.lower().startswith(("en", "англ"))
    delivery = ("on screen", "off screen") if english else ("в кадре", "за кадром")
    elapsed = 0
    blocks = []
    for scene in scenes:
        block = [f"{stamp(elapsed)}–{stamp(elapsed + scene.duration_ms)}"]
        for line in scene.lines:
            mode = delivery[line.delivery == "off_screen"]
            block.append(f"{line.speaker} ({mode}): {line.text}")
        blocks.append("\n".join(block))
        elapsed += scene.duration_ms
    return "\n\n".join(blocks)


def normalized_line(speaker: str, delivery: str, text: str):
    # Splitting on whitespace allows breathing breaks without changing the words.
    return [(speaker, delivery, word) for word in text.casefold().split()]


def matches_script(script: str, scenes: list) -> bool:
    """Legacy and freely written scripts have no machine-readable scene headers."""
    header = r"\d{2}:\d{2}\.\d{3}–\d{2}:\d{2}\.\d{3}"
    blocks = re.split(r"\n\s*\n", script.strip())
    if not re.fullmatch(header, blocks[0].split("\n")[0]):
        return True
    if len(blocks) != len(scenes):
        return False
    elapsed = 0
    for block, scene in zip(blocks, scenes, strict=True):
        timing, *lines = block.splitlines()
        if timing != f"{stamp(elapsed)}–{stamp(elapsed + scene.keep_ms)}":
            return False
        elapsed += scene.keep_ms
        expected = []
        for line in lines:
            match = re.fullmatch(
                r"(.+) \((в кадре|за кадром|on screen|off screen)\): (.+)", line
            )
            if not match:
                return False
            speaker, mode, text = match.groups()
            delivery = "on_screen" if mode in ("в кадре", "on screen") else "off_screen"
            expected.extend(normalized_line(speaker, delivery, text))
        actual = [
            token
            for line in scene.utterances
            for token in normalized_line(line.speaker, line.delivery, line.text)
        ]
        if actual != expected:
            return False
    return True
