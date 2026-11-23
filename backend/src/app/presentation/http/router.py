from fastapi import APIRouter

from app.presentation.http.routers.admin import router as admin_router
from app.presentation.http.routers.agent_tokens import router as agent_tokens_router
from app.presentation.http.routers.auth import router as auth_router
from app.presentation.http.routers.avatars import router as avatars_router
from app.presentation.http.routers.knowledge import router as knowledge_router
from app.presentation.http.routers.media import router as media_router
from app.presentation.http.routers.projects import router as projects_router
from app.presentation.http.routers.script_jobs import router as script_jobs_router
from app.presentation.http.routers.search import router as search_router
from app.presentation.http.routers.videos import router as videos_router
from app.presentation.http.routers.voices import router as voices_router

router = APIRouter()
router.include_router(admin_router)
router.include_router(script_jobs_router)
router.include_router(agent_tokens_router)
router.include_router(videos_router)
router.include_router(media_router)
router.include_router(avatars_router)
router.include_router(voices_router)
router.include_router(auth_router)
router.include_router(projects_router)
router.include_router(knowledge_router)
router.include_router(search_router)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
