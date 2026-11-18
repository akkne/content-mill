import os
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from app.application.knowledge_service import KnowledgeService
from app.container import auth_service, knowledge_service
from app.infrastructure.database.knowledge_unit_of_work import (
    SqlAlchemyKnowledgeUnitOfWork,
)
from app.infrastructure.database.models import (
    AccessTokenModel,
    DocumentVersionModel,
    KnowledgeNodeModel,
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
            node_ids = select(KnowledgeNodeModel.id).where(
                KnowledgeNodeModel.project_id.in_(project_ids)
            )
            session.execute(
                delete(DocumentVersionModel).where(
                    DocumentVersionModel.node_id.in_(node_ids)
                )
            )
            session.execute(
                delete(KnowledgeNodeModel).where(
                    KnowledgeNodeModel.project_id.in_(project_ids)
                )
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


def test_knowledge_tree_owner_moves_and_archive(login):
    owner = login()
    stranger = login()
    with TestClient(app) as client:
        project_id = client.post(
            "/api/v1/projects", json={"name": "Knowledge"}, headers=owner
        ).json()["id"]
        base = f"/api/v1/projects/{project_id}/nodes"
        assert client.get(base, headers=stranger).status_code == 404
        assert (
            client.post(
                base, json={"name": "Wrong", "kind": "folder"}, headers=stranger
            ).status_code
            == 404
        )
        initial = client.get(f"{base}/tree", headers=owner).json()["items"]
        assert {node["name"] for node in initial} >= {
            "Бренд",
            "Аватары",
            "Референсы",
            "Промпты",
        }
        brand = client.post(
            base, json={"name": "Client", "kind": "folder"}, headers=owner
        )
        assert brand.status_code == 201
        brand_id = brand.json()["id"]
        assert brand.json()["revision"] == 1
        products = client.post(
            base,
            json={"name": "Products", "kind": "folder", "parent_id": brand_id},
            headers=owner,
        )
        assert products.status_code == 201
        products_id = products.json()["id"]
        assert (
            client.get(f"{base}?parent_id={brand_id}", headers=owner).json()["items"][
                0
            ]["id"]
            == products_id
        )
        assert (
            len(client.get(f"{base}/tree", headers=owner).json()["items"])
            == len(initial) + 2
        )
        assert (
            client.post(
                base, json={"name": "client", "kind": "folder"}, headers=owner
            ).status_code
            == 409
        )
        other_project = client.post(
            "/api/v1/projects", json={"name": "Other"}, headers=owner
        ).json()["id"]
        assert (
            client.post(
                f"/api/v1/projects/{other_project}/nodes",
                json={"name": "Cross project", "kind": "folder", "parent_id": brand_id},
                headers=owner,
            ).status_code
            == 422
        )
        assert (
            client.patch(
                f"{base}/{brand_id}", json={"name": "Brand 2"}, headers=owner
            ).status_code
            == 428
        )
        renamed = client.patch(
            f"{base}/{brand_id}",
            json={"name": "Brand 2"},
            headers={**owner, "If-Match": "1"},
        )
        assert renamed.status_code == 200
        assert renamed.json()["revision"] == 2
        assert (
            client.patch(
                f"{base}/{brand_id}",
                json={"name": "Old"},
                headers={**owner, "If-Match": "1"},
            ).status_code
            == 409
        )
        assert (
            client.post(
                f"{base}/{brand_id}/move",
                json={"new_parent_id": products_id},
                headers={**owner, "If-Match": "2"},
            ).status_code
            == 422
        )
        moved = client.post(
            f"{base}/{products_id}/move",
            json={"new_parent_id": None},
            headers={**owner, "If-Match": "1"},
        )
        assert moved.status_code == 200
        assert moved.json()["parent_id"] is None
        archived_child = client.post(
            base,
            json={"name": "Rules", "kind": "folder", "parent_id": brand_id},
            headers=owner,
        ).json()["id"]
        assert (
            client.delete(
                f"{base}/{brand_id}", headers={**stranger, "If-Match": "2"}
            ).status_code
            == 404
        )
        assert (
            client.delete(
                f"{base}/{brand_id}", headers={**owner, "If-Match": "2"}
            ).status_code
            == 204
        )
        assert client.get(f"{base}/{brand_id}", headers=owner).status_code == 404
        assert client.get(f"{base}/{archived_child}", headers=owner).status_code == 404
        assert client.get(f"{base}/{products_id}", headers=owner).status_code == 200


def test_text_document_versions_and_access(login):
    class MemoryStore:
        def __init__(self):
            self.objects = {}

        def put(self, key, content, content_type):
            assert key not in self.objects
            self.objects[key] = content

        def get(self, key):
            return self.objects[key]

        def delete(self, key):
            self.objects.pop(key, None)

    store = MemoryStore()
    app.dependency_overrides[knowledge_service] = lambda: KnowledgeService(
        SqlAlchemyKnowledgeUnitOfWork, store
    )
    try:
        owner = login()
        stranger = login()
        with TestClient(app) as client:
            project_id = client.post(
                "/api/v1/projects", json={"name": "Documents"}, headers=owner
            ).json()["id"]
            base = f"/api/v1/projects/{project_id}/nodes"
            document = client.post(
                base, json={"name": "Voice.md", "kind": "document"}, headers=owner
            ).json()
            path = f"{base}/{document['id']}/content"
            empty = client.get(path, headers=owner)
            assert empty.json()["version"] == 0
            assert empty.json()["content"] == ""
            assert (
                client.put(
                    path, json={"content": "First", "format": "markdown"}, headers=owner
                ).status_code
                == 428
            )
            first = client.put(
                path,
                json={"content": "Первый", "format": "markdown"},
                headers={**owner, "If-Match": "1"},
            )
            assert first.status_code == 200
            assert first.json()["version"] == 1
            assert first.json()["revision"] == 2
            assert (
                client.put(
                    path,
                    json={"content": "stale", "format": "plain"},
                    headers={**owner, "If-Match": "1"},
                ).status_code
                == 409
            )
            second = client.put(
                path,
                json={"content": "Second", "format": "plain"},
                headers={**owner, "If-Match": "2"},
            )
            assert second.json()["version"] == 2
            assert (
                client.get(f"{path}?version=1", headers=owner).json()["content"]
                == "Первый"
            )
            assert client.get(path, headers=owner).json()["content"] == "Second"
            versions = client.get(
                f"{base}/{document['id']}/versions", headers=owner
            ).json()["items"]
            assert [item["version"] for item in versions] == [2, 1]
            assert "storage_key" not in versions[0]
            assert len(store.objects) == 2
            context_path = f"/api/v1/projects/{project_id}/context"
            linked = client.put(
                context_path,
                json={
                    "description": "From document",
                    "source_version_ids": [versions[0]["id"]],
                },
                headers={**owner, "If-Match": "1"},
            )
            assert linked.status_code == 200
            assert linked.json()["source_version_ids"] == [versions[0]["id"]]
            assert client.get(context_path, headers=owner).json()[
                "source_version_ids"
            ] == [versions[0]["id"]]
            other_project = client.post(
                "/api/v1/projects", json={"name": "Other sources"}, headers=stranger
            ).json()["id"]
            assert (
                client.put(
                    f"/api/v1/projects/{other_project}/context",
                    json={"source_version_ids": [versions[0]["id"]]},
                    headers={**stranger, "If-Match": "1"},
                ).status_code
                == 422
            )
            assert client.get(path, headers=stranger).status_code == 404
            assert (
                client.get(
                    f"{base}/{document['id']}/versions", headers=stranger
                ).status_code
                == 404
            )
    finally:
        app.dependency_overrides.pop(knowledge_service, None)
