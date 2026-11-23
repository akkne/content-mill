import httpx

from app.application.videos.production import ProductionError
from app.infrastructure.providers.media.media_download import download_result
from app.infrastructure.video.video_failures import provider_cause


class HeyGenLipSync:
    def __init__(self, key: str):
        self.key = key

    def request(self, method, path, **kwargs):
        if not self.key:
            raise ProductionError("heygen_key")
        response = httpx.request(
            method,
            "https://api.heygen.com/v3/" + path,
            headers={"X-Api-Key": self.key},
            timeout=120,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()["data"]

    def submit(self, video: bytes, audio: bytes) -> str:
        def upload(name, body, fmt):
            if len(body) > 50_000_000:
                raise ProductionError("lipsync_input")
            asset = self.request("POST", "assets", files={"file": (name, body, fmt)})
            return {"type": "asset_id", "asset_id": asset["asset_id"]}

        payload = {
            "mode": "precision",
            "video": upload("scene.mp4", video, "video/mp4"),
            "audio": upload("speech.wav", audio, "audio/wav"),
        }
        try:
            order = self.request("POST", "lipsyncs", json=payload)["lipsync_id"]
            if not isinstance(order, str) or not order:
                raise ValueError("Missing order ID")
            return order
        except httpx.HTTPStatusError as error:
            if error.response.status_code >= 500:
                raise ProductionError("order_unconfirmed") from error
            raise
        except (httpx.RequestError, ValueError, TypeError, KeyError) as error:
            raise ProductionError("order_unconfirmed") from error

    def collect(self, operation: str) -> bytes | None:
        result = self.request("GET", "lipsyncs/" + operation)
        if result["status"] in (
            "pending",
            "running",
        ):
            return None
        if result["status"] == "failed":
            cause = provider_cause(
                {
                    "code": result.get("failure_code"),
                    "message": result.get("failure_message"),
                }
            )
            raise ProductionError("lipsync_failed", **cause)
        if result["status"] != "completed":
            raise ValueError("Unexpected HeyGen order status")
        return download_result(result["video_url"], 64 * 1024 * 1024)
