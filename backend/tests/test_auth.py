import os
from uuid import uuid4

import pytest
from app.db import connection, migrate
from app.main import app
from argon2 import PasswordHasher
from fastapi.testclient import TestClient


@pytest.fixture
def account():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for auth integration tests")
    migrate()
    user_id = uuid4()
    email = f"test-{user_id}@example.test"
    with connection() as conn:
        conn.execute(
            "INSERT INTO users (id, email, display_name, password_hash) "
            "VALUES (%s, %s, %s, %s)",
            (user_id, email, "Тестовый пользователь", PasswordHasher().hash("correct-password-123")),
        )
    yield email, user_id
    with connection() as conn:
        conn.execute(
            "DELETE FROM access_tokens WHERE session_id IN "
            "(SELECT id FROM auth_sessions WHERE user_id = %s)",
            (user_id,),
        )
        conn.execute("DELETE FROM auth_sessions WHERE user_id = %s", (user_id,))
        conn.execute("DELETE FROM users WHERE id = %s", (user_id,))


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
        with connection() as conn:
            stored = conn.execute(
                "SELECT refresh_hash FROM auth_sessions WHERE user_id = %s", (user_id,)
            ).fetchone()
        assert stored["refresh_hash"] != first["refresh_token"]
        assert len(stored["refresh_hash"]) == 64
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
        assert client.get(
            "/api/v1/me", headers={"Authorization": f"Bearer {first['access_token']}"}
        ).status_code == 401

        replay = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
        )
        assert replay.status_code == 401
        assert client.get(
            "/api/v1/me", headers={"Authorization": f"Bearer {second['access_token']}"}
        ).status_code == 401

        new_login = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "correct-password-123"},
        ).json()
        logout = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": new_login["refresh_token"]},
        )
        assert logout.status_code == 204
        assert client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {new_login['access_token']}"},
        ).status_code == 401


def test_login_is_rate_limited(account):
    email, _ = account
    with TestClient(app) as client:
        for _ in range(10):
            assert client.post(
                "/api/v1/auth/login", json={"email": email, "password": "wrong"}
            ).status_code == 401
        limited = client.post(
            "/api/v1/auth/login", json={"email": email, "password": "wrong"}
        )
        assert limited.status_code == 429
        assert limited.json()["error"]["code"] == "rate_limited"
