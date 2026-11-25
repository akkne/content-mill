from dataclasses import asdict
from textwrap import wrap
from typing import Annotated, Literal
from uuid import UUID
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.application.videos.service import VideoService
from app.container import video_service
from app.domain.motion import STYLES
from app.domain.video import Video
from app.presentation.http.dependencies import CurrentUser
from app.presentation.http.schemas.videos import VideoAction, VideoInput

router = APIRouter(prefix="/api/v1/projects/{project_id}/videos")
Service = Annotated[VideoService, Depends(video_service)]


@router.get("")
def list_videos(
    project_id: UUID,
    user: CurrentUser,
    service: Service,
    status: Literal[
        "all", "draft", "generating", "failed", "ready", "planned", "published"
    ] = "all",
    q: str = Query(default="", max_length=180),
) -> dict:
    workspace = service.workspace(user.id, project_id, status, q)
    return {
        "project": workspace["project"],
        "items": [
            {
                "id": v.id,
                "title": v.title,
                "status": v.status,
                "created_at": v.created_at,
                "platform": v.settings["platform"],
                "duration": v.settings["duration"],
            }
            for v in workspace["items"]
        ],
    }


@router.get("/options")
def options(project_id: UUID, user: CurrentUser, service: Service) -> dict:
    return service.options(user.id, project_id)


@router.post("", status_code=201)
def create(
    project_id: UUID, payload: VideoInput, user: CurrentUser, service: Service
) -> Video:
    defaults = {"duration", "editing_style"} - payload.model_fields_set
    settings = payload.model_dump(exclude={"title", "sources", "assemble"} | defaults)
    return service.create(
        user.id, project_id, payload.title, settings, payload.sources, payload.assemble
    )


@router.get("/{video_id}")
def detail(
    project_id: UUID, video_id: UUID, user: CurrentUser, service: Service
) -> dict:
    video = service.detail(user.id, project_id, video_id)
    progress = video.progress()
    journal = video.journal
    style = STYLES.get(video.settings.get("motion_template"))
    return {
        **asdict(video),
        "progress": progress,
        "journal": journal,
        "motion_title": {lang: style[lang]["title"] for lang in ("ru", "en")}
        if style
        else None,
    }


@router.post("/{video_id}/actions")
def change(
    project_id: UUID,
    video_id: UUID,
    payload: VideoAction,
    user: CurrentUser,
    service: Service,
) -> Video:
    return service.detail(user.id, project_id, video_id, payload.action, payload.value)


@router.get("/{video_id}/cover")
def cover(
    project_id: UUID, video_id: UUID, user: CurrentUser, service: Service
) -> Response:
    video = service.detail(user.id, project_id, video_id)
    lines = "".join(
        f'<tspan x="36" dy="42">{escape(line)}</tspan>'
        for line in wrap(video.title, 22)
    )
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 960">'
        '<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#1d3761"/>'
        '<stop offset="1" stop-color="#2455a2"/></linearGradient></defs>'
        '<rect width="540" height="960" fill="url(#bg)"/>'
        '<circle cx="490" cy="352" r="130" fill="none" stroke="#ffffff" stroke-opacity=".12" stroke-width="40"/>'
        f'<text y="430" fill="white" font-family="sans-serif" font-size="34">{lines}</text></svg>'
    )
    return Response(
        svg,
        media_type="image/svg+xml",
        headers={"Content-Disposition": 'attachment; filename="cover.svg"'},
    )
