import json
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from app.application.videos.production import VideoProduction
from app.application.videos.reel import ReelPlan, validate_plan
from app.application.videos.reel_media import Word
from app.application.videos.text import CastVideoCopy, DetailedVideoCopy
from app.domain.video import Video
from pydantic import ValidationError


def test_source_recording_to_openmotion_resumes_without_resubmitting_layers():
    recording = str(uuid4())
    video = Video(
        uuid4(),
        uuid4(),
        "Space",
        "generating",
        {
            "speaker_source_id": recording,
            "generated_overlays": True,
            "language": "English",
            "brief": "Space flight",
            "sources": [],
            "duration": 15,
            "reel_format": "reel-story",
            "production": {"stage": "reel_source", "files": {}},
        },
        "",
        "",
        [],
        datetime.now(UTC),
    )
    # Punctuation groups each sentence into a separate caption with a breather.
    words = [
        Word(start_ms=i * 1200, end_ms=i * 1200 + 1000, text=f"Sentence {i}.")
        for i in range(8)
    ]
    media = MagicMock()
    media.transcribe.return_value = words
    media.rough_cut.return_value = b"speaker"
    media.render_motion.side_effect = [b"first alpha", b"second alpha"]
    media.motion_design.return_value = b"poster"
    frames, clips, motion, model, preview = (MagicMock() for _ in range(5))
    preview.render.return_value = b"preview"
    score = json.dumps(
        {
            "layers": [
                {"artwork": "<circle r='30'/>", "keys": [{"t": 0}, {"t": 1, "x": 30}]},
                {"artwork": "<path d='M5 5L25 25'/>", "keys": [{"t": 0}]},
            ]
        }
    )
    model.generate_edit.side_effect = [score, score]
    model.generate.side_effect = [
        json.dumps(
            {
                "candidates": [
                    {"hook": "Space", "passages": [{"first": 0, "last": 7}]}
                ],
                "selected": 0,
            }
        ),
        json.dumps(
            {
                "art_direction": "Blue paper",
                "overlays": [
                    {
                        "first": i,
                        "last": i,
                        "position": "left",
                        "design": "A planet",
                        "motion": "rotate",
                    }
                    for i in (1, 4)
                ],
            }
        ),
    ]
    motion.submit.return_value = {"job": "export"}
    motion.collect.return_value = b"mp4"
    work = MagicMock()
    from app.domain.project import ProjectContext

    work.return_value.__enter__.return_value.repository.context.return_value = (
        ProjectContext(uuid4(), 1, "", [], [], [], "", [], [])
    )
    producer = VideoProduction(
        work,
        None,
        model,
        frames,
        clips,
        None,
        preview,
        reel_media=media,
        motion=motion,
        describe_error=lambda *_: {},
    )
    producer.read = lambda project, version: ("video/mp4", b"original")
    artifacts = {}
    producer.artifact = lambda _, name: artifacts[name]
    for _ in range(30):
        files, _ = producer.step(video)
        artifacts.update((name, body) for name, _, _, body in files)
        video.settings["production"]["files"].update({name: {} for name, *_ in files})
        if video.status == "ready":
            break
    assert video.status == "ready" and artifacts["final.mp4"] == b"mp4"
    assert artifacts["rough-cut.mp4"] == b"speaker"
    assert artifacts["overlay-01.webm"] == b"first alpha"
    frames.submit.assert_not_called()
    clips.submit.assert_not_called()
    assert model.generate_edit.call_count == 2
    assert (
        "overlay-01.motion.json" in artifacts and "overlay-02-design.png" in artifacts
    )
    assert motion.submit.call_args.args[4] == [b"speaker"]
    assert motion.submit.call_args.kwargs["overlays"] == [
        (1200, 2200, "wide-left", b"first alpha"),
        (4800, 5800, "wide-left", b"second alpha"),
    ]
    assert json.loads(artifacts["captions.json"])[1]["text"] == "Sentence 1."
    assert "Sentence 7." in video.script


@pytest.mark.parametrize("ranges", [[(0, 1)], [(1, 2), (2, 3)], [(1, 8)]])
def test_opening_breathers_and_end_of_transcript_are_protected(ranges):
    phrases = [
        SimpleNamespace(start_ms=i * 1000, end_ms=(i + 1) * 1000) for i in range(5)
    ]
    plan = ReelPlan(
        art_direction="Ink",
        overlays=[
            {
                "first": a,
                "last": b,
                "position": "right",
                "design": "Car",
                "motion": "roll",
            }
            for a, b in ranges
        ],
    )
    with pytest.raises(ValueError, match="interval"):
        validate_plan(plan, phrases, False, [])


