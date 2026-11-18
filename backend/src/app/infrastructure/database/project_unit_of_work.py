from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session

from app.infrastructure.database.knowledge_repository import (
    SqlAlchemyKnowledgeRepository,
)
from app.infrastructure.database.project_repository import SqlAlchemyProjectRepository
from app.infrastructure.database.session import session_factory


class SqlAlchemyProjectUnitOfWork:
    def __init__(self) -> None:
        self.session: Session | None = None
        self.repository: SqlAlchemyProjectRepository

    def __enter__(self) -> Self:
        self.session = session_factory()()
        self.knowledge = SqlAlchemyKnowledgeRepository(self.session)
        self.repository = SqlAlchemyProjectRepository(self.session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self.session is not None:
            self.session.rollback()
            self.session.close()

    def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("Unit of work is not active")
        self.session.commit()
