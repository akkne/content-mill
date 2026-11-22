import base64

import httpx

from app.application.videos.production import ProductionError


def data_uri(mime: str, data: bytes) -> str:
    return f"data:{mime};base64," + base64.b64encode(data).decode()


class FalMedia:
    def __init__(self, key: str):
        self.key = key

    def request(self, method: str, url: str, payload: dict | None = None) -> dict:
        if not self.key:
            raise ProductionError("fal_key")
        response = httpx.request(
            method,
            url,
            headers={"Authorization": "Key " + self.key},
            json=payload,
            timeout=180,
        )
        if response.status_code in (401, 403):
            raise ProductionError("fal_access")
        if response.status_code == 402:
            raise ProductionError("fal_balance")
        if response.status_code == 422:
            raise ProductionError(
                "clip_rejected" if "/requests/" in url else "invalid_input"
            )
        response.raise_for_status()
        return response.json()

    def download(self, url: str, limit: int) -> bytes:
        parsed = httpx.URL(url)
        host = parsed.host
        if parsed.scheme != "https" or not (
            host in {"fal.media", "storage.googleapis.com"}
            or host.endswith(".fal.media")
        ):
            raise ValueError("Unexpected fal asset URL")
        with httpx.stream("GET", url, timeout=90) as res:
            res.raise_for_status()
            data = bytearray()
            for chunk in res.iter_bytes():
                data.extend(chunk)
                if len(data) > limit:
                    raise ValueError("Oversized media")
            return bytes(data)
