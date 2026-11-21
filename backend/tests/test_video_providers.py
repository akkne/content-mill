from io import BytesIO
from uuid import uuid4

import pytest
from app.application.video_production import ProductionError
from app.infrastructure.nano_banana import NanoBanana21
from app.infrastructure.veo_fast import VeoFast
from PIL import Image


def test_portrait_image_and_native_audio_queue(monkeypatch):
    frame = BytesIO()
    Image.new("RGB", (9, 16)).save(frame, "PNG")
    order = str(uuid4())
    calls = []

    class Provider:
        def request(self, method, url, payload=None):
            calls.append((method, url, payload))
            if url.startswith("https://fal.run/"):
                return {"images": [{"url": "https://fal.media/start.png"}]}
            if method == "POST":
                return {"request_id": order}
            if url.endswith("/status"):
                return {"status": "IN_PROGRESS" if len(calls) == 4 else "COMPLETED"}
            return {"video": {"url": "https://fal.media/shot.mp4"}}

        def download(self, url, limit):
            return frame.getvalue() if url.endswith(".png") else b"video"

    api = Provider()
    frames = NanoBanana21(api)
    assert frames.generate("portrait", []) == frame.getvalue()
    assert calls[-1][1].endswith("google/nano-banana-2.1")
    frames.generate("portrait in store", [b"reference"])
    assert calls[-1][1].endswith("/edit")
    assert calls[-1][2]["image_urls"][0].startswith("data:image/jpeg;base64,")
    clips = VeoFast(api)
    assert clips.submit("line", frame.getvalue()) == order
    assert calls[-1][2]["generate_audio"] and calls[-1][2]["duration"] == "8s"
    assert clips.collect(order) is None
    assert clips.collect(order) == b"video"
    assert calls[-1][:2] == ("GET", f"{VeoFast.queue}/requests/{order}")
    monkeypatch.setattr(api, "request", lambda *args: {"status": "FAILED"})
    with pytest.raises(ProductionError, match="clip_rejected"):
        clips.collect(order)
