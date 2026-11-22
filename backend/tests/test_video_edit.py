import asyncio
import base64
import shutil
from array import array
from io import BytesIO

import pytest
from app.application.video_production import (
    SavedStoryboard,
    Timeline,
    validate_cuts,
)
from app.infrastructure.montage_mcp import montage_server
from app.infrastructure.video_edit import FFmpegEditor, ffmpeg, track_info
from PIL import Image


def test_spoken_line_survives_frame_rounding_and_legacy_boards_load():
    shot = {
        "composition": "Behind the counter",
        "cast_and_wardrobe": "Anna in a red coat",
        "cut": "Cut on the turn",
        "image_prompt": "Anna at the counter",
        "video_prompt": "Anna turns: Hello.",
        "reference_ids": [],
    }
    line = {
        "speaker": "Anna",
        "text": "Hello.",
        "delivery": "on_screen",
        "start_ms": 35,
        "end_ms": 7400,
    }
    legacy = shot | {"speaker": "Anna", "dialogue": "Hello."}
    board = SavedStoryboard(scenes=[shot | {"utterances": [line]}, legacy])
    timeline = Timeline(
        cuts=[
            {"scene": 1, "start_ms": 32, "end_ms": 7532},
            {"scene": 2, "start_ms": 0, "end_ms": 7500},
        ]
    )
    with pytest.raises(ValueError, match="truncates dialogue"):
        validate_cuts(timeline, board, [8000, 8000], 15)
    timeline.cuts[0].start_ms = 0
    timeline.cuts[0].end_ms = 7500
    validate_cuts(timeline, board, [8000, 8000], 15)


@pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="requires the production renderer",
)
def test_real_montage_keeps_delayed_audio_at_the_cut(tmp_path):
    # Tone starts one second after picture in each input MP4.
    ffmpeg(
        tmp_path,
        [
            "-f",
            "lavfi",
            "-i",
            "color=red:s=90x160:r=30:d=2",
            "-itsoffset",
            "1",
            "-f",
            "lavfi",
            "-i",
            "sine=f=440:d=1",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "scene-01.mp4",
        ],
    )
    clip = (tmp_path / "scene-01.mp4").read_bytes()
    editor = FFmpegEditor()
    length, _ = editor.inspect(clip)
    assert abs(length - 2000) < 40
    timeline = Timeline(
        cuts=[{"scene": scene, "start_ms": 500, "end_ms": 1500} for scene in (1, 2)]
    )
    rendered = tmp_path / "final.mp4"
    rendered.write_bytes(editor.render([clip, clip], timeline, 2))
    tracks, _ = track_info(rendered)
    assert int(tracks["video"]["nb_frames"]) == 48
    assert abs(float(tracks["audio"]["duration"]) - 2) < 0.025
    pcm = ffmpeg(
        tmp_path,
        [
            "-i",
            rendered.name,
            "-vn",
            "-ac",
            "1",
            "-ar",
            "8000",
            "-f",
            "s16le",
            "pipe:1",
        ],
    )
    samples = array("h", pcm)
    for start in (0, 8000):
        assert max(abs(s) for s in samples[start + 800 : start + 2400]) < 50
        assert max(abs(s) for s in samples[start + 4800 : start + 6400]) > 500

    server = montage_server(tmp_path)
    wave = asyncio.run(server.call_tool("listen", {"scene": 1}))[0]
    assert wave.mimeType == "image/png"
    image = Image.open(BytesIO(base64.b64decode(wave.data))).convert("RGB")
    assert image.size == (800, 160)
    assert image.crop((0, 0, 300, 160)).getbbox() is None
    assert image.crop((500, 0, 800, 160)).getbbox() is not None
