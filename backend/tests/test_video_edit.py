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


def test_cast_voice_and_visible_audio_take_separate_routes():
    from types import SimpleNamespace
    from uuid import uuid4

    from app.application.video_cast import validate_cast_scene
    from app.application.video_production import Scene, VideoProduction

    anna, ben, photo = [str(uuid4()) for _ in range(3)]
    people = [
        {
            "character_id": identifier,
            "display_name": name,
            "voice": {"elevenlabs_voice_id": voice, "model_id": "chosen-model"},
            "files": [{"version_id": photo, "role": "face_reference"}],
        }
        for identifier, name, voice in [
            (anna, "Anna", "voice-a"),
            (ben, "Ben", "voice-b"),
        ]
    ]
    shot = Scene(
        composition="close-up",
        cast_and_wardrobe="Anna",
        cut="cut",
        image_prompt="Anna",
        video_prompt="Anna",
        reference_ids=[photo],
        visible_character_ids=[anna],
        utterances=[
            {
                "character_id": anna,
                "speaker": "Anna",
                "delivery": "on_screen",
                "text": "Hello",
                "start_ms": 500,
                "end_ms": 2000,
            },
            {
                "character_id": ben,
                "speaker": "Ben",
                "delivery": "off_screen",
                "text": "Hi",
                "start_ms": 3000,
                "end_ms": 5000,
            },
        ],
    )
    validate_cast_scene(shot, people)
    requests = []

    def submit(voice, text, request):
        requests.append((voice["model_id"], voice["elevenlabs_voice_id"], text))
        return text

    sync_inputs = []

    def sync(video, audio):
        sync_inputs.append((video, audio))
        return "sync-id"

    worker = VideoProduction(
        None,
        None,
        None,
        None,
        None,
        SimpleNamespace(
            prepare_line=lambda audio, duration: audio,
            speech_track=lambda lines, duration: b"|".join(line[2] for line in lines),
            dub=lambda video, audio: video + b":" + audio,
            inspect=lambda clip: (8000, "preview"),
        ),
        None,
        SimpleNamespace(submit_line=submit, collect_line=lambda op: op.encode()),
        SimpleNamespace(submit=sync, collect=lambda op: b"synced"),
    )
    state = {"stage": "speech", "index": 0, "line": 0}
    video = SimpleNamespace(
        settings={"duration": 15, "production": state, "characters": people}
    )
    artifacts = {"scene-01-source.mp4": b"source"}
    worker.artifact = lambda video, name: artifacts[name]
    for _ in range(10):
        files, _ = worker.character_audio(video, shot, 2)
        artifacts.update({name: body for name, _, _, body in files})
        if state["stage"] == "frame":
            break
    assert requests == [
        ("chosen-model", "voice-a", "Hello"),
        ("chosen-model", "voice-b", "Hi"),
    ]
    assert sync_inputs == [(b"source", b"Hello")]
    assert artifacts["scene-01.mp4"] == b"synced:Hello|Hi"


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="requires ffmpeg")
def test_dub_uses_complete_line_at_planned_sample_offset(tmp_path):
    import wave

    ffmpeg(tmp_path, ["-f", "lavfi", "-i", "sine=f=700:d=0.4", "line.mp3"])
    editor = FFmpegEditor()
    line = editor.prepare_line((tmp_path / "line.mp3").read_bytes(), 600)
    track = editor.speech_track([(250, 850, line)], 1000)
    with wave.open(BytesIO(line)) as source, wave.open(BytesIO(track)) as result:
        assert result.getframerate() == 24000 and result.getnframes() == 24000
        assert not any(result.readframes(6000))
        assert result.readframes(source.getnframes()) == source.readframes(
            source.getnframes()
        )
        assert not any(result.readframes(24000))
