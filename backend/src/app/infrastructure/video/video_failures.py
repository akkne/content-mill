"""Translate operational failures into safe, localizable video diagnostics."""

import re
import subprocess

import httpx

from app.application.videos.production import ProductionError
from app.application.voices.catalog import CatalogError
from app.domain.knowledge import DocumentStorageError

HTTP_REASONS = {
    400: "invalid_input",
    401: "authentication",
    402: "balance",
    403: "permission",
    404: "not_found",
    408: "timeout",
    409: "conflict",
    410: "expired",
    413: "too_large",
    415: "unsupported_format",
    422: "invalid_input",
    429: "rate_limit",
    451: "moderation",
    504: "timeout",
}

PROVIDER_REASONS = {
    "BAD_REQUEST": "invalid_input",
    "UNAUTHORIZED": "authentication",
    "PAYMENT_REQUIRED": "balance",
    "FORBIDDEN": "permission",
    "NOT_FOUND": "not_found",
    "REQUEST_TIMEOUT": "timeout",
    "CONFLICT": "conflict",
    "PAYLOAD_TOO_LARGE": "too_large",
    "UNPROCESSABLE_ENTITY": "invalid_input",
    "TOO_MANY_REQUESTS": "rate_limit",
    "RATE_LIMIT_EXCEEDED": "rate_limit",
    "INTERNAL_SERVER_ERROR": "provider_down",
    "BAD_GATEWAY": "provider_down",
    "SERVICE_UNAVAILABLE": "provider_down",
    "GATEWAY_TIMEOUT": "timeout",
    "CONTENT_POLICY_VIOLATION": "moderation",
    "CONTENT_MODERATION": "moderation",
    "HF_USAGE_EXHAUSTED": "balance",
    "INSUFFICIENT_QUOTA": "balance",
    "INVALID_PARAMETER": "invalid_input",
    "REQUEST_IN_PROGRESS": "conflict",
    "MODEL_NOT_FOUND": "not_found",
    "CONTEXT_LENGTH_EXCEEDED": "too_large",
    "OVERLOADED_ERROR": "provider_down",
    "PERMISSION_ERROR": "permission",
    "AUTHENTICATION_ERROR": "authentication",
    "RATE_LIMIT_ERROR": "rate_limit",
}


def provider_cause(body: object) -> dict:
    if not isinstance(body, dict):
        return {}
    code = body.get("code") or body.get("type")
    metadata = body.get("metadata")
    raw = metadata.get("raw") if isinstance(metadata, dict) else None
    text = " ".join(s.lower() for s in (body.get("message"), raw) if isinstance(s, str))
    detail = {}
    if isinstance(code, str) and re.fullmatch(
        r"[A-Z][A-Z0-9_]{1,47}|[a-z][a-z0-9_]{1,47}", code
    ):
        detail["provider_code"] = code
        if code.upper() in PROVIDER_REASONS:
            detail["reason"] = PROVIDER_REASONS[code.upper()]
    if "prominent public figure" in text:
        detail["reason"] = "public_figure"
    elif any(
        word in text
        for word in ("модерац", "content policy", "content moderation", "safety filter")
    ):
        detail["reason"] = "moderation"
    return detail


def http_failure(error: httpx.HTTPStatusError) -> dict:
    status = error.response.status_code
    try:
        body = error.response.json()
    except (ValueError, httpx.ResponseNotRead):
        body = None
    cause = provider_cause(body.get("error")) if isinstance(body, dict) else {}
    return {
        "http_status": status,
        "reason": HTTP_REASONS.get(
            status, "provider_down" if status >= 500 else "http_error"
        ),
        **cause,
    }


def describe_video_error(error: BaseException, stage: str) -> dict:
    detail = {"stage": stage}
    if isinstance(error, ProductionError):
        return {**detail, "reason": error.code, **error.detail}
    if isinstance(error, DocumentStorageError):
        return {**detail, "reason": "storage"}
    if isinstance(error, CatalogError) and error.__cause__:
        return describe_video_error(error.__cause__, stage)
    if isinstance(error, httpx.HTTPStatusError):
        return {**detail, **http_failure(error)}
    if isinstance(
        error, (httpx.TimeoutException, subprocess.TimeoutExpired, TimeoutError)
    ):
        reason = "timeout"
    elif isinstance(error, httpx.RequestError):
        reason = "network"
    elif isinstance(error, (ValueError, KeyError, TypeError, AttributeError)):
        reason = {
            "script": "invalid_script",
            "storyboard": "invalid_storyboard",
            "edit": "invalid_edit",
            "render": "render_failed",
            "dub": "audio_failed",
            "mix_speech": "audio_failed",
        }.get(stage, "invalid_response")
    elif isinstance(error, CatalogError):
        reason = HTTP_REASONS.get(error.status, "speech_unavailable")
    elif isinstance(error, subprocess.CalledProcessError):
        reason = "media_processing"
    elif isinstance(error, RuntimeError) and stage in ("script", "edit", "storyboard"):
        reason = "model_failed"
    else:
        reason = "stage_failed"
    return {**detail, "reason": reason}
