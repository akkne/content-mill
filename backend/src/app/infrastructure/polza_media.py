import base64
import re

import httpx

from app.application.video_production import ProductionError


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
        errors = {
            401: "polza_access",
            403: "polza_access",
            402: "polza_balance",
            429: "polza_limit",
        }
        if response.status_code in errors:
            raise ProductionError(errors[response.status_code])
        response.raise_for_status()
        return response.json()

    def submit(self, model: str, inputs: dict) -> str:
        result = self.request(
            "POST", "", {"model": model, "input": inputs, "async": True}
        )
        identifier = result["id"]
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", identifier):
            raise ValueError("Invalid Polza operation ID")
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
            raise ProductionError(rejected)
        if result["status"] != "completed":
            raise ValueError("Unexpected Polza status")
        url = httpx.URL(result["data"]["url"])
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
