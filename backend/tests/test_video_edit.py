import asyncio
import base64
import shutil
from array import array
from io import BytesIO

import pytest
from app.application.videos.production import (
    SavedStoryboard,
    Timeline,
    validate_cuts,
)
from app.infrastructure.video.montage_mcp import montage_server
from app.infrastructure.video.video_edit import FFmpegEditor, ffmpeg, track_info
from app.infrastructure.video.video_failures import describe_video_error
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


@pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="requires FFmpeg"
)
@pytest.mark.parametrize(
    ("video_seconds", "audio_seconds", "accepted"),
    [
        ("10.125", "10.21", True),
        ("3.75", "3.75", True),
        ("3.5", "10", False),
        ("10", "3.7495", False),
    ],
)
def test_collect_checks_both_tracks_against_fractional_scene_window(
    tmp_path, video_seconds, audio_seconds, accepted
):
    from types import SimpleNamespace

    from app.application.videos.production import ProductionError, VideoProduction

    ffmpeg(
        tmp_path,
        [
            "-f",
            "lavfi",
            "-i",
            f"color=red:s=32x32:r=24:d={video_seconds}",
            "-f",
            "lavfi",
            "-i",
            f"sine=r=48000:d={audio_seconds}",
            "-c:v",
            "libx264",
            "-c:a",
            "alac",
            "-movie_timescale",
            "48000",
            "take.mp4",
        ],
    )
    clip = (tmp_path / "take.mp4").read_bytes()
    board = SavedStoryboard(
        scenes=[
            {
                "keep_ms": 3750,
                "composition": "opening",
                "cast_and_wardrobe": "presenter",
                "cut": "cut",
                "image_prompt": "portrait",
                "video_prompt": "turn",
                "reference_ids": [],
                "utterances": [],
            }
        ]
    )
    state = {"stage": "collect", "index": 0, "files": {}, "operation": "heygen:paid"}
    video = SimpleNamespace(settings={"duration": 15, "production": state})
    worker = VideoProduction(
        None,
        None,
        object(),
        None,
        SimpleNamespace(collect=lambda _: clip),
        FFmpegEditor(),
        None,
        describe_error=describe_video_error,
    )
    worker.artifact = lambda video, name: board.model_dump_json()
    if accepted:
        files, _ = worker.step(video)
        assert state["stage"] == "edit"
        assert files == [("scene-01.mp4", "video", "video/mp4", clip)]
    else:
        with pytest.raises(ProductionError) as error:
            worker.step(video)
        assert error.value.detail["reason"] == "invalid_clip"


def test_cast_dialogue_is_dubbed_onto_veo_clip():
    from types import SimpleNamespace
    from uuid import uuid4

    from app.application.videos.cast import validate_cast_scene
    from app.application.videos.production import Scene, VideoProduction

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
        describe_error=describe_video_error,
    )
    state = {"stage": "speech", "index": 0, "line": 0, "files": {}}
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
    assert artifacts["scene-01.mp4"] == b"source:Hello|Hi"
    assert "scene-01-visible.wav" not in artifacts
    for stage in ("sync", "collect_sync"):
        state.update(stage=stage, index=0, operation="old-order")
        files, _ = worker.character_audio(video, shot, 2)
        assert files[0][3] == b"source:Hello|Hi"
        assert state["stage"] == "frame" and "operation" not in state

    # Only the on-screen voice reaches HeyGen. The final dub still includes both.
    artifacts["scene-01.png"] = b"portrait"
    orders = []

    def submit_sync(clip, audio):
        orders.append((clip, audio))
        return "heygen-1"

    worker.lipsync = SimpleNamespace(submit=submit_sync, collect=lambda op: b"synced")
    video.settings["heygen_lipsync"] = True
    state.update(stage="mix_speech", index=0)
    for _ in range(4):
        files, _ = worker.character_audio(video, shot, 2)
        for name, _, _, body in files:
            artifacts[name] = body
            state["files"][name] = {}
    assert orders == [(b"portrait", b"Hello")]
    assert artifacts["scene-01.mp4"] == b"synced:Hello|Hi"
    assert state["stage"] == "frame" and "operation" not in state

    for line in shot.utterances:
        line.delivery = "off_screen"
    state.update(stage="mix_speech", index=0)
    worker.character_audio(video, shot, 2)
    assert state["stage"] == "dub" and len(orders) == 1


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


