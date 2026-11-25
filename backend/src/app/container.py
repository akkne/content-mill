import os
import shutil
from functools import lru_cache
from pathlib import Path
from uuid import UUID

import httpx

from app.application.agents.files import AgentFiles
from app.application.auth.service import AuthService
from app.application.avatars.library import AvatarLibrary
from app.application.knowledge.service import KnowledgeService
from app.application.projects.admin import ClientAdministration
from app.application.projects.service import ProjectService
from app.application.scripts.jobs import ScriptModel, ScriptWriter
from app.application.videos.production import VideoProduction
from app.application.videos.service import VideoService
from app.application.videos.text import VideoTextGenerator
from app.application.voices.library import VoiceLibrary
from app.application.voices.speech import SpeechService
from app.domain.video import FACTS_STYLE, STORY_STYLE
from app.infrastructure.database.repositories.script_jobs import SqlScriptJobs
from app.infrastructure.database.repositories.speech import SqlSpeechRepository
from app.infrastructure.database.repositories.voice_library import SqlVoiceLibrary
from app.infrastructure.database.transactions.auth import SqlAlchemyAuthUnitOfWork
from app.infrastructure.database.transactions.knowledge import (
    SqlAlchemyKnowledgeUnitOfWork,
)
from app.infrastructure.database.transactions.projects import (
    SqlAlchemyProjectUnitOfWork,
)
from app.infrastructure.providers.media.heygen_avatar6 import HeyGenAvatar6
from app.infrastructure.providers.media.polza_kling_26 import PolzaKling26
from app.infrastructure.providers.media.polza_media import PolzaMedia
from app.infrastructure.providers.media.polza_nano_banana import PolzaNanoBanana21
from app.infrastructure.providers.speech.lumean import LumeanElevenLabs
from app.infrastructure.providers.text.astra_script import AstraCli
from app.infrastructure.providers.text.claude_script import ClaudeCodeCli, ClaudeScript
from app.infrastructure.providers.text.codex_script import CodexCli, CodexScript
from app.infrastructure.providers.text.sol_script import SolCli
from app.infrastructure.security.passwords import Argon2Passwords
from app.infrastructure.security.tokens import SecureTokens
from app.infrastructure.starter_prompts import starter_prompts
from app.infrastructure.storage.s3_documents import S3DocumentStore
from app.infrastructure.video.asset_preview import AssetPreview
from app.infrastructure.video.openmotion import OpenMotion
from app.infrastructure.video.reel_media import ReelMediaEditor
from app.infrastructure.video.video_edit import FFmpegEditor
from app.infrastructure.video.video_failures import describe_video_error

passwords = Argon2Passwords()
tokens = SecureTokens()


def auth_service() -> AuthService:
    return AuthService(SqlAlchemyAuthUnitOfWork, passwords, tokens)


def client_administration() -> ClientAdministration:
    return ClientAdministration(SqlAlchemyProjectUnitOfWork)


def project_service() -> ProjectService:
    return ProjectService(
        SqlAlchemyProjectUnitOfWork, starter_prompts(), S3DocumentStore()
    )


def knowledge_service() -> KnowledgeService:
    return KnowledgeService(SqlAlchemyKnowledgeUnitOfWork, S3DocumentStore())


@lru_cache(maxsize=1)
def voice_catalog() -> LumeanElevenLabs:
    return LumeanElevenLabs(
        os.getenv("LUMEAN_API_KEY", "").strip(), httpx.Client(timeout=8)
    )


def voice_library() -> VoiceLibrary:
    return VoiceLibrary(SqlVoiceLibrary(), voice_catalog())


def read_style_guide(project: UUID, style: str) -> bytes | None:
    folder = os.getenv("CONTENT_MILL_STYLE_GUIDES")
    name = {FACTS_STYLE: "facts.jpg", STORY_STYLE: "story.jpg"}.get(style)
    if folder and name:
        path = Path(folder) / str(project) / name
        if path.is_file():
            return path.read_bytes()
    return None


def video_service() -> VideoService:
    models, selected = text_models()
    assembly_error = ""
    if not os.getenv("POLZA_API_KEY", "").strip():
        assembly_error = "Для сборки добавьте POLZA_API_KEY на сервере."
    elif AstraCli.model not in models:
        assembly_error = "Для монтажа подключите Codex на сервере."
    return VideoService(
        SqlAlchemyProjectUnitOfWork,
        VideoTextGenerator(models.get(selected), agent_files(), read_style_guide),
        assembly_error,
        lipsync_available=bool(
            os.getenv("HEYGEN_API_KEY", "").strip()
            and os.getenv("LUMEAN_API_KEY", "").strip()
        ),
    )


def video_production() -> VideoProduction:
    models, _ = text_models()
    api = PolzaMedia(os.getenv("POLZA_API_KEY", "").strip())
    return VideoProduction(
        SqlAlchemyProjectUnitOfWork,
        S3DocumentStore(),
        models.get(AstraCli.model),
        PolzaNanoBanana21(api),
        PolzaKling26(api),
        FFmpegEditor(),
        AssetPreview(),
        voice_catalog() if os.getenv("LUMEAN_API_KEY", "").strip() else None,
        reel_media=ReelMediaEditor(),
        motion=OpenMotion(os.environ.get("OPENMOTION_URL", "http://localhost:4173")),
        style_guide=read_style_guide,
        lipsync=HeyGenAvatar6(os.getenv("HEYGEN_API_KEY", "").strip()),
        describe_error=describe_video_error,
    )


def avatar_library() -> AvatarLibrary:
    return AvatarLibrary(SqlAlchemyProjectUnitOfWork, S3DocumentStore())


def agent_files() -> AgentFiles:
    return AgentFiles(SqlAlchemyProjectUnitOfWork, S3DocumentStore(), AssetPreview())


def speech_service() -> SpeechService:
    return SpeechService(SqlSpeechRepository(), voice_catalog())


def text_models() -> tuple[dict[str, ScriptModel], str]:
    models: dict[str, ScriptModel] = {}
    providers = {
        "claude": (ClaudeScript, ClaudeCodeCli, "ANTHROPIC_API_KEY"),
        "codex": (CodexScript, AstraCli, "OPENAI_API_KEY"),
    }
    provider = os.getenv("CONTENT_MILL_SCRIPT_PROVIDER", "codex").strip().lower()
    if provider and provider not in providers:
        raise ValueError("CONTENT_MILL_SCRIPT_PROVIDER must be codex, claude or empty")
    api_models = []
    for name, (api, cli, variable) in providers.items():
        key = os.getenv(variable, "").strip()
        if key:
            models[api.model] = api(key)
            api_models.append(api.model)
            if shutil.which(name):
                models[cli.model] = cli(key)
                if name == "codex":
                    models[CodexCli.model] = CodexCli(key)
                    models[SolCli.model] = SolCli(key)
    auth_file = os.getenv("CONTENT_MILL_CODEX_AUTH_FILE")
    if auth_file and AstraCli.model not in models and shutil.which("codex"):
        path = Path(auth_file)
        if path.is_file():
            models[SolCli.model] = SolCli(auth_file=path)
            models[AstraCli.model] = AstraCli(auth_file=path)
    if provider:
        selected = providers[provider][1].model
    else:
        selected = os.getenv("CONTENT_MILL_SCRIPT_MODEL", "").strip() or next(
            iter(api_models), ""
        )
    return models, selected


def script_writer() -> ScriptWriter:
    models, selected = text_models()
    return ScriptWriter(
        SqlAlchemyProjectUnitOfWork, agent_files(), SqlScriptJobs(), models, selected
    )
