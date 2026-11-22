import json
import os
from base64 import b64decode
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from app.application.knowledge.service import KnowledgeService
from app.container import auth_service, knowledge_service
from app.domain.knowledge import DocumentStorageError
from app.infrastructure.database.models import (
    AccessTokenModel,
    AvatarWorkspaceModel,
    DocumentVersionModel,
    KnowledgeNodeModel,
    ProjectAgentTokenModel,
    ProjectContextModel,
    ProjectModel,
    RefreshSessionModel,
    UserModel,
    VideoModel,
)
from app.infrastructure.database.session import session_factory
from app.infrastructure.database.transactions.knowledge import (
    SqlAlchemyKnowledgeUnitOfWork,
)
from app.infrastructure.examples.library import example_entries
from app.infrastructure.storage.s3_documents import S3DocumentStore
from app.main import app
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import delete, select, update


@pytest.fixture(scope="session")
def migrated_database():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required")
    config = Config(str(Path(__file__).parents[1] / "src" / "alembic.ini"))
    command.upgrade(config, "head")


@pytest.fixture
def login(migrated_database, monkeypatch):
    objects = {}
    monkeypatch.setattr(
        S3DocumentStore,
        "put",
        lambda self, key, body, mime: objects.update({key: body}),
    )
    monkeypatch.setattr(S3DocumentStore, "get", lambda self, key: objects[key])
    monkeypatch.setattr(
        S3DocumentStore, "delete", lambda self, key: objects.pop(key, None)
    )
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
                delete(AvatarWorkspaceModel).where(
                    AvatarWorkspaceModel.owner_id == user_id
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

        changes = {"products": [], "description": "Updated"}
        patched = client.patch(path, json=changes, headers={**owner, "If-Match": "2"})
        assert patched.status_code == 200
        assert patched.json() == {**saved.json(), **changes, "revision": 3}
        assert client.patch(path, json=changes, headers=headers).status_code == 409

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


@pytest.fixture
def video_model(monkeypatch):
    class Model:
        def generate(self, instructions, text, images):
            data = json.loads(text)
            return json.dumps(
                {
                    "script": data["title"]
                    + " ".join(m.get("text", "") for m in data["materials"]),
                    "caption": "Подпись к ролику",
                    "edit_plan": ["0–3 с: общий план"],
                }
            )

    monkeypatch.setattr(
        "app.container.text_models",
        lambda: ({"fake": Model(), "codex:gpt-6.2-astra": Model()}, "fake"),
    )


def test_text_document_versions_and_access(login, video_model, monkeypatch):
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
    from app.container import agent_files

    files = agent_files()
    files.store = store
    monkeypatch.setattr("app.container.agent_files", lambda: files)
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
            original_text = (
                "Первый вариант озвучивания" + " " * 220 + "обязательный финал"
            )
            first = client.put(
                path,
                json={"content": original_text, "format": "markdown"},
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
                == original_text
            )
            assert client.get(path, headers=owner).json()["content"] == "Second"
            assert [
                item["id"]
                for item in client.get(
                    f"/api/v1/projects/{project_id}/search?q=Second", headers=owner
                ).json()["items"]
            ] == [document["id"]]
            assert (
                client.get(
                    f"/api/v1/projects/{project_id}/search?q=Первый вариант озвучивания",
                    headers=owner,
                ).json()["items"]
                == []
            )
            assert (
                client.get(
                    f"/api/v1/projects/{project_id}/search?q=%25", headers=owner
                ).json()["items"]
                == []
            )
            assert [
                item["id"]
                for item in client.get(
                    f"/api/v1/projects/{project_id}/search?q=Voice", headers=owner
                ).json()["items"]
            ] == [document["id"]]
            versions = client.get(
                f"{base}/{document['id']}/versions", headers=owner
            ).json()["items"]
            assert [item["version"] for item in versions] == [2, 1]
            assert "storage_key" not in versions[0]
            assert len(store.objects) == 2
            with session_factory()() as session:
                session.execute(
                    update(DocumentVersionModel)
                    .where(DocumentVersionModel.id == versions[0]["id"])
                    .values(search_text=None)
                )
                session.commit()
            assert [
                item["id"]
                for item in client.get(
                    f"/api/v1/projects/{project_id}/search?q=Second", headers=owner
                ).json()["items"]
            ] == [document["id"]]
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
            video_path = f"/api/v1/projects/{project_id}/videos"
            choices = client.get(video_path + "/options", headers=owner).json()[
                "sources"
            ]
            assert [s["id"] for s in choices if s["selected"]] == [versions[0]["id"]]
            payload = {"title": "Из базы знаний", "sources": [versions[1]["id"]]}
            draft = client.post(video_path, headers=owner, json=payload)
            assert draft.status_code == 201
            assert "обязательный финал" in draft.json()["script"]
            assert draft.json()["settings"]["sources"][0]["version"] == 1
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
                    f"/api/v1/projects/{project_id}/search?q=Voice", headers=stranger
                ).status_code
                == 404
            )
            assert (
                client.get(
                    f"{base}/{document['id']}/versions", headers=stranger
                ).status_code
                == 404
            )
            assert (
                client.delete(
                    f"{base}/{document['id']}", headers={**owner, "If-Match": "3"}
                ).status_code
                == 204
            )
            assert (
                client.get(
                    f"/api/v1/projects/{project_id}/search?q=Voice", headers=owner
                ).json()["items"]
                == []
            )
    finally:
        app.dependency_overrides.pop(knowledge_service, None)