def test_source_prompt_preserves_each_storyboard_window_on_retry_and_edit():
    import json
    from types import SimpleNamespace

    from app.application.videos.production import VideoProduction, source_prompt

    shot = {
        "composition": "00:00–00:07. Opening",
        "cast_and_wardrobe": "cast",
        "cut": "cut",
        "image_prompt": "frame",
        "video_prompt": "old prompt",
        "reference_ids": [],
        "utterances": [],
    }
    old = SavedStoryboard(scenes=[shot, shot | {"composition": "00:07–00:15. Ending"}])
    plan = [{"keep_ms": n, "video_prompt": "Slow pan"} for n in (7000, 8000)]
    model = SimpleNamespace(generate=lambda *args: json.dumps({"scenes": plan}))
    worker = VideoProduction(
        None, None, model, None, None, None, None, describe_error=describe_video_error
    )
    files, _ = worker.upgrade_storyboard(old, 15)
    board = SavedStoryboard.model_validate_json(files[0][3])
    assert "0–7s" in source_prompt(board.scenes[0])
    assert "0–8s" in source_prompt(board.scenes[1])
    cuts = Timeline(
        cuts=[
            {"scene": i, "start_ms": 0, "end_ms": n} for i, n in [(1, 7000), (2, 8000)]
        ]
    )
    validate_cuts(cuts, board, [10000, 10000], 15)
    cuts.cuts[0].start_ms, cuts.cuts[0].end_ms = 1000, 8000
    with pytest.raises(ValueError, match="storyboard window"):
        validate_cuts(cuts, board, [10000, 10000], 15)
    plan[0]["keep_ms"], plan[1]["keep_ms"] = 8000, 7000
    with pytest.raises(ValueError, match="timecodes"):
        worker.upgrade_storyboard(old, 15)


@pytest.mark.skipif(
    not shutil.which("ffmpeg"), reason="requires the production renderer"
)
def test_product_photo_appears_only_during_selected_interval(tmp_path):
    ffmpeg(
        tmp_path,
        [
            "-f",
            "lavfi",
            "-i",
            "color=red:s=90x160:r=24:d=3",
            "-f",
            "lavfi",
            "-i",
            "sine=f=440:d=3",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "base.mp4",
        ],
    )
    photo = BytesIO()
    Image.new("RGB", (180, 90), "lime").save(photo, "PNG")
    plan = Timeline(
        cuts=[{"scene": 1, "start_ms": 0, "end_ms": 3000}],
        photo_cutaway={"start_ms": 1000, "end_ms": 2000},
        subtitles=[{"start_ms": 1000, "end_ms": 2000, "text": "Product"}],
    )
    body = FFmpegEditor().render(
        [(tmp_path / "base.mp4").read_bytes()], plan, 3, product_photo=photo.getvalue()
    )
    (tmp_path / "final.mp4").write_bytes(body)
    for time, expected in [("0.5", 0), ("1.5", 1), ("2.5", 0)]:
        frame = ffmpeg(
            tmp_path,
            [
                "-ss",
                time,
                "-i",
                "final.mp4",
                "-frames:v",
                "1",
                "-f",
                "image2pipe",
                "-c:v",
                "png",
                "pipe:1",
            ],
        )
        img = Image.open(BytesIO(frame)).convert("RGB")
        assert img.getpixel((360, 640))[expected] > 200
        if expected == 1:
            assert max(img.getpixel((100, 100))) < 30
            assert img.crop((100, 930, 620, 1260)).convert("L").getextrema()[1] > 120
    audio = ffmpeg(
        tmp_path,
        [
            "-ss",
            "1.4",
            "-i",
            "final.mp4",
            "-t",
            "0.2",
            "-vn",
            "-ac",
            "1",
            "-f",
            "s16le",
            "pipe:1",
        ],
    )
    assert max(array("h", audio)) > 500


def test_reference_caption_accents_only_existing_words():
    from app.application.videos.production import Subtitle
    from app.domain.video import FACTS_STYLE, STORY_STYLE
    from app.infrastructure.video.reference_captions import reference_captions

    caption = Subtitle(
        start_ms=999, end_ms=2310, text="Всего 12 дней", emphasis="12 дней"
    )
    facts = reference_captions([caption], FACTS_STYLE)
    story = reference_captions([caption], STORY_STYLE)
    assert "0:00:01.00,0:00:02.31" in facts
    assert r"Всего {\1c&H54F2DB&\fnDejaVu Serif\i1}12 дней{\rCaption}" in facts
    assert r"Всего {\1c&H63DFFF&\fnDejaVu Serif\i1}12 дней{\rCaption}" in story
    caption.emphasis = "другое слово"
    assert reference_captions([caption], STORY_STYLE).endswith("Всего 12 дней\n")


@pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="requires FFmpeg"
)
def test_dub_keeps_short_trailing_pause_in_avatar_scene(tmp_path):
    from app.infrastructure.video.video_edit import wav_bytes

    ffmpeg(
        tmp_path,
        [
            "-f",
            "lavfi",
            "-i",
            "color=red:s=90x160:r=25:d=4.28",
            "-an",
            "-c:v",
            "libx264",
            "avatar.mp4",
        ],
    )
    editor = FFmpegEditor()
    clip = (tmp_path / "avatar.mp4").read_bytes()
    for sounding_tail, expected_complete in [(False, True), (True, False)]:
        speech = b"\x01\x00" * 84000
        tail = (b"\x01\x00" if sounding_tail else b"\x00\x00") * 21600
        duration, _ = editor.inspect(editor.dub(clip, wav_bytes(speech + tail)))
        assert (duration >= 4400) is expected_complete


@pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="requires FFmpeg"
)
def test_dub_retains_picture_through_shorter_voiceover(tmp_path):
    from app.infrastructure.video.video_edit import wav_bytes

    ffmpeg(
        tmp_path,
        [
            "-f",
            "lavfi",
            "-i",
            "color=blue:s=160x90:r=30:d=10",
            "-c:v",
            "libx264",
            "source.mp4",
        ],
    )
    editor = FFmpegEditor()
    audio = wav_bytes(bytes(7200 * 48))
    clip = editor.dub((tmp_path / "source.mp4").read_bytes(), audio)
    assert editor.inspect(clip)[0] == 7200


def test_reference_effects_follow_spoken_script_and_keep_the_audio(tmp_path):
    from uuid import uuid4

    from app.application.videos.production import Scene, validate_cards
    from app.application.videos.spoken_script import (
        ScriptScene,
        format_script,
        matches_script,
    )

    ref = uuid4()
    shot = Scene(
        keep_ms=4000,
        composition="mid",
        cast_and_wardrobe="host",
        cut="match",
        video_prompt="host presents",
        image_prompt="host",
        reference_ids=[],
        utterances=[
            {
                "speaker": "Илья",
                "delivery": "on_screen",
                "text": "Визуалы и маркетинг.",
                "start_ms": 0,
                "end_ms": 3500,
            },
        ],
    )
    approved = format_script(
        [ScriptScene(duration_ms=4000, lines=shot.model_dump()["utterances"])],
        "Русский",
    )
    assert matches_script(approved, [shot])
    assert not matches_script(approved.replace("маркетинг", "дизайн"), [shot])
    board = SavedStoryboard(scenes=[shot])
    timeline = Timeline(
        cuts=[{"scene": 1, "start_ms": 0, "end_ms": 4000, "push_in": True}],
        graphics=[
            {
                "kind": "list",
                "beats": [
                    {"at_ms": 150, "label": "Визуалы"},
                    {"at_ms": 950, "label": "маркетинг"},
                ],
                "end_ms": 1850,
            }
        ],
        photo_cards=[
            {"start_ms": 2000, "end_ms": 2950, "cue": "маркетинг", "version_id": ref}
        ],
    )
    validate_cards(timeline, board, 4, {str(ref)})
    with pytest.raises(ValueError):
        validate_cards(timeline, board, 4, set())
    timeline.graphics[0].beats[0].label = "Рост"
    with pytest.raises(ValueError):
        validate_cards(timeline, board, 4, {str(ref)})
    timeline.graphics[0].beats[0].label = "Визуалы"
    if not shutil.which("ffmpeg"):
        pytest.skip("requires FFmpeg")
    ffmpeg(
        tmp_path,
        [
            "-f",
            "lavfi",
            "-i",
            "color=red:s=90x160:r=24:d=4",
            "-f",
            "lavfi",
            "-i",
            "sine=f=440:d=4",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "source.mp4",
        ],
    )
    photo = BytesIO()
    Image.new("RGB", (240, 260), "lime").save(photo, "PNG")
    result = FFmpegEditor().render(
        [(tmp_path / "source.mp4").read_bytes()],
        timeline,
        4,
        card_images={ref: photo.getvalue()},
    )
    (tmp_path / "result.mp4").write_bytes(result)
    tracks, _ = track_info(tmp_path / "result.mp4")
    assert int(tracks["video"]["nb_frames"]) == 96
    assert abs(float(tracks["audio"]["duration"]) - 4) < 0.03

    def pixel(at):
        return tuple(
            ffmpeg(
                tmp_path,
                [
                    "-ss",
                    str(at),
                    "-i",
                    "result.mp4",
                    "-vf",
                    "crop=2:2:360:556,scale=1:1",
                    "-frames:v",
                    "1",
                    "-pix_fmt",
                    "rgb24",
                    "-f",
                    "rawvideo",
                    "pipe:1",
                ],
            )
        )

    assert max(pixel(0.3)) < 80
    assert pixel(2.5)[1] > 170
    assert pixel(3.5)[0] > 170
