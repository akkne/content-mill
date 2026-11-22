from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.domain.knowledge import DocumentStorageError, InvalidNodeOperation
from app.domain.project import ProjectNotFound
from app.presentation.http.dependencies import CurrentUser, KnowledgeServiceDependency

router = APIRouter(prefix="/api/v1/projects/{project_id}")


@router.get("/search")
def search(
    project_id: UUID,
    user: CurrentUser,
    service: KnowledgeServiceDependency,
    q: Annotated[str, Query(min_length=1, max_length=200)],
) -> dict:
    query = q.strip()
    if not query:
        raise HTTPException(status_code=422, detail="Введите запрос")
    try:
        matches = service.search_nodes(project_id, user.id, query)
    except ProjectNotFound as error:
        raise HTTPException(status_code=404, detail="Проект не найден") from error
    except DocumentStorageError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except InvalidNodeOperation as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"items": matches, "next_cursor": None}