def test_media_upload_version_visibility_and_voice(login):

    class Store:
        def __init__(self):
            self.objects = {}

        def upload_url(self, key, mime, size):
            return key

        def read_upload(self, key, size):
            return self.objects[key][: size + 1]

        def put(self, key, content, mime):
            self.objects[key] = content

        def delete(self, key):
            self.objects.pop(key, None)

        def download_url(self, key):
            return key

    store = Store()
    service = KnowledgeService(SqlAlchemyKnowledgeUnitOfWork, store)
    app.dependency_overrides[knowledge_service] = lambda: service
    try:
        owner, stranger = login(), login()
        with TestClient(app) as client:
            project = client.post(
                "/api/v1/projects", json={"name": "Media"}, headers=owner
            ).json()["id"]
            base = f"/api/v1/projects/{project}"
            data = (
                Path(__file__).parents[2]
                / "frontend-mvp/assets/knowledge/sample-audio.m4a"
            ).read_bytes()
            payload = {
                "name": "voice.m4a",
                "mime_type": "audio/mp4",
                "size_bytes": len(data),
                "sha256": sha256(data).hexdigest(),
            }

            def start(headers, **changes):
                return client.post(
                    f"{base}/files/uploads", json=payload | changes, headers=headers
                )

            def complete(upload, headers):
                return client.post(
                    f"{base}/files/uploads/{upload['upload_id']}/complete",
                    headers=headers,
                )

            assert start(stranger).status_code == 404
            upload = start(owner).json()
            store.objects[upload["upload_url"]] = b"wrong"
            assert complete(upload, owner).status_code == 422
            assert not any(
                n["name"] == "voice.m4a"
                for n in client.get(f"{base}/nodes/tree", headers=owner).json()["items"]
            )
            store.objects[upload["upload_url"]] = data
            assert complete(upload, stranger).status_code == 404
            saved = complete(upload, owner).json()
            assert complete(upload, owner).json() == saved
            node = saved["node"]
            path = f"{base}/nodes/{node['id']}"
            assert node["kind"] == "audio"
            assert client.get(path + "/download", headers=stranger).status_code == 404
            assert client.get(path + "/content", headers=owner).status_code == 404
            assert start(owner, node_id=node["id"]).status_code == 428
            headers = owner | {"If-Match": str(node["revision"])}
            second = start(headers, node_id=node["id"]).json()
            store.objects[second["upload_url"]] = data
            saved2 = complete(second, owner).json()
            assert saved2["version"]["version"] == 2
            assert start(headers, node_id=node["id"]).status_code == 409
            old = client.get(path + "/download?version=1", headers=owner).json()
            latest = client.get(path + "/download", headers=owner).json()
            assert latest["url"] != old["url"]
            assert store.objects[old["url"]] == data
            rev = saved2["node"]["revision"]
            retired = client.patch(
                path + "/voice",
                json={"name": "Анна", "language": "ru", "model": "example"},
                headers=owner | {"If-Match": str(rev)},
            )
            assert retired.status_code == 404
            assert (
                client.delete(path, headers=owner | {"If-Match": str(rev)}).status_code
                == 204
            )
            assert client.get(path + "/download", headers=owner).status_code == 404
    finally:
        app.dependency_overrides.pop(knowledge_service, None)


def test_project_creation_rolls_back_partial_prompt_set(login, monkeypatch):
    owner = login()
    stored = set()

    def fail_second_write(self, key, content, mime):
        stored.add(key)
        if len(stored) == 2:
            raise DocumentStorageError

    monkeypatch.setattr(S3DocumentStore, "put", fail_second_write)
    monkeypatch.setattr(
        S3DocumentStore, "delete", lambda self, key: stored.discard(key)
    )
    with TestClient(app, headers=owner) as client:
        response = client.post("/api/v1/projects", json={"name": "Проба"})
        assert response.status_code == 503
        assert not stored
        assert client.get("/api/v1/projects").json()["items"] == []


