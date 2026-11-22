from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.routing import Route

from app.domain.project import ProjectNotFound
from app.domain.video import InvalidVideo, VideoNotFound, VideoTextUnavailable
from app.lifespan import lifespan
from app.presentation.http import errors
from app.presentation.http.router import router
from app.presentation.mcp import ProjectMcpEndpoint

app = FastAPI(title="Content Mill API", lifespan=lifespan)
app.router.routes.append(
    Route("/mcp", endpoint=ProjectMcpEndpoint(), methods=["POST", "GET", "DELETE"])
)
app.include_router(router)
app.add_exception_handler(HTTPException, errors.handle_http_error)
app.add_exception_handler(ProjectNotFound, errors.missing_resource)
app.add_exception_handler(VideoNotFound, errors.missing_resource)
app.add_exception_handler(VideoTextUnavailable, errors.unavailable_video_text)
app.add_exception_handler(InvalidVideo, errors.invalid_video)
app.add_exception_handler(RequestValidationError, errors.handle_validation_error)
