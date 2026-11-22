from uuid import UUID

from app.application.videos.production import ProductionError
from app.infrastructure.providers.media.fal_media import FalMedia, data_uri


class VeoFast:
    queue = "https://queue.fal.run/fal-ai/veo3.1"

    def __init__(self, api: FalMedia):
        self.api = api

    def submit(self, prompt: str, frame: bytes) -> str:
        result = self.api.request(
            "POST",
            self.queue + "/fast/image-to-video",
            {
                "prompt": prompt,
                "image_url": data_uri("image/png", frame),
                "aspect_ratio": "9:16",
                "duration": "8s",
                "resolution": "720p",
                "generate_audio": True,
            },
        )
        return str(UUID(result["request_id"]))

    def collect(self, operation: str) -> bytes | None:
        url = f"{self.queue}/requests/{UUID(operation)}"
        status = self.api.request("GET", url + "/status")["status"]
        if status in ("IN_QUEUE", "IN_PROGRESS"):
            return None
        if status != "COMPLETED":
            raise ProductionError("clip_rejected")
        result = self.api.request("GET", url)
        return self.api.download(result["video"]["url"], 64 * 1024 * 1024)
