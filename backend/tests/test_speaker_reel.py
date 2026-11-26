import json
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from app.application.videos.production import VideoProduction
from app.application.videos.reel import ReelPlan, validate_plan
from app.application.videos.reel_media import Word
from app.domain.video import Video


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
