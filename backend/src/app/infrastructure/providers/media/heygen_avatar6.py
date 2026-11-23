from urllib.parse import quote

import httpx

from app.application.videos.production import ProductionError
from app.infrastructure.providers.media.heygen_lipsync import HeyGenLipSync
from app.infrastructure.providers.media.media_download import download_result


class HeyGenAvatar6(HeyGenLipSync):
    model = "heygen-avatar-6-turbo"

    def submit(self, image: bytes, audio: bytes) -> str:
        def asset(name, data, mime):
            if len(data) > 50_000_000:
                raise ProductionError("lipsync_input")
            uploaded = self.request(
                "POST", "assets", files={"file": (name, data, mime)}
            )
            return {"type": "asset_id", "asset_id": uploaded["asset_id"]}

        payload = {
            "model": self.model,
            "reference_images": [asset("presenter.png", image, "image/png")],
            "audio": asset("speech.wav", audio, "audio/wav"),
            "resolution": "1080p",
        }
        try:
            order = self.request("POST", "models/avatars", json=payload)["video_id"]
            if not isinstance(order, str) or not order:
                raise ValueError("Missing video ID")
            return order
        except httpx.HTTPStatusError as error:
            if error.response.status_code >= 500:
                raise ProductionError("order_unconfirmed") from error
            raise
        except (httpx.RequestError, ValueError, KeyError, TypeError) as error:
            raise ProductionError("order_unconfirmed") from error

    def collect(self, operation: str) -> bytes | None:
        result = self.request("GET", "models/videos/" + quote(operation, safe=""))
        if result["status"] in {"pending", "processing"}:
            return None
        if result["status"] in {"failed", "cancelled"}:
            raise ProductionError("lipsync_failed")
        if result["status"] != "completed":
            raise ValueError("Unexpected Avatar 6 status")
        return download_result(result["video_url"], 64 * 1024 * 1024)
