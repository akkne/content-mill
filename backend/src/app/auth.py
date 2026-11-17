import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID, uuid4

import psycopg
from argon2 import PasswordHasher, exceptions
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.db import connection

router = APIRouter(prefix="/api/v1")
password_hasher = PasswordHasher()
dummy_password_hash = password_hasher.hash("unusable-dummy-password")
ACCESS_LIFETIME = timedelta(minutes=15)
REFRESH_LIFETIME = timedelta(days=14)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=1024)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=256)


class TokenPair(BaseModel):
    access_token: str
    access_expires_at: datetime
    refresh_token: str
    refresh_expires_at: datetime


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_tokens(conn: psycopg.Connection, user_id: UUID, family_id: UUID) -> TokenPair:
    now = datetime.now(UTC)
    access = f"cm_at_{secrets.token_urlsafe(32)}"
    refresh = f"cm_rt_{secrets.token_urlsafe(32)}"
    session_id = uuid4()
    access_expiry = now + ACCESS_LIFETIME
    refresh_expiry = now + REFRESH_LIFETIME
    conn.execute(
        "INSERT INTO auth_sessions (id, user_id, family_id, refresh_hash, expires_at) "
        "VALUES (%s, %s, %s, %s, %s)",
        (session_id, user_id, family_id, token_hash(refresh), refresh_expiry),
    )
    conn.execute(
        "INSERT INTO access_tokens (token_hash, session_id, expires_at) "
        "VALUES (%s, %s, %s)",
        (token_hash(access), session_id, access_expiry),
    )
    return TokenPair(
        access_token=access,
        access_expires_at=access_expiry,
        refresh_token=refresh,
        refresh_expires_at=refresh_expiry,
    )


def invalid_credentials() -> HTTPException:
    return HTTPException(status_code=401, detail="Неверная почта или пароль")


def invalid_session() -> HTTPException:
    return HTTPException(status_code=401, detail="Сессия недействительна")


def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer cm_at_"):
        raise invalid_session()
    token = authorization.removeprefix("Bearer ")
    if len(token) > 256:
        raise invalid_session()
    with connection() as conn:
        user = conn.execute(
            "SELECT u.id, u.display_name FROM access_tokens a "
            "JOIN auth_sessions s ON s.id = a.session_id "
            "JOIN users u ON u.id = s.user_id "
            "WHERE a.token_hash = %s AND a.expires_at > now() "
            "AND s.revoked_at IS NULL AND s.expires_at > now()",
            (token_hash(token),),
        ).fetchone()
    if user is None:
        raise invalid_session()
    return user


@router.post("/auth/login", response_model=TokenPair)
def login(payload: LoginRequest, request: Request) -> TokenPair:
    email = payload.email.strip().lower()
    client_ip = request.client.host if request.client else "unknown"
    attempt_key = token_hash(f"{client_ip}:{email}")
    with connection() as conn:
        conn.execute("DELETE FROM login_attempts WHERE attempted_at < now() - interval '15 minutes'")
        count = conn.execute(
            "SELECT count(*) AS count FROM login_attempts WHERE attempt_key = %s",
            (attempt_key,),
        ).fetchone()["count"]
        if count >= 10:
            raise HTTPException(status_code=429, detail="Слишком много попыток. Повторите через 15 минут")
        user = conn.execute(
            "SELECT id, password_hash FROM users WHERE email = %s", (email,)
        ).fetchone()
        try:
            valid = password_hasher.verify(
                user["password_hash"] if user else dummy_password_hash,
                payload.password,
            )
        except (exceptions.VerifyMismatchError, exceptions.VerificationError):
            valid = False
        if not valid or user is None:
            conn.execute("INSERT INTO login_attempts (attempt_key) VALUES (%s)", (attempt_key,))
            conn.commit()
            raise invalid_credentials()
        conn.execute("DELETE FROM login_attempts WHERE attempt_key = %s", (attempt_key,))
        return issue_tokens(conn, user["id"], uuid4())


@router.post("/auth/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest) -> TokenPair:
    if not payload.refresh_token.startswith("cm_rt_"):
        raise invalid_session()
    with connection() as conn:
        session = conn.execute(
            "SELECT id, user_id, family_id, expires_at, revoked_at, rotated_at "
            "FROM auth_sessions WHERE refresh_hash = %s FOR UPDATE",
            (token_hash(payload.refresh_token),),
        ).fetchone()
        if session is None:
            raise invalid_session()
        if session["rotated_at"] is not None:
            conn.execute(
                "UPDATE auth_sessions SET revoked_at = now() "
                "WHERE family_id = %s AND revoked_at IS NULL",
                (session["family_id"],),
            )
            conn.commit()
            raise invalid_session()
        if session["revoked_at"] is not None or session["expires_at"] <= datetime.now(UTC):
            raise invalid_session()
        conn.execute(
            "UPDATE auth_sessions SET revoked_at = now(), rotated_at = now() WHERE id = %s",
            (session["id"],),
        )
        return issue_tokens(conn, session["user_id"], session["family_id"])


@router.post("/auth/logout", status_code=204)
def logout(payload: RefreshRequest) -> None:
    with connection() as conn:
        session = conn.execute(
            "SELECT family_id FROM auth_sessions WHERE refresh_hash = %s",
            (token_hash(payload.refresh_token),),
        ).fetchone()
        if session:
            conn.execute(
                "UPDATE auth_sessions SET revoked_at = now() "
                "WHERE family_id = %s AND revoked_at IS NULL",
                (session["family_id"],),
            )


@router.get("/me")
def me(user: Annotated[dict, Depends(current_user)]) -> dict:
    return {"id": user["id"], "display_name": user["display_name"], "projects": []}
