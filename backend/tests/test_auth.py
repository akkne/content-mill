import os
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from app.container import auth_service
from app.infrastructure.database.models import (
    AccessTokenModel,
    RefreshSessionModel,
    UserModel,
)
from app.infrastructure.database.session import session_factory
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import delete, select


@pytest.fixture(scope="session")
def database_ready():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for auth integration tests")
    config = Config(str(Path(__file__).parents[1] / "src" / "alembic.ini"))
    command.upgrade(config, "head")


@pytest.fixture
def account(database_ready):
    email = f"test-{uuid4()}@example.test"
    user = auth_service().create_or_reset_user(
        email, "Тестовый пользователь", "correct-password-123"
    )
    yield email, user.id
    with session_factory()() as session:
        model = session.scalar(select(UserModel).where(UserModel.email == email))
        if model:
            session.execute(
                delete(AccessTokenModel).where(
                    AccessTokenModel.session_id.in_(
                        select(RefreshSessionModel.id).where(
                            RefreshSessionModel.user_id == model.id
                        )
                    )
                )
            )
            session.execute(
                delete(RefreshSessionModel).where(
                    RefreshSessionModel.user_id == model.id
                )
            )
            session.delete(model)
        session.commit()


def test_login_refresh_replay_and_logout(account):
    email, user_id = account
    with TestClient(app) as client:
        wrong = client.post(
            "/api/v1/auth/login", json={"email": email, "password": "wrong-password"}
        )
        assert wrong.status_code == 401
        assert wrong.json()["error"]["code"] == "unauthorized"
        assert client.get("/api/v1/me").status_code == 401

        login = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "correct-password-123"},
        )
        assert login.status_code == 200
        first = login.json()
        with session_factory()() as session:
            stored = session.scalar(
                select(RefreshSessionModel).where(
                    RefreshSessionModel.refresh_hash
                    == auth_service().tokens.hash(first["refresh_token"])
                )
            )
            assert stored is not None
            assert stored.refresh_hash != first["refresh_token"]
            assert len(stored.refresh_hash) == 64
        me = client.get(
            "/api/v1/me", headers={"Authorization": f"Bearer {first['access_token']}"}
        )
        assert me.status_code == 200
        assert me.json() == {
            "id": str(user_id),
            "display_name": "Тестовый пользователь",
            "projects": [],
        }

        refresh = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
        )
        assert refresh.status_code == 200
        second = refresh.json()
        assert second["refresh_token"] != first["refresh_token"]
        assert (
            client.get(
                "/api/v1/me",
                headers={"Authorization": f"Bearer {first['access_token']}"},
            ).status_code
            == 401
        )

        replay = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
        )
        assert replay.status_code == 401
        assert (
            client.get(
                "/api/v1/me",
                headers={"Authorization": f"Bearer {second['access_token']}"},
            ).status_code
            == 401
        )

        new_login = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "correct-password-123"},
        ).json()
        logout = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": new_login["refresh_token"]},
        )
        assert logout.status_code == 204
        assert (
            client.get(
                "/api/v1/me",
                headers={"Authorization": f"Bearer {new_login['access_token']}"},
            ).status_code
            == 401
        )


def test_login_is_rate_limited(account):
    email, _ = account
    with TestClient(app) as client:
        for _ in range(10):
            assert (
                client.post(
                    "/api/v1/auth/login", json={"email": email, "password": "wrong"}
                ).status_code
                == 401
            )
        limited = client.post(
            "/api/v1/auth/login", json={"email": email, "password": "wrong"}
        )
        assert limited.status_code == 429
        assert limited.json()["error"]["code"] == "rate_limited"
