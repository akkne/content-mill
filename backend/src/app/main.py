import asyncio
import logging
from collections.abc import Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.routing import Route

from app.container import knowledge_service, script_writer, video_production
from app.domain.project import ProjectNotFound
from app.domain.video import InvalidVideo, VideoNotFound, VideoTextUnavailable
from app.infrastructure.video_failures import describe_video_error
from app.presentation.http.agent_tokens import router as agent_tokens_router
from app.presentation.http.auth import router as auth_router
from app.presentation.http.avatars import router as avatars_router
from app.presentation.http.knowledge import router as knowledge_router
from app.presentation.http.media import router as media_router
from app.presentation.http.projects import router as projects_router
from app.presentation.http.script_jobs import router as script_jobs_router
from app.presentation.http.search import router as search_router
from app.presentation.http.videos import router as videos_router
from app.presentation.http.voices import router as voices_router
from app.presentation.mcp import ProjectMcpEndpoint, create_mcp


async def cleanup_loop():
    while True:
        await asyncio.sleep(60)
        try:
            await asyncio.to_thread(knowledge_service().clean_uploads)
        except Exception:
            logging.getLogger(__name__).exception("Failed to clean expired uploads")


async def queue_loop(run_next: Callable[[], bool]):
    while True:
        try:
            worked = await asyncio.to_thread(run_next)
        except Exception:
            logging.getLogger(__name__).exception("Job queue unavailable")
            worked = False
        await asyncio.sleep(0 if worked else 5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    writer = script_writer()
    mcp = create_mcp()
    app.state.mcp_app = mcp.streamable_http_app()
    async with mcp.session_manager.run():
        tasks = [
            asyncio.create_task(cleanup_loop()),
            asyncio.create_task(queue_loop(writer.run_next)),
            asyncio.create_task(queue_loop(video_production().run_next)),
        ]
        try:
            yield
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(title="Content Mill API", lifespan=lifespan)
app.router.routes.append(
    Route("/mcp", endpoint=ProjectMcpEndpoint(), methods=["POST", "GET", "DELETE"])
)
app.include_router(script_jobs_router)
app.include_router(agent_tokens_router)
app.include_router(videos_router)
app.include_router(media_router)
app.include_router(avatars_router)
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


@app.exception_handler(VideoTextUnavailable)
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
