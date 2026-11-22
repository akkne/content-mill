from contextlib import contextmanager
from io import BytesIO

import httpx
import pytest
from app.application.video_production import ProductionError
from app.infrastructure.polza_media import PolzaMedia
from app.infrastructure.polza_nano_banana import PolzaNanoBanana21
from app.infrastructure.polza_veo_fast import PolzaVeoFast
from app.infrastructure.video_failures import describe_video_error
from PIL import Image


def test_polza_scene_requests(monkeypatch):
    png = BytesIO()
    Image.new("RGB", (9, 16)).save(png, "PNG")
    calls = []
    replies = iter(
        [
            {"id": "aig_frame"},
            {"status": "processing"},
            {"status": "completed", "data": [{"url": "https://s3.polza.ai/frame"}]},
            {"id": "gen_video"},
            {"status": "failed"},
        ]
    )

    def request(method, url, *, headers, json, timeout):
        assert headers == {"Authorization": "Bearer test"}
        calls.append((method, url, json))
        return httpx.Response(
            200, json=next(replies), request=httpx.Request(method, url)
        )

    @contextmanager
    def download(method, url, *, timeout):
        assert str(url) == "https://s3.polza.ai/frame"
        yield httpx.Response(
            200, content=png.getvalue(), request=httpx.Request(method, url)
        )

    monkeypatch.setattr(httpx, "request", request)
    monkeypatch.setattr(httpx, "stream", download)
    api = PolzaMedia("test")
    frames, clips = PolzaNanoBanana21(api), PolzaVeoFast(api)
    frame = frames.submit("portrait", [b"ref"])
    assert calls[-1][2] == {
        "async": True,
        "model": "google/gemini-nano-banana-2.1",
        "input": {
            "aspect_ratio": "9:16",
            "image_resolution": "1K",
            "output_format": "png",
            "prompt": "portrait",
            "images": [{"type": "base64", "data": "data:image/jpeg;base64,cmVm"}],
        },
    }
    assert frames.collect(frame) is None
    assert frames.collect(frame) == png.getvalue()
    video = clips.submit("dialogue", png.getvalue())
    assert calls[-1][2]["model"] == "google/veo3_fast"
    assert calls[-1][2]["input"]["generationType"] == "FIRST_AND_LAST_FRAMES_2_VIDEO"
    with pytest.raises(ProductionError, match="clip_rejected"):
        clips.collect(video)
    with pytest.raises(ProductionError, match="legacy_operation"):
        clips.collect("old-fal-id")
    assert calls[-1][1] == "https://polza.ai/api/v1/media/gen_video"


@pytest.mark.parametrize("as_list", [True, False])
def test_resume_completed_video_only_reads_saved_order(monkeypatch, as_list):
    api = PolzaMedia("test")

    def status(method, path):
        assert (method, path) == ("GET", "/gen_saved")
        asset = {"url": "https://s3.polza.ai/scene.mp4"}
        return {"status": "completed", "data": [asset] if as_list else asset}

    @contextmanager
    def download(method, url, *, timeout):
        assert method == "GET" and str(url) == "https://s3.polza.ai/scene.mp4"
        yield httpx.Response(200, content=b"clip", request=httpx.Request(method, url))

    monkeypatch.setattr(api, "request", status)
    monkeypatch.setattr(httpx, "stream", download)
    assert PolzaVeoFast(api).collect("polza:gen_saved") == b"clip"


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        [{}],
        {"url": None},
        [{"url": "http://s3.polza.ai/x"}],
        [{"url": "https://other.example/x"}],
    ],
)
def test_unusable_result_does_not_mark_order_rejected(monkeypatch, data):
    api = PolzaMedia("test")
    monkeypatch.setattr(
        api, "request", lambda *_: {"status": "completed", "data": data}
    )
    with pytest.raises(ValueError, match="asset URL"):
        api.collect("polza:gen_saved", 100, "frame_rejected")


def test_terminal_moderation_keeps_retry_code_and_safe_reason(monkeypatch):
    api = PolzaMedia("test")
    monkeypatch.setattr(
        api,
        "request",
        lambda *_: {
            "status": "failed",
            "error": {
                "code": "FORBIDDEN",
                "message": "Контент отклонён системой модерации.",
                "metadata": {
                    "raw": "The input content was flagged for containing a prominent public figure. private input"
                },
            },
        },
    )
    with pytest.raises(ProductionError, match="clip_rejected") as caught:
        PolzaVeoFast(api).collect("polza:gen_saved")
    assert describe_video_error(caught.value, "collect") == {
        "stage": "collect",
        "reason": "public_figure",
        "provider_code": "FORBIDDEN",
    }


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        (400, "invalid_input"),
        (401, "authentication"),
        (402, "balance"),
        (403, "permission"),
        (404, "not_found"),
        (408, "timeout"),
        (409, "conflict"),
        (410, "expired"),
        (413, "too_large"),
        (415, "unsupported_format"),
        (422, "invalid_input"),
        (429, "rate_limit"),
        (500, "provider_down"),
        (502, "provider_down"),
        (503, "provider_down"),
        (504, "timeout"),
        (418, "http_error"),
    ],
)
def test_video_http_diagnostics(status, reason):
    response = httpx.Response(
        status,
        text="private provider diagnostic",
        request=httpx.Request("GET", "https://example.test/"),
    )
    with pytest.raises(httpx.HTTPStatusError) as caught:
        response.raise_for_status()
    assert describe_video_error(caught.value, "submit") == {
        "stage": "submit",
        "reason": reason,
        "http_status": status,
    }


def test_polza_http_forbidden_distinguishes_moderation_from_access(monkeypatch):
    response = httpx.Response(
        403,
        json={
            "error": {
                "code": "FORBIDDEN",
                "message": "Контент отклонён системой модерации.",
            }
        },
        request=httpx.Request("POST", "https://example.test"),
    )
    monkeypatch.setattr(httpx, "request", lambda *args, **kwargs: response)
    with pytest.raises(ProductionError, match="polza_access") as caught:
        PolzaMedia("test").submit("model", {})
    assert describe_video_error(caught.value, "submit") == {
        "stage": "submit",
        "reason": "moderation",
        "provider_code": "FORBIDDEN",
        "http_status": 403,
    }
