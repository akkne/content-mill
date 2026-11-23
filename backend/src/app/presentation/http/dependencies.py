import os
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException

from app.application.auth.service import AuthService
from app.application.knowledge.service import KnowledgeService
from app.container import auth_service, knowledge_service
from app.domain.auth import InvalidSession, User

AuthServiceDependency = Annotated[AuthService, Depends(auth_service)]
KnowledgeServiceDependency = Annotated[KnowledgeService, Depends(knowledge_service)]


def current_user(
    service: AuthServiceDependency, authorization: str | None = Header(default=None)
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Сессия недействительна")
    try:
        return service.current_user(authorization.removeprefix("Bearer "))
    except InvalidSession as error:
        raise HTTPException(status_code=401, detail="Сессия недействительна") from error


CurrentUser = Annotated[User, Depends(current_user)]


def is_admin(user_id: UUID) -> bool:
    return str(user_id) == os.getenv("MILL_ADMIN_USER_ID", "").strip().lower()


def require_admin(user: CurrentUser) -> None:
    if not is_admin(user.id):
        raise HTTPException(status_code=403, detail="Требуется доступ администратора")


def expected_revision(value: str | None) -> int:
    if value is None:
        raise HTTPException(status_code=428, detail="Требуется заголовок If-Match")
    try:
        revision = int(value.strip('"'))
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Некорректный If-Match") from error
    if revision < 1:
        raise HTTPException(status_code=400, detail="Некорректный If-Match")
    return revision
