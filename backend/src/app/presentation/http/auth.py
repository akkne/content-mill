from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response

from app.application.auth_service import AuthService
from app.application.project_service import ProjectService
from app.container import auth_service, project_service
from app.domain.auth import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidSession,
    TokenPair,
    TooManyAttempts,
    User,
)
from app.presentation.http.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
)

router = APIRouter(prefix="/api/v1")
Service = Annotated[AuthService, Depends(auth_service)]


def current_user(
    service: Service, authorization: str | None = Header(default=None)
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Сессия недействительна")
    try:
        return service.current_user(authorization.removeprefix("Bearer "))
    except InvalidSession as error:
        raise HTTPException(status_code=401, detail="Сессия недействительна") from error


def token_response(pair: TokenPair, response: Response) -> TokenPairResponse:
    response.headers["Cache-Control"] = "no-store"
    return TokenPairResponse.model_validate(pair, from_attributes=True)


@router.post("/auth/register", response_model=TokenPairResponse, status_code=201)
def register(
    payload: RegisterRequest, request: Request, response: Response, service: Service
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


@router.post("/auth/login", response_model=TokenPairResponse)
def login(
    payload: LoginRequest, request: Request, response: Response, service: Service
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
    payload: RefreshRequest, response: Response, service: Service
) -> TokenPairResponse:
    try:
        pair = service.refresh(payload.refresh_token)
    except InvalidSession as error:
        raise HTTPException(status_code=401, detail="Сессия недействительна") from error
    return token_response(pair, response)


@router.post("/auth/logout", status_code=204)
def logout(payload: RefreshRequest, service: Service) -> None:
    service.logout(payload.refresh_token)


@router.get("/me")
def me(
    user: Annotated[User, Depends(current_user)],
    projects: Annotated[ProjectService, Depends(project_service)],
) -> dict:
    owned = projects.list_projects(user.id, 100)
    return {
        "id": user.id,
        "display_name": user.display_name,
        "projects": [
            {"id": item.id, "name": item.name, "role": "owner"} for item in owned[:100]
        ],
    }
