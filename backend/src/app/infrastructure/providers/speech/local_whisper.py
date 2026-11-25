"""Run multilingual Whisper locally and keep the original audio time base."""

import os
from functools import lru_cache
from io import BytesIO

import av

from app.application.videos.reel_media import Word


@lru_cache(maxsize=1)
def recognizer():
    from faster_whisper import WhisperModel

    return WhisperModel(
        os.getenv("CONTENT_MILL_WHISPER_MODEL", "small"),
        device="cpu",
        compute_type="int8",
        cpu_threads=4,
    )


def transcribe(media: bytes, fmt: str, language: str) -> list[Word]:
    with av.open(
        BytesIO(media),
        format={"video/mp4": "mov", "video/webm": "matroska"}[fmt],
        options={"protocol_whitelist": "pipe"},
    ) as container:
        if not container.streams.audio:
            return []
        audio = container.streams.audio[0]
        start = round(float((audio.start_time or 0) * audio.time_base) * 1000) - round(
            (container.start_time or 0) / 1000
        )
        duration = (container.duration or 0) // 1000
        if not 0 < duration <= 3 * 3600 * 1000:
            raise ValueError("Unexpected recording duration")
    segments, _ = recognizer().transcribe(
        BytesIO(media),
        language=language,
        word_timestamps=True,
        vad_filter=True,
        condition_on_previous_text=False,
    )
    words = []
    previous = 0
    for segment in segments:
        for word in segment.words or ():
            first = max(previous, start + round(word.start * 1000))
            last = min(duration, start + round(word.end * 1000))
            text = word.word.strip()
            if text and first < last:
                words.append(Word(start_ms=first, end_ms=last, text=text))
                previous = last
    return words
