import os
from functools import lru_cache

import httpx

from app.application.agent_files import AgentFiles
from app.application.auth_service import AuthService
from app.application.knowledge_service import KnowledgeService
from app.application.project_service import ProjectService
from app.application.speech import SpeechService
from app.application.videos import VideoService
from app.application.voice_library import VoiceLibrary
from app.infrastructure.asset_preview import AssetPreview
from app.infrastructure.database.knowledge_unit_of_work import (
    SqlAlchemyKnowledgeUnitOfWork,
)
from app.infrastructure.database.project_unit_of_work import SqlAlchemyProjectUnitOfWork
from app.infrastructure.database.speech import SqlSpeechRepository
from app.infrastructure.database.unit_of_work import SqlAlchemyAuthUnitOfWork
from app.infrastructure.database.voice_library import SqlVoiceLibrary
from app.infrastructure.lumean import LumeanElevenLabs
from app.infrastructure.mock_video_generator import MockVideoGenerator
from app.infrastructure.security.passwords import Argon2Passwords
from app.infrastructure.security.tokens import SecureTokens
from app.infrastructure.starter_prompts import starter_prompts
from app.infrastructure.storage.s3_documents import S3DocumentStore

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
    return VideoService(SqlAlchemyProjectUnitOfWork, MockVideoGenerator())


def agent_files() -> AgentFiles:
    return AgentFiles(SqlAlchemyProjectUnitOfWork, S3DocumentStore(), AssetPreview())


def speech_service() -> SpeechService:
    return SpeechService(SqlSpeechRepository(), voice_catalog())
