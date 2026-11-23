from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.application.projects.service import ProjectService
from app.container import project_service
from app.domain.auth import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidSession,
    TokenPair,
    TooManyAttempts,
)
from app.owner import configured_owner
from app.presentation.http.dependencies import (
    AuthServiceDependency,
    CurrentUser,
    is_admin,
)
from app.presentation.http.schemas.auth import (
    LoginRequest,
    OwnerSetupRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
)

router = APIRouter(prefix="/api/v1")


def token_response(pair: TokenPair, response: Response) -> TokenPairResponse:
    response.headers["Cache-Control"] = "no-store"
    return TokenPairResponse.model_validate(pair, from_attributes=True)


@router.post("/auth/register", response_model=TokenPairResponse, status_code=201)
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    service: AuthServiceDependency,
) -> TokenPairResponse:
    client_ip = request.client.host if request.client else "unknown"
    try:
        pair = service.register(
            payload.email, payload.display_name, payload.password, client_ip
        )
    except EmailAlreadyRegistered as error:
        raise HTTPException(
            status_code=409, detail="Не удалось зарегистрировать эту почту"
        ) from error
    except TooManyAttempts as error:
        raise HTTPException(
            status_code=429, detail="Слишком много попыток. Повторите через 15 минут"
        ) from error
    return token_response(pair, response)


@router.post("/auth/owner-setup", response_model=TokenPairResponse)
def owner_setup(
    payload: OwnerSetupRequest, response: Response, service: AuthServiceDependency
) -> TokenPairResponse:
    owner = configured_owner()
    if owner is None:
        raise HTTPException(status_code=403, detail="Ссылка недействительна")
    try:
        pair = service.complete_owner_setup(
            owner, payload.token, payload.email, payload.password
        )
    except InvalidSession as error:
        raise HTTPException(status_code=403, detail="Ссылка недействительна") from error
    except EmailAlreadyRegistered as error:
        raise HTTPException(status_code=409, detail="Эта почта уже занята") from error
    return token_response(pair, response)


@router.post("/auth/login", response_model=TokenPairResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    service: AuthServiceDependency,
) -> TokenPairResponse:
    client_ip = request.client.host if request.client else "unknown"
    try:
        pair = service.login(payload.email.strip().lower(), payload.password, client_ip)
    except InvalidCredentials as error:
        raise HTTPException(
            status_code=401, detail="Неверная почта или пароль"
        ) from error
    except TooManyAttempts as error:
        raise HTTPException(
            status_code=429, detail="Слишком много попыток. Повторите через 15 минут"
        ) from error
    return token_response(pair, response)


@router.post("/auth/refresh", response_model=TokenPairResponse)
def refresh(
    payload: RefreshRequest, response: Response, service: AuthServiceDependency
) -> TokenPairResponse:
    try:
        pair = service.refresh(payload.refresh_token)
    except InvalidSession as error:
        raise HTTPException(status_code=401, detail="Сессия недействительна") from error
    return token_response(pair, response)


@router.post("/auth/logout", status_code=204)
def logout(payload: RefreshRequest, service: AuthServiceDependency) -> None:
    service.logout(payload.refresh_token)


@router.get("/me")
def me(
    user: CurrentUser,
    projects: Annotated[ProjectService, Depends(project_service)],
) -> dict:
    owned = projects.list_projects(user.id, 100)
    return {
        "id": user.id,
        "display_name": user.display_name,
        **({"is_admin": True} if is_admin(user.id) else {}),
        "projects": [
            {"id": item.id, "name": item.name, "role": "owner"} for item in owned[:100]
        ],
    }