def test_transparent_animation_preserves_matte_and_foley(tmp_path):
    import shutil

    from app.infrastructure.video.reel_media import ReelMediaEditor
    from app.infrastructure.video.video_edit import ffmpeg, track_info

    if not shutil.which("ffprobe") or not shutil.which("ffmpeg"):
        pytest.skip("requires FFmpeg")
    ffmpeg(
        tmp_path,
        [
            "-f",
            "lavfi",
            "-i",
            "color=c=0x00ff00:s=90x160:d=5:r=24",
            "-f",
            "lavfi",
            "-i",
            "sine=f=400:d=5",
            "-vf",
            "drawbox=x=25:y=50:w=40:h=60:c=blue:t=fill",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "source.mp4",
        ],
    )
    layer = tmp_path / "layer.webm"
    layer.write_bytes(
        ReelMediaEditor().transparent((tmp_path / "source.mp4").read_bytes(), 1000)
    )
    tracks, _ = track_info(layer, "matroska")
    assert "audio" in tracks and tracks["video"]["tags"]["alpha_mode"] == "1"
    pixels = ffmpeg(
        tmp_path,
        [
            "-c:v",
            "libvpx-vp9",
            "-i",
            layer.name,
            "-an",
            "-vf",
            "alphaextract,scale=9:16",
            "-frames:v",
            "1",
            "-pix_fmt",
            "gray",
            "-f",
            "rawvideo",
            "pipe:1",
        ],
    )
    assert pixels[0] < 10 and pixels[8 * 9 + 4] > 240


def test_model_keyframes_render_transparent_motion_with_foley(tmp_path):
    import shutil
    from io import BytesIO

    from app.application.videos.motion_score import MotionScore
    from app.infrastructure.video.vector_motion import (
        artwork,
        motion_design,
        render_layer,
    )
    from app.infrastructure.video.video_edit import ffmpeg, track_info
    from PIL import Image

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("requires FFmpeg")
    score = MotionScore(
        layers=[
            {
                "artwork": '<rect width="80" height="100" fill="red"/>',
                "keys": [{"t": 0}, {"t": 1, "x": 240}],
            },
            {"artwork": '<circle cx="50" cy="160" r="10"/>', "keys": [{"t": 0}]},
        ],
        sounds=[{"kind": "tap", "t": 0.4}],
    )
    poster = Image.open(BytesIO(motion_design(score))).convert("RGBA")
    assert poster.getpixel((250, 50)) == (255, 0, 0, 255)
    path = tmp_path / "overlay.webm"
    path.write_bytes(render_layer(score, 500))
    tracks, _ = track_info(path, "matroska")
    assert "audio" in tracks and tracks["video"]["tags"]["alpha_mode"] == "1"
    pixels = ffmpeg(
        tmp_path,
        [
            "-c:v",
            "libvpx-vp9",
            "-i",
            path.name,
            "-an",
            "-vf",
            "alphaextract,scale=60:36",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "gray",
            "pipe:1",
        ],
    )
    first, last = pixels[:2160], pixels[-2160:]
    assert first[5 * 60 + 3] > 240 and last[5 * 60 + 3] < 10 and last[5 * 60 + 25] > 240
    with pytest.raises(ValueError):
        artwork('<image href="file:///etc/hostname"/>')


def test_old_unsubmitted_illustration_continues_with_gpt():
    from app.application.videos.reel import ReelEdit

    media = MagicMock()
    job = SimpleNamespace(
        reel_media=media, motion=MagicMock(), clips=MagicMock(), frames=MagicMock()
    )
    state = {
        "stage": "overlay_animate",
        "overlay_index": 0,
        "files": {"overlay-01.webm": {}},
    }
    reel = ReelEdit(
        job, SimpleNamespace(settings={"production": state, "language": "English"})
    )
    plan = SimpleNamespace(overlays=[object(), object()])
    assert reel.generate_overlay(plan, []) == ([], 0)
    assert (state["stage"], state["overlay_index"]) == ("reel_motion_score", 1)
    assert not job.frames.mock_calls and not job.clips.mock_calls


