from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.domain.motion import REELS, STYLES
from app.presentation.http.dependencies import CurrentUser, KnowledgeServiceDependency

router = APIRouter(prefix="/api/v1")


@router.get("/motion/styles")
def styles(user: CurrentUser):
    return list(STYLES.values())


@router.get("/motion/reels")
def reel_formats(user: CurrentUser):
    return list(REELS.values())


@router.put("/projects/{project_id}/motion/styles/{style_id}")
def assign(
    project_id: UUID,
    style_id: str,
    user: CurrentUser,
    service: KnowledgeServiceDependency,
):
    style = REELS.get(style_id) or STYLES.get(style_id)
    if style is None:
        raise HTTPException(404)
    return service.save_motion_style(project_id, user.id, style)


@router.get("/projects/{project_id}/motion/styles")
def assigned(project_id: UUID, user: CurrentUser, service: KnowledgeServiceDependency):
    return [
        n.description.removeprefix("openmotion:")
        for n in service.list_nodes(project_id, user.id)
        if n.description and n.description.startswith("openmotion:")
    ]
