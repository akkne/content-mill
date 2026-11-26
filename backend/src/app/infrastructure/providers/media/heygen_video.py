import base64

from app.application.videos.production import ProductionError
from app.infrastructure.providers.media.heygen_api import HeyGenAPI


class HeyGenVideo(HeyGenAPI):
    model = "heygen-video-1"

    def submit(self, prompt: str, frame: bytes, request_id: str) -> str:
        payload = {
            "model": self.model,
            "mode": "image_to_video",
            "image": {
                "type": "base64",
                "media_type": "image/png",
                "data": base64.b64encode(frame).decode("ascii"),
            },
            "prompt": prompt,
            "duration": 10,
            "resolution": "768p",
        }
        order = self.create_video(
            "models/videos", payload, headers={"Idempotency-Key": request_id}
        )
        return "heygen:" + order

    def collect(self, operation: str) -> bytes | None:
        prefix, _, order = operation.partition(":")
        if prefix != "heygen" or not order:
            raise ProductionError("legacy_operation")
        return self.collect_video(order, "clip_rejected")
