from urllib.parse import quote

import httpx

from app.application.videos.production import ProductionError
from app.infrastructure.providers.media.media_download import download_result


class HeyGenAPI:
    model: str

    def __init__(self, key: str):
        self.key = key

    def request(self, method, path, **kwargs):
        if not self.key:
            raise ProductionError("heygen_key")
        response = httpx.request(
            method,
            "https://api.heygen.com/v3/" + path,
            headers={"X-Api-Key": self.key, **kwargs.pop("headers", {})},
            timeout=120,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()["data"]

    def create_video(self, path: str, payload: dict, **options) -> str:
        try:
            order = self.request("POST", path, json=payload, **options)["video_id"]
            if not isinstance(order, str) or not order:
                raise ValueError("Missing video ID")
            return order
        except httpx.HTTPStatusError as error:
            if error.response.status_code >= 500:
                raise ProductionError("order_unconfirmed", model=self.model) from error
            raise
        except (httpx.RequestError, ValueError, KeyError, TypeError) as error:
            raise ProductionError("order_unconfirmed", model=self.model) from error

    def collect_video(self, operation: str, rejection: str) -> bytes | None:
        result = self.request("GET", "models/videos/" + quote(operation, safe=""))
        if result["status"] in {"pending", "processing"}:
            return None
        if result["status"] in {"failed", "cancelled"}:
            raise ProductionError(rejection)
        if result["status"] != "completed":
            raise ValueError("Unexpected HeyGen video status")
        return download_result(result["video_url"], 64 * 1024 * 1024)