def test_starter_folders_and_reusable_voice(login, video_model):
    owner = login()
    with TestClient(app, headers=owner) as client:
        project = client.post("/api/v1/projects", json={"name": "Студия"}).json()
        base = f"/api/v1/projects/{project['id']}/nodes"
        tree = client.get(f"{base}/tree").json()["items"]
        documents = [
            n
            for n in tree
            if n["kind"] == "document" and n["name"] != "Описание аватара.md"
        ]
        assert len(documents) == 10
        for node in documents:
            saved = client.get(f"{base}/{node['id']}/content").json()
            assert saved["version"] == 1 and saved["content"].startswith("# ")
        by_name = {node["name"]: node for node in tree}

        def children(parent):
            return {n["name"] for n in tree if n["parent_id"] == by_name[parent]["id"]}

        assert children("Бренд") == {"Товары", "Формат", "Правила бренда"}
        assert not children("Голоса")
        assert "Описание аватара.md" in children("Основной аватар")
        assert not children("Товары")
        assert children("Материалы") == {"Аудио", "Видео", "Изображения"}
        assert children("Промпты") == {
            "Бриф и источники",
            "Сценарий и хуки",
            "Раскадровка",
            "Голос",
            "Аватар",
            "Медиаматериалы",
            "Анимации",
            "Монтаж и субтитры",
            "Рендер и проверка",
        }

        def folder(parent, name):
            return client.post(
                base, json={"parent_id": parent, "kind": "folder", "name": name}
            )

        assert folder(by_name["Голоса"]["id"], "Алиса").status_code == 422
        personal = client.post(
            "/api/v1/voices", json={"name": "Алиса", "voice_id": "voice-42"}
        ).json()
        voice = client.patch(
            f"/api/v1/voices/{personal['id']}/projects", json={"add": [project["id"]]}
        ).json()[0]
        videos = f"/api/v1/projects/{project['id']}/videos"
        assert client.get(videos + "/options").json()["voices"] == {
            personal["id"]: "Алиса"
        }
        assert (
            client.post(videos, json={"title": "Тест", "voice": "random"}).status_code
            == 422
        )
        recording = client.post(
            videos, json={"title": "Тест", "voice": personal["id"]}
        ).json()
        assert recording["settings"]["library_voice_id"] == personal["id"]
        profile = {
            "voice_gender": "female",
            "description": "Спокойный тембр",
            "voice_language": "русский",
            "voice_model": "eleven_multilingual_v2",
            "elevenlabs_voice_id": "voice-42",
        }
        saved = client.patch(f"/api/v1/voices/{personal['id']}", json=profile)
        assert saved.status_code == 200
        assert all(saved.json()[key] == value for key, value in profile.items())
        assert (
            client.get(f"{base}/{voice['id']}").json()["description"]
            == profile["description"]
        )
        avatar = folder(by_name["Аватары"]["id"], "Ведущая").json()
        sections = client.get(base, params={"parent_id": avatar["id"]}).json()["items"]
        assert {n["name"] for n in sections} == children("Основной аватар")
        wardrobe = next(n for n in sections if n["folder_role"] == "wardrobe")
        assert folder(wardrobe["id"], "Белая рубашка").status_code == 201
        assert folder(wardrobe["id"], "белая рубашка").status_code == 409
        avatar_url = f"{base}/{avatar['id']}/profile"
        data = {"linked_voice_id": voice["id"]}
        assert (
            client.put(avatar_url, json=data, headers={"If-Match": "1"}).json()[
                "linked_voice_id"
            ]
            == voice["id"]
        )
        assert (
            client.put(avatar_url, json=data, headers={"If-Match": "1"}).status_code
            == 409
        )
        other = client.post("/api/v1/projects", json={"name": "Другой"}).json()
        other_base = f"/api/v1/projects/{other['id']}/nodes"
        other_avatar = next(
            n
            for n in client.get(f"{other_base}/tree").json()["items"]
            if n["folder_role"] == "avatar"
        )
        assert (
            client.put(
                f"{other_base}/{other_avatar['id']}/profile",
                json=data,
                headers={"If-Match": "1"},
            ).status_code
            == 422
        )
        assert (
            client.delete(
                f"{base}/{voice['id']}", headers={"If-Match": "2"}
            ).status_code
            == 204
        )
        assert client.get(f"{base}/{avatar['id']}").json()["linked_voice_id"] is None


