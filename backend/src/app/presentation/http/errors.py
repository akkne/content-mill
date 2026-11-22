from uuid import uuid4

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.knowledge import DocumentStorageError, NodeConflict, NodeNotFound
from app.domain.project import ProjectNotFound, RevisionConflict
from app.domain.video import InvalidVideo, VideoTextUnavailable
from app.infrastructure.video.video_failures import describe_video_error


def translate(error: Exception) -> HTTPException:
    if isinstance(error, DocumentStorageError):
        return HTTPException(status_code=503, detail=str(error))
    if isinstance(error, (ProjectNotFound, NodeNotFound)):
        return HTTPException(status_code=404, detail="Ресурс не найден")
    if isinstance(error, RevisionConflict):
        return HTTPException(status_code=409, detail="Версия узла изменилась")
    if isinstance(error, NodeConflict):
        return HTTPException(status_code=409, detail="Имя уже занято в этой папке")
    return HTTPException(status_code=422, detail=str(error))


def handle_http_error(_: Request, error: HTTPException) -> JSONResponse:
    codes = {
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        429: "rate_limited",
        503: "service_unavailable",
    }
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": codes.get(error.status_code, "request_failed"),
                "message": str(error.detail),
                "request_id": str(uuid4()),
            }
        },
    )


def missing_resource(request: Request, error: Exception) -> JSONResponse:
    return handle_http_error(request, HTTPException(404, "Проект или ролик не найден"))


def unavailable_video_text(
    request: Request, error: VideoTextUnavailable
) -> JSONResponse:
    if error.__cause__ is None:
        return handle_http_error(request, HTTPException(503, str(error)))
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "video_script_failed",
                "message": str(error),
                "request_id": str(uuid4()),
                "failure": describe_video_error(error.__cause__, "script"),
            }
        },
    )


def invalid_video(request: Request, error: InvalidVideo) -> JSONResponse:
    return handle_http_error(request, HTTPException(422, str(error)))


def handle_validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Некорректные данные запроса",
                "request_id": str(uuid4()),
                "fields": [
                    ".".join(str(part) for part in item["loc"])
                    for item in error.errors()
                ],
            }
        },
    )
