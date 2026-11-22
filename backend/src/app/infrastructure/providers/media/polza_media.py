import base64
import re
from datetime import UTC, datetime

import httpx

from app.application.videos.production import ProductionError
from app.infrastructure.video.video_failures import http_failure, provider_cause


def image_input(data: bytes, mime: str) -> dict[str, str]:
    return {
        "type": "base64",
        "data": f"data:{mime};base64," + base64.b64encode(data).decode("ascii"),
    }


class PolzaMedia:
    def __init__(self, key: str):
        self.key = key

    def request(self, method: str, path: str, payload: dict | None = None) -> dict:
        if not self.key:
            raise ProductionError("polza_key")
        response = httpx.request(
            method,
            "https://polza.ai/api/v1/media" + path,
            headers={"Authorization": "Bearer " + self.key},
            json=payload,
            timeout=120,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            legacy = {
                401: "polza_access",
                403: "polza_access",
                402: "polza_balance",
                429: "polza_limit",
            }
            if code := legacy.get(response.status_code):
                raise ProductionError(code, **http_failure(error)) from error
            raise
        return response.json()

    def submit(self, model: str, inputs: dict) -> str:
        started = datetime.now(UTC).isoformat()
        try:
            result = self.request(
                "POST", "", {"model": model, "input": inputs, "async": True}
            )
            identifier = result.get("id") if isinstance(result, dict) else None
            if not isinstance(identifier, str) or not re.fullmatch(
                r"[A-Za-z0-9_-]{1,200}", identifier
            ):
                raise ValueError("Missing Polza operation ID")
        except (httpx.TransportError, ValueError) as error:
            raise ProductionError(
                "order_unconfirmed", model=model, attempted_at=started
            ) from error
        return "polza:" + identifier

    def collect(self, operation: str, limit: int, rejected: str) -> bytes | None:
        provider, _, identifier = operation.partition(":")
        if provider != "polza":
            raise ProductionError("legacy_operation")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", identifier):
            raise ValueError("Invalid Polza operation ID")
        result = self.request("GET", "/" + identifier)
        if result["status"] in {"pending", "processing"}:
            return None
        if result["status"] in {"failed", "cancelled"}:
            cause = provider_cause(result.get("error"))
            if result["status"] == "cancelled":
                cause.setdefault("reason", "cancelled")
            raise ProductionError(rejected, **cause)
        if result["status"] != "completed":
            raise ValueError("Unexpected Polza status")
        asset = result.get("data")
        if isinstance(asset, list) and asset:
            asset = asset[0]
        location = asset.get("url") if isinstance(asset, dict) else None
        if not location or not isinstance(location, str):
            raise ValueError("Completed Polza operation has no asset URL")
        url = httpx.URL(location)
        if url.scheme != "https" or not (
            url.host == "polza.ai" or url.host.endswith(".polza.ai")
        ):
            raise ValueError("Unexpected Polza asset URL")
        with httpx.stream("GET", url, timeout=90) as response:
            response.raise_for_status()
            data = bytearray()
            for chunk in response.iter_bytes():
                data.extend(chunk)
                if len(data) > limit:
                    raise ValueError("Oversized Polza asset")
        return bytes(data)