def test_voice_catalog_and_manual_import(login):
    import httpx
    from app.application.voices.library import VoiceLibrary
    from app.container import voice_catalog, voice_library
    from app.infrastructure.database.repositories.voice_library import SqlVoiceLibrary
    from app.infrastructure.providers.speech.elevenlabs import ElevenLabsCatalog

    calls = []

    def lookup(request):
        calls.append(request)
        assert request.headers["xi-api-key"] == "test"
        return httpx.Response(
            200,
            json={
                "voices": [
                    {
                        "voice_id": "one",
                        "name": "Anna",
                        "labels": {"gender": "female", "language": "ru"},
                        "preview_url": "https://example.test/demo.mp3",
                    }
                ],
                "has_more": not request.url.params.get("voice_ids"),
                "next_page_token": "page2",
            },
        )

    owner, stranger = login(), login()
    with (
        httpx.Client(transport=httpx.MockTransport(lookup)) as provider,
        TestClient(app, headers=owner) as client,
    ):
        catalog = ElevenLabsCatalog("test", provider)
        app.dependency_overrides[voice_catalog] = lambda: catalog
        app.dependency_overrides[voice_library] = lambda: VoiceLibrary(
            SqlVoiceLibrary(), catalog
        )
        try:
            project = client.post("/api/v1/projects", json={"name": "Каталог"}).json()
            path = "/api/v1/voices"
            assert client.get(path, headers=stranger).json() == []
            assert not calls
            params = {
                "query": "Anna",
                "language": "ru",
                "gender": "female",
                "cursor": "p",
            }
            page = client.get(path + "/catalog", params=params).json()
            assert page["next_cursor"] == "page2"
            assert page["items"][0]["languages"] == ["ru"]
            assert dict(calls[0].url.params) == {
                "page_size": "20",
                "include_total_count": "false",
                "search": "Anna",
                "language": "ru",
                "gender": "female",
                "next_page_token": "p",
            }
            assert client.get(path + "/catalog", params=params).json() == page
            assert len(calls) == 1
            data = {"name": "Анна", "voice_id": "one", "from_catalog": True}
            saved = client.post(path, json=data).json()
            assert saved["voice_gender"] == "female"
            assert saved["elevenlabs_voice_id"] == "one"
            assert saved["voice_preview_url"] == "https://example.test/demo.mp3"
            assert calls[-1].url.params["voice_ids"] == "one"
            assert client.get(path, headers=stranger).json() == []
            membership = f"{path}/{saved['id']}/projects"
            other = client.post("/api/v1/projects", json={"name": "Другой"}).json()[
                "id"
            ]
            foreign = client.post(
                "/api/v1/projects", headers=stranger, json={"name": "Чужой"}
            ).json()["id"]
            assert (
                client.patch(
                    membership, headers=stranger, json={"add": [project["id"]]}
                ).status_code
                == 404
            )
            assert (
                client.patch(membership, json={"add": [other, foreign]}).status_code
                == 404
            )
            assert client.get(path).json()[0]["project_ids"] == []
            ids = [project["id"], other]
            first = client.patch(membership, json={"add": ids}).json()
            assert len(first) == 2
            assert client.patch(membership, json={"add": ids}).json() == first
            assert set(client.get(path).json()[0]["project_ids"]) == set(ids)
            assert client.patch(membership, json={"remove": ids}).status_code == 200
            assert client.get(path).json()[0]["project_ids"] == []
            restored = client.patch(membership, json={"add": ids}).json()
            assert [n["id"] for n in restored] == [n["id"] for n in first]
            assert (
                client.post(path, json=data | {"voice_id": "missing"}).status_code
                == 404
            )
            app.dependency_overrides[voice_catalog] = lambda: ElevenLabsCatalog(
                "", provider
            )
            assert client.get(path + "/catalog").status_code == 503
            manual = client.post(
                path, json={"name": "Свой", "voice_id": "two", "gender": "male"}
            )
            assert manual.status_code == 201
            assert manual.json()["voice_gender"] == "male"
        finally:
            app.dependency_overrides.pop(voice_catalog)
            app.dependency_overrides.pop(voice_library)


