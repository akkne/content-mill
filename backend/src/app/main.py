import asyncio
import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.container import knowledge_service
from app.domain.project import ProjectNotFound
from app.domain.video import InvalidVideo, VideoNotFound
from app.presentation.http.auth import router as auth_router
from app.presentation.http.knowledge import router as knowledge_router
from app.presentation.http.media import router as media_router
from app.presentation.http.projects import router as projects_router
from app.presentation.http.search import router as search_router
from app.presentation.http.videos import router as videos_router
from app.presentation.http.voices import router as voices_router


async def cleanup_loop():
    while True:
        await asyncio.sleep(60)
        try:
            await asyncio.to_thread(knowledge_service().clean_uploads)
        except Exception:
            logging.getLogger(__name__).exception("Failed to clean expired uploads")


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(cleanup_loop())
    try:
        yield
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


app = FastAPI(title="Content Mill API", lifespan=lifespan)
app.include_router(videos_router)
app.include_router(media_router)
app.include_router(voices_router)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(knowledge_router)
app.include_router(search_router)


@app.exception_handler(HTTPException)
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


@app.exception_handler(ProjectNotFound)
@app.exception_handler(VideoNotFound)
def missing_resource(request: Request, error: Exception) -> JSONResponse:
    return handle_http_error(request, HTTPException(404, "Проект или ролик не найден"))


@app.exception_handler(InvalidVideo)
def invalid_video(request: Request, error: InvalidVideo) -> JSONResponse:
    return handle_http_error(request, HTTPException(422, str(error)))


@app.exception_handler(RequestValidationError)
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