@pytest.mark.parametrize("duration", [15, 20, 30, 40, 45, 60])
def test_short_shots_cover_every_supported_runtime(duration):
    from app.application.videos.production import Storyboard
    from app.domain.video import scene_count

    count = scene_count({"duration": duration, "short_shots": True})
    assert 3000 <= duration * 1000 / count <= 4000
    assert count <= Storyboard.model_json_schema()["properties"]["scenes"]["maxItems"]
    assert count > scene_count({"duration": duration})


def test_white_cutaways_use_actual_speech_keep_hook_and_allow_subphrase_cuts():
    from app.application.videos.reel import WhiteCutawayPlan

    phrases = [
        Word(start_ms=i * 2000, end_ms=i * 2000 + 1800, text="Предмет.")
        for i in range(3)
    ]

    def plan(a, b):
        return WhiteCutawayPlan(
            art_direction="ink",
            cutaways=[{"start_ms": a, "end_ms": b, "design": "pen", "motion": "draw"}],
        )

    words = [w.model_dump() for w in phrases]
    cut = plan(2110, 3350).timeline(phrases, words).overlays[0]
    assert cut.window(phrases) == (2110, 3350) and cut.first == cut.last == 1
    for a, b in [(500, 1500), (2200, 3120), (2050, 4200), (5200, 6200)]:
        with pytest.raises(ValueError):
            plan(a, b).timeline(phrases, words)


def test_white_motion_renders_an_opaque_portrait_with_visible_art():
    from io import BytesIO

    from app.application.videos.motion_score import MotionScore
    from app.infrastructure.video.vector_motion import motion_design
    from PIL import Image

    score = MotionScore(
        white_cutaway=True,
        layers=[
            {
                "artwork": '<rect x="50" y="90" width="120" height="100" fill="#123456"/>',
                "keys": [{"t": 0}, {"t": 1, "x": 70}],
            },
            {"artwork": '<circle cx="32" cy="15" r="5"/>', "keys": [{"t": 0}]},
        ],
    )
    image = Image.open(BytesIO(motion_design(score))).convert("RGBA")
    assert image.size == (360, 640) and image.getpixel((0, 0)) == (255, 255, 255, 255)
    assert image.getpixel((135, 130)) == (18, 52, 86, 255)
    for layer in score.layers:
        layer.keys[-1].opacity = 0
    with pytest.raises(ValueError, match="visible until the hard cut"):
        motion_design(score)


def test_short_storyboard_enforces_duration_and_alternating_camera():
    from app.application.videos.production import ShortStoryboard

    shot = {
        "keep_ms": 3500,
        "camera_setup": "frontal medium",
        "composition": "Desk",
        "cast_and_wardrobe": "Presenter",
        "cut": "Straight",
        "image_prompt": "Desk",
        "video_prompt": "Presenter speaks",
        "reference_ids": [],
        "utterances": [],
    }
    other = dict(shot, camera_setup="three-quarter medium")
    assert len(ShortStoryboard(scenes=[shot, other]).scenes) == 2
    for invalid in [shot, dict(other, keep_ms=2999), dict(other, keep_ms=4001)]:
        with pytest.raises(ValueError):
            ShortStoryboard(scenes=[shot, invalid])


def test_legacy_overlay_cannot_bypass_phrase_validation_with_exact_times():
    plan = ReelPlan(
        art_direction="Ink",
        overlays=[
            {
                "first": 5,
                "last": 7,
                "start_ms": 0,
                "end_ms": 1200,
                "position": "left",
                "design": "Poster",
                "motion": "Fold",
            }
        ],
    )
    with pytest.raises(ValueError, match="interval"):
        validate_plan(plan, [], False, [])


def test_short_script_requires_individual_visual_directions_for_every_shot():
    scenes = [{"duration_ms": 3500, "lines": []}] * 2
    note = (
        "From the opening waist-up framing the presenter raises the page to eye level, "
        "tracks the heading with one finger and holds it in view through the outgoing cut."
    )
    script = {"scenes": scenes, "caption": "A page", "edit_plan": [note]}
    with pytest.raises(
        ValidationError, match="Each scene needs its own visual direction"
    ):
        DetailedVideoCopy.model_validate(script)
    assert CastVideoCopy.model_validate(script).edit_plan == [note]
    with pytest.raises(ValidationError, match="at least 150 characters"):
        DetailedVideoCopy.model_validate({**script, "edit_plan": [note, "Zoom in."]})