def test_project_video_lifecycle(login, video_model, monkeypatch):
    from types import SimpleNamespace

    from app.application.videos.production import ProductionError
    from app.container import video_production

    # Drive each checkpoint explicitly, without external billing or sleeps.
    worker = video_production()
    monkeypatch.setattr(
        "app.lifespan.video_production", lambda: SimpleNamespace(run_next=lambda: False)
    )
    shot = {
        key: "test"
        for key in (
            "composition",
            "cast_and_wardrobe",
            "cut",
            "image_prompt",
            "video_prompt",
        )
    }
    shot["reference_ids"] = []
    shot["utterances"] = [
        {
            "speaker": "Анна",
            "delivery": "on_screen",
            "text": "Привет!",
            "start_ms": 500,
            "end_ms": 4000,
        }
    ]
    shot["video_prompt"] = "Анна говорит в кадре: Привет!"

    def storyboard(instructions, text, images, materials):
        data = json.loads(text)
        assert "prompt_guides" not in data and data["script"] == "Авторский сценарий"
        assert [m["origin"] for m in data["materials"]] == ["user"]
        assert [entry[0] for entry in materials] == [source_id]
        assert data["edit_notes"] == [] and data["speech_window_ms"] == [250, 7750]
        return json.dumps({"scenes": [shot, shot | {"continuity_scene": 1}]})

    def edit(instructions, text, images, clips, materials):
        assert len(images) == len(clips) == 2
        frames = json.loads(text)["first_frames"]
        source, *frame_inputs = list(materials)
        assert source[0] == source_id and source[1] == "markdown" and source[2]
        assert [f["name"] for f in frames] == ["scene-01.png", "scene-02.png"]
        assert frame_inputs == [
            (f["version_id"], "image/png", b"test frame") for f in frames
        ]
        return json.dumps(
            {"cuts": [{"scene": i, "start_ms": 0, "end_ms": 7500} for i in [1, 2]]}
        )

    class Clips:
        submitted = 0

        def submit(self, prompt, frame):
            self.submitted += 1
            return "saved-request"

        def collect(self, operation):
            assert operation == "saved-request"
            return b"test clip"

    worker.model = SimpleNamespace(generate_storyboard=storyboard, generate_edit=edit)
    worker.frames = SimpleNamespace(
        submit=lambda prompt, refs: "frame-id", collect=lambda op: b"test frame"
    )
    worker.preview = SimpleNamespace(render=lambda data, fmt: b"jpeg")
    worker.clips = Clips()
    worker.editor = SimpleNamespace(
        inspect=lambda data: (8000, "jpeg"), render=lambda *args: b"final"
    )

    owner, stranger = login(), login()
    with TestClient(app) as client:
        project = client.post(
            "/api/v1/projects", headers=owner, json={"name": "Студия"}
        ).json()["id"]
        base = f"/api/v1/projects/{project}/videos"
        assert client.get(base, headers=stranger).status_code == 404
        assert (
            client.post(
                base, headers=owner, json={"title": "Тест", "sources": [str(uuid4())]}
            ).status_code
            == 422
        )
        source_id = client.get(base + "/options", headers=owner).json()["sources"][0][
            "id"
        ]
        video = client.post(
            base,
            headers=owner,
            json={"title": "Тест сборки", "duration": 15, "sources": [source_id]},
        ).json()
        assert video["journal"] == ["0–3 с: общий план"]
        assert video["caption"] == "Подпись к ролику"
        path = f"{base}/{video['id']}"
        assert (
            client.get(
                base, params={"q": "сборки", "status": "draft"}, headers=owner
            ).json()["items"][0]["id"]
            == video["id"]
        )
        assert client.get(path, headers=stranger).status_code == 404

        def act(action, value=""):
            return client.post(
                path + "/actions",
                headers=owner,
                json={"action": action, "value": value},
            )

        assert (
            act("script", "Авторский сценарий").json()["script"] == "Авторский сценарий"
        )
        monkeypatch.delenv("POLZA_API_KEY", raising=False)
        assert act("assemble").status_code == 503
        monkeypatch.setenv("POLZA_API_KEY", "test")
        assert act("assemble").json()["status"] == "generating"
        assert act("assemble").status_code == 422
        assert worker.run_next()  # Copy the pinned document to the production folder.
        assert worker.run_next()

        def unavailable(prompt, refs):
            raise ProductionError("polza_balance")

        monkeypatch.setattr(worker.frames, "submit", unavailable)
        assert worker.run_next()
        assert client.get(path, headers=owner).json()["status"] == "failed"
        assert act("assemble").json()["status"] == "generating"
        monkeypatch.setattr(worker.frames, "submit", lambda prompt, refs: "frame-id")

        def make_stage_due():
            with session_factory().begin() as session:
                session.execute(
                    update(VideoModel)
                    .where(VideoModel.id == video["id"])
                    .values(ready_at=datetime.now(UTC))
                )

        assert worker.run_next()  # Provider accepted the first frame order.
        make_stage_due()

        def missing_asset(operation):
            assert operation == "frame-id"
            raise ValueError("Missing asset URL")

        with monkeypatch.context() as failure:
            failure.setattr(worker.frames, "collect", missing_asset)
            assert worker.run_next()
        stopped = client.get(path, headers=owner).json()["settings"]["production"]
        assert stopped["failure"] == {
            "stage": "collect_frame",
            "reason": "invalid_response",
        }
        resumed = act("assemble").json()["settings"]["production"]
        assert "failure" not in resumed
        assert (
            resumed["stage"] == "collect_frame" and resumed["operation"] == "frame-id"
        )
        for _ in range(8):
            make_stage_due()
            assert worker.run_next()

        def storage_outage(*args):
            raise DocumentStorageError("temporary outage")

        with monkeypatch.context() as failure:
            failure.setattr(worker.store, "put", storage_outage)
            assert worker.run_next()
        failed = client.get(path, headers=owner).json()
        assert failed["status"] == "failed"
        assert failed["settings"]["production"]["stage"] == "render"
        assert "final.mp4" not in failed["settings"]["production"]["files"]
        assert act("assemble").json()["status"] == "generating"
        assert worker.run_next()
        result = client.get(path, headers=owner).json()
        assert result["status"] == "ready"
        files = result["settings"]["production"]["files"]
        assert result["journal"] == ["0–7.5 · test", "7.5–15 · test"]
        assert len(files) == 10 and "final.mp4" in files
        request = json.loads(
            worker.read(UUID(project), files["edit-request.json"]["version"])[1]
        )
        assert request["input"]["clip_versions"] == [
            files[f"scene-{i:02}.mp4"]["version"] for i in (1, 2)
        ]
        assert worker.read(UUID(project), files["final.mp4"]["version"])[1] == b"final"
        assert worker.clips.submitted == 2
        assert act("schedule", "2000-01-01T00:00:00Z").status_code == 422
        assert act("publish").json()["status"] == "published"
        assert client.get(path, headers=owner).json()["settings"]["publication"]
        assert act("duplicate").json()["status"] == "draft"
        assert act("delete").status_code == 200
        assert client.get(path, headers=owner).status_code == 404


