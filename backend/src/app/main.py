from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.presentation.http.auth import router as auth_router
from app.presentation.http.knowledge import router as knowledge_router
from app.presentation.http.projects import router as projects_router
from app.presentation.http.search import router as search_router

app = FastAPI(title="Content Mill API")
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
