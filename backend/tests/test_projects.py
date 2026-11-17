import os
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from app.container import auth_service
from app.infrastructure.database.models import (
    AccessTokenModel,
    ProjectContextModel,
    ProjectModel,
    RefreshSessionModel,
    UserModel,
)
from app.infrastructure.database.session import session_factory
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import delete, select


@pytest.fixture(scope="session")
def migrated_database():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required")
    config = Config(str(Path(__file__).parents[1] / "src" / "alembic.ini"))
    command.upgrade(config, "head")


@pytest.fixture
def login(migrated_database):
    users = []

    def create() -> dict[str, str]:
        email = f"project-{uuid4()}@example.test"
        user = auth_service().create_or_reset_user(
            email, "Project tester", "password-12345"
        )
        users.append(user.id)
        with TestClient(app) as client:
            pair = client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "password-12345"},
            ).json()
        return {"Authorization": f"Bearer {pair['access_token']}"}

    yield create
    with session_factory()() as session:
        for user_id in users:
            project_ids = select(ProjectModel.id).where(
                ProjectModel.owner_id == user_id
            )
            session.execute(
                delete(ProjectContextModel).where(
                    ProjectContextModel.project_id.in_(project_ids)
                )
            )
            session.execute(
                delete(ProjectModel).where(ProjectModel.owner_id == user_id)
            )
            sessions = select(RefreshSessionModel.id).where(
                RefreshSessionModel.user_id == user_id
            )
            session.execute(
                delete(AccessTokenModel).where(
                    AccessTokenModel.session_id.in_(sessions)
                )
            )
            session.execute(
                delete(RefreshSessionModel).where(
                    RefreshSessionModel.user_id == user_id
                )
            )
            session.execute(delete(UserModel).where(UserModel.id == user_id))
        session.commit()


def test_projects_context_owner_and_revisions(login):
    owner = login()
    stranger = login()
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/projects", json={"name": "  Brand  "}, headers=owner
        )
        assert created.status_code == 201
        project = created.json()
        project_id = project["id"]
        assert project["name"] == "Brand"
        assert (
            client.get("/api/v1/projects", headers=owner).json()["items"][0]["id"]
            == project_id
        )
        second_id = client.post(
            "/api/v1/projects", json={"name": "Second"}, headers=owner
        ).json()["id"]
        first_page = client.get("/api/v1/projects?limit=1", headers=owner).json()
        next_page = client.get(
            f"/api/v1/projects?limit=1&cursor={first_page['next_cursor']}",
            headers=owner,
        ).json()
        assert {first_page["items"][0]["id"], next_page["items"][0]["id"]} == {
            project_id,
            second_id,
        }
        assert next_page["next_cursor"] is None
        assert client.get("/api/v1/projects", headers=stranger).json()["items"] == []
        assert (
            client.get(f"/api/v1/projects/{project_id}", headers=stranger).status_code
            == 404
        )
        assert (
            client.get(
                f"/api/v1/projects/{project_id}/context", headers=stranger
            ).status_code
            == 404
        )
        assert {
            item["id"]
            for item in client.get("/api/v1/me", headers=owner).json()["projects"]
        } == {project_id, second_id}

        path = f"/api/v1/projects/{project_id}/context"
        assert client.get(path, headers=owner).json()["revision"] == 1
        assert client.put(path, json={}, headers=owner).status_code == 428
        payload = {
            "description": "Client profile",
            "audiences": ["Creators"],
            "products": [{"name": "Course", "description": "Video"}],
            "facts": [{"text": "Founded in 2020", "source_url": "https://example.com"}],
            "tone_of_voice": "Clear",
            "forbidden_terms": ["hype"],
            "source_version_ids": [],
        }
        headers = {**owner, "If-Match": "1"}
        saved = client.put(path, json=payload, headers=headers)
        assert saved.status_code == 200
        assert saved.json()["revision"] == 2
        assert saved.json()["products"] == payload["products"]
        assert client.get(path, headers=owner).json()["description"] == "Client profile"
        assert client.put(path, json=payload, headers=headers).status_code == 409
        assert (
            client.put(
                path, json=payload, headers={**stranger, "If-Match": "2"}
            ).status_code
            == 404
        )
        assert (
            client.put(
                path,
                json={**payload, "source_version_ids": [str(uuid4())]},
                headers={**owner, "If-Match": "2"},
            ).status_code
            == 422
        )

        rename = client.patch(
            f"/api/v1/projects/{project_id}", json={"name": "New name"}, headers=headers
        )
        assert rename.status_code == 200
        assert rename.json()["revision"] == 2
        assert (
            client.patch(
                f"/api/v1/projects/{project_id}", json={"name": "Old"}, headers=headers
            ).status_code
            == 409
        )