def test_project_mcp_tools_and_scope(login):
    owner, stranger = login(), login()
    with TestClient(app, base_url="http://localhost") as client:

        def create(headers):
            pid = client.post(
                "/api/v1/projects", headers=headers, json={"name": "Студия"}
            ).json()["id"]
            return f"/api/v1/projects/{pid}"

        project = create(owner)
        other = create(stranger)
        endpoint = project + "/mcp-token"

        def issue(path, headers):
            response = client.post(path + "/mcp-token", headers=headers)
            assert response.status_code == 201
            return {
                "Authorization": "Bearer " + response.json()["token"],
                "Accept": "application/json, text/event-stream",
            }

        token = issue(project, owner)

        def rpc(headers, method, params):
            return client.post(
                "/mcp",
                headers=headers,
                json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
            )

        def call(headers, name, **args):
            return rpc(headers, "tools/call", {"name": name, "arguments": args}).json()[
                "result"
            ]

        assert client.post(endpoint, headers=stranger).status_code == 404
        assert client.get("/api/v1/me", headers=token).status_code == 401
        assert rpc(owner, "tools/list", {}).status_code == 401
        assert (
            rpc(
                token,
                "initialize",
                {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1"},
                },
            ).status_code
            == 200
        )
        assert {
            item["name"]
            for item in rpc(token, "tools/list", {}).json()["result"]["tools"]
        } == {"find_assets", "read_document", "preview_asset"}
        reply = call(token, "find_assets", query="Промпты", limit=1)
        assert not reply["isError"], reply
        result = reply["structuredContent"]
        assert result["next_offset"] == 1
        asset = result["items"][0]
        assert asset["path"].startswith("Промпты/")
        vid = asset["version_id"]
        text = call(token, "read_document", version_id=vid, limit=8)[
            "structuredContent"
        ]
        assert len(text["text"]) == 8 and text["next_offset"] == 8
        assert call(issue(other, stranger), "read_document", version_id=vid)["isError"]
        project_id = UUID(project.rsplit("/", 1)[1])
        user_id = UUID(client.get("/api/v1/me", headers=owner).json()["id"])
        knowledge_service().import_examples(project_id, user_id, example_entries())
        for kind in ("image", "video"):
            row = call(token, "find_assets", kind=kind)["structuredContent"]["items"][0]
            block = call(token, "preview_asset", version_id=row["version_id"])[
                "content"
            ][0]
            assert block["type"] == "image" and block["mimeType"] == "image/jpeg"
            assert max(Image.open(BytesIO(b64decode(block["data"]))).size) <= 768
        replacement = issue(project, owner)
        assert rpc(token, "tools/list", {}).status_code == 401
        assert client.delete(endpoint, headers=owner).status_code == 204
        assert rpc(replacement, "tools/list", {}).status_code == 401
        expired = issue(project, owner)
        with session_factory()() as session:
            session.execute(
                update(ProjectAgentTokenModel)
                .where(ProjectAgentTokenModel.project_id == project_id)
                .values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
            )
            session.commit()
        assert rpc(expired, "tools/list", {}).status_code == 401


