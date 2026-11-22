import os
import shutil
from functools import lru_cache
from pathlib import Path

import httpx

from app.application.agent_files import AgentFiles
from app.application.auth_service import AuthService
from app.application.avatars import AvatarLibrary
from app.application.knowledge_service import KnowledgeService
from app.application.project_service import ProjectService
from app.application.script_jobs import ScriptModel, ScriptWriter
from app.application.speech import SpeechService
from app.application.video_production import VideoProduction
from app.application.video_text import VideoTextGenerator
from app.application.videos import VideoService
from app.application.voice_library import VoiceLibrary
from app.infrastructure.asset_preview import AssetPreview
from app.infrastructure.astra_script import AstraCli
from app.infrastructure.claude_script import ClaudeCodeCli, ClaudeScript
from app.infrastructure.codex_script import CodexCli, CodexScript
from app.infrastructure.database.knowledge_unit_of_work import (
    SqlAlchemyKnowledgeUnitOfWork,
)
from app.infrastructure.database.project_unit_of_work import SqlAlchemyProjectUnitOfWork
from app.infrastructure.database.script_jobs import SqlScriptJobs
from app.infrastructure.database.speech import SqlSpeechRepository
from app.infrastructure.database.unit_of_work import SqlAlchemyAuthUnitOfWork
from app.infrastructure.database.voice_library import SqlVoiceLibrary
from app.infrastructure.lumean import LumeanElevenLabs
from app.infrastructure.polza_kling_26 import PolzaKling26
from app.infrastructure.polza_media import PolzaMedia
from app.infrastructure.polza_nano_banana import PolzaNanoBanana21
from app.infrastructure.security.passwords import Argon2Passwords
from app.infrastructure.security.tokens import SecureTokens
from app.infrastructure.starter_prompts import starter_prompts
from app.infrastructure.storage.s3_documents import S3DocumentStore
from app.infrastructure.video_edit import FFmpegEditor
from app.infrastructure.video_failures import describe_video_error

passwords = Argon2Passwords()
tokens = SecureTokens()


def auth_service() -> AuthService:
    return AuthService(SqlAlchemyAuthUnitOfWork, passwords, tokens)


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


def video_service() -> VideoService:
    models, selected = text_models()
    assembly_error = ""
    if not os.getenv("POLZA_API_KEY", "").strip():
        assembly_error = "Для сборки добавьте POLZA_API_KEY на сервере."
    elif AstraCli.model not in models:
        assembly_error = "Для монтажа подключите Codex на сервере."
    return VideoService(
        SqlAlchemyProjectUnitOfWork,
        VideoTextGenerator(models.get(selected), agent_files()),
        assembly_error,
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
    auth_file = os.getenv("CONTENT_MILL_CODEX_AUTH_FILE")
    if auth_file and AstraCli.model not in models and shutil.which("codex"):
        path = Path(auth_file)
        if path.is_file():
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