def test_lumean_speech_lifecycle(login):
    import httpx
    from app.application.voices.speech import SpeechService
    from app.container import speech_service
    from app.infrastructure.database.repositories.speech import SqlSpeechRepository
    from app.infrastructure.providers.speech.lumean import LumeanElevenLabs

    template, order, request = uuid4(), uuid4(), uuid4()
    calls = []

    def upstream(req):
        import json

        path = req.url.path.rsplit("/", 1)[-1]
        body = json.loads(req.content) if req.content else {}
        assert req.headers["X-API-KEY"] == "test"
        calls.append(path)
        if path == "templates":
            assert body["config"]["tts_settings"]["voice_id"] == "my-voice"
            data = {"id": str(template)}
        elif path == "orders":
            assert body["template_id"] == str(template) and body["name"] == str(request)
            data = {"id": str(order)}
        elif path == str(order):
            data = {"status": "completed", "result": {"files": ["final.mp3"]}}
        elif path == "url":
            assert body["path"] == "final.mp3"
            data = {"url": "https://example.test/final.mp3"}
        else:
            pytest.fail(path)
        return httpx.Response(200, json={"success": True, "data": data})

    owner, other = login(), login()
    with (
        httpx.Client(transport=httpx.MockTransport(upstream)) as provider,
        TestClient(app) as client,
    ):
        service = SpeechService(
            SqlSpeechRepository(), LumeanElevenLabs("test", provider)
        )
        app.dependency_overrides[speech_service] = lambda: service
        try:
            voice = client.post(
                "/api/v1/voices",
                headers=owner,
                json={"name": "Диктор", "voice_id": "my-voice"},
            ).json()["id"]
            path = f"/api/v1/voices/{voice}/speech"
            payload = {"text": "Привет", "request_id": str(request)}
            assert client.post(path, headers=other, json=payload).status_code == 404
            for _ in range(2):
                assert client.post(path, headers=owner, json=payload).status_code == 202
            assert (
                client.post(
                    path, headers=owner, json={**payload, "text": "Другой текст"}
                ).status_code
                == 409
            )
            assert client.get(path, headers=owner).json() == [str(request)]
            assert (
                client.get(path + "/" + str(request), headers=other).status_code == 404
            )
            assert client.get(path + "/" + str(request), headers=owner).json() == {
                "status": "completed",
                "url": "https://example.test/final.mp3",
            }
            assert calls == ["templates", "orders", str(order), "url"]
        finally:
            app.dependency_overrides.pop(speech_service)


@pytest.mark.parametrize("provider", ["codex", "claude"])
def test_managed_script_runs_without_mcp(login, monkeypatch, provider):
    import httpx
    from app.container import script_writer
    from app.infrastructure.database.models import ScriptJobModel

    owner, stranger = login(), login()
    key = "OPENAI_API_KEY" if provider == "codex" else "ANTHROPIC_API_KEY"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("CONTENT_MILL_SCRIPT_MODEL", raising=False)
    monkeypatch.setenv("CONTENT_MILL_SCRIPT_PROVIDER", "")
    calls = []
    foreign_version = uuid4()

    def respond(url, *, headers, json, timeout):
        calls.append(json)
        if len(calls) == 1:
            import json as codec

            message = json.get("input", json.get("messages"))[0]["content"][0]["text"]
            catalog = codec.loads(message)["catalog"]
            output = codec.dumps(
                {
                    "query": "",
                    "versions": [str(foreign_version), str(catalog[0]["version_id"])],
                }
            )
        else:
            output = "Готовый сценарий тестового ролика"
            assert "materials" in str(json) and str(foreign_version) not in str(json)
            assert "version_id" in str(json)
        if provider == "codex":
            assert url == "https://api.openai.com/v1/responses"
            body = {
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": output}],
                    }
                ],
            }
        else:
            assert url == "https://api.anthropic.com/v1/messages"
            body = {
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": output}],
            }
        return httpx.Response(200, json=body, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", respond)
    client = TestClient(app)
    project = client.post(
        "/api/v1/projects", headers=owner, json={"name": "Сценарии"}
    ).json()["id"]
    path = f"/api/v1/projects/{project}/scripts"
    brief = {"brief": "Покажи преимущества продукта"}
    assert client.post(path, headers=owner, json=brief).status_code == 503
    monkeypatch.setenv(key, "test-only")
    assert client.post(path, headers=stranger, json=brief).status_code == 404
    assert client.get(path, headers=stranger).status_code == 404
    later = datetime.now(UTC) + timedelta(hours=1)
    scheduled = client.post(
        path, headers=owner, json={**brief, "run_at": later.isoformat()}
    )
    assert scheduled.status_code == 202
    assert not script_writer().run_next()
    assert (
        client.delete(path + "/" + scheduled.json()["id"], headers=owner).status_code
        == 204
    )
    queued = client.post(path, headers=owner, json=brief)
    assert queued.status_code == 202
    assert client.post(path, headers=owner, json=brief).status_code == 409
    assert script_writer().run_next()
    job = client.get(path, headers=owner).json()["items"][0]
    assert (
        job["status"] == "done" and job["result"] == "Готовый сценарий тестового ролика"
    )
    assert len(calls) == 2
    assert not script_writer().run_next()
    with session_factory()() as session:
        assert session.get(ScriptJobModel, UUID(job["id"])).model == job["model"]
        assert session.get(ProjectAgentTokenModel, UUID(project)) is None


@pytest.mark.parametrize("missing_folders", [False, True])
def test_avatar_library_project_snapshot_and_voice(login, video_model, missing_folders):
    owner, other = login(), login()
    with TestClient(app, headers=owner) as client:
        personal = client.post("/api/v1/avatars/workspace").json()["project_id"]
        assert client.get("/api/v1/projects").json()["items"] == []
        project = client.post("/api/v1/projects", json={"name": "Shoot"}).json()["id"]
        if missing_folders:
            destination = f"/api/v1/projects/{project}/nodes"
            for folder in client.get(destination + "/tree").json()["items"]:
                if folder["folder_role"] in {"avatars", "voices"}:
                    client.delete(
                        f"{destination}/{folder['id']}",
                        headers={"If-Match": str(folder["revision"])},
                    ).raise_for_status()
        base = f"/api/v1/projects/{personal}/nodes"
        root = next(
            n
            for n in client.get(base + "/tree").json()["items"]
            if n["folder_role"] == "avatars"
        )
        avatar = client.post(
            base, json={"parent_id": root["id"], "name": "Анна", "kind": "folder"}
        ).json()
        doc = next(
            n
            for n in client.get(base + "/tree").json()["items"]
            if n["kind"] == "document"
        )
        assert client.put(
            f"{base}/{doc['id']}/content",
            headers={"If-Match": "1"},
            json={"content": "Портрет Анны", "format": "markdown"},
        ).is_success
        voice = client.post(
            "/api/v1/voices",
            json={
                "name": "Voice A",
                "voice_id": "external-a",
                "model": "eleven_multilingual_v2",
            },
        ).json()
        linked = client.patch(
            f"/api/v1/voices/{voice['id']}/projects", json={"add": [personal]}
        ).json()[0]
        client.put(
            f"{base}/{avatar['id']}/profile",
            headers={"If-Match": "1"},
            json={"linked_voice_id": linked["id"]},
        ).raise_for_status()
        assign = f"/api/v1/avatars/{avatar['id']}/projects/{project}"
        assert client.post(assign, headers=other).status_code == 404
        assigned = client.post(assign).json()["node_id"]
        assert client.post(assign).json()["node_id"] == assigned
        assert client.post("/api/v1/avatars/workspace").json()["assignments"] == {
            avatar["id"]: [project]
        }
        videos = f"/api/v1/projects/{project}/videos"
        options = client.get(videos + "/options").json()
        character = next(a for a in options["avatars"] if a["id"] == assigned)
        assert character["default_voice_id"] == options["cast_voices"][0]["id"]
        assert client.get("/api/v1/voices").json()[0]["project_ids"] == [project]
        body = {
            "title": "Бриф",
            "characters": [
                {"character_id": assigned, "voice_id": character["default_voice_id"]}
            ],
        }
        result = client.post(videos, json=body)
        result.raise_for_status()
        settings = result.json()["settings"]
        cast = settings["characters"][0]
        assert (
            cast["display_name"] == "Анна"
            and cast["voice"]["elevenlabs_voice_id"] == "external-a"
        )
        assert cast["files"] == settings["sources"] == []
        # Upload after assignment, with no media in the project snapshot.
        from contextlib import ExitStack

        from app.application.knowledge.seed_documents import create_entry
        from app.application.videos.cast import avatar_references
        from app.container import video_production
        from app.domain.knowledge import ExampleEntry

        worker = video_production()
        with worker.work() as work, ExitStack() as cleanup:
            tree = work.knowledge.list(UUID(personal))
            for folder_name in ("Лицо крупным планом", "Разрешения"):
                folder = next(
                    n
                    for n in tree
                    if n.parent_id == UUID(avatar["id"]) and n.name == folder_name
                )
                create_entry(
                    UUID(personal),
                    folder.id,
                    ExampleEntry(
                        "photo", None, "photo.jpg", "image", b"photo", "image/jpeg"
                    ),
                    work.knowledge,
                    worker.store,
                    cleanup,
                )
            work.commit()
            cleanup.pop_all()
        with worker.work() as work:
            refs = avatar_references(work, UUID(project), [cast])
        assert [(r["role"], r["workspace"], r["character_id"]) for r in refs] == [
            ("face_reference", personal, assigned)
        ]
        assert worker.read(UUID(personal), refs[0]["id"]) == ("image/jpeg", b"photo")
        assert (
            client.post(
                videos,
                json={"title": "Other", "characters": [{"character_id": avatar["id"]}]},
            ).status_code
            == 422
        )
        client.post(
            videos + "/" + result.json()["id"] + "/actions", json={"action": "delete"}
        ).raise_for_status()
