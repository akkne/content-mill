from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update

from app.application.agent_ports import AgentScope
from app.application.script_jobs import BusyProject, ScriptJob
from app.domain.project import ProjectNotFound
from app.infrastructure.database.models import ProjectModel
from app.infrastructure.database.models import ScriptJobModel as Job
from app.infrastructure.database.session import session_factory


def as_job(row: Job) -> ScriptJob:
    return ScriptJob(
        row.id,
        AgentScope(row.project_id, row.owner_id),
        row.brief,
        row.model,
        row.status,
        row.run_at,
        row.result,
    )


class SqlScriptJobs:
    def submit(
        self, scope: AgentScope, brief: str, model: str, when: datetime
    ) -> ScriptJob:
        with session_factory().begin() as session:
            project = session.scalar(
                select(ProjectModel.id)
                .where(
                    ProjectModel.id == scope.project_id,
                    ProjectModel.owner_id == scope.owner_id,
                )
                .with_for_update()
            )
            if project is None:
                raise ProjectNotFound
            active = session.scalar(
                select(Job.id)
                .where(Job.project_id == project, Job.status.in_(["queued", "running"]))
                .limit(1)
            )
            if active:
                raise BusyProject
            row = Job(
                project_id=project,
                owner_id=scope.owner_id,
                brief=brief,
                model=model,
                run_at=when,
                status="queued",
            )
            session.add(row)
            session.flush()
            return as_job(row)

    def history(self, scope: AgentScope) -> list[ScriptJob]:
        with session_factory()() as session:
            if (
                session.scalar(
                    select(ProjectModel.id).where(
                        ProjectModel.id == scope.project_id,
                        ProjectModel.owner_id == scope.owner_id,
                    )
                )
                is None
            ):
                raise ProjectNotFound
            rows = session.scalars(
                select(Job)
                .where(
                    Job.project_id == scope.project_id, Job.owner_id == scope.owner_id
                )
                .order_by(Job.created_at.desc())
                .limit(20)
            )
            return [as_job(row) for row in rows]

    def cancel(self, scope: AgentScope, job: UUID) -> bool:
        with session_factory().begin() as session:
            cancelled = session.scalar(
                update(Job)
                .where(
                    Job.id == job,
                    Job.project_id == scope.project_id,
                    Job.owner_id == scope.owner_id,
                    Job.status == "queued",
                )
                .values(status="cancelled")
                .returning(Job.id)
            )
            return cancelled is not None

    def claim(self) -> ScriptJob | None:
        now = datetime.now(UTC)
        with session_factory().begin() as session:
            session.execute(
                update(Job)
                .where(
                    Job.status == "running",
                    Job.started_at < now - timedelta(minutes=15),
                )
                .values(
                    status="failed",
                    result="Выполнение прервано. Можно запустить сценарий снова.",
                )
            )
            row = session.scalar(
                select(Job)
                .where(Job.status == "queued", Job.run_at <= now)
                .order_by(Job.run_at, Job.id)
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            if row is None:
                return None
            row.status = "running"
            row.started_at = now
            return as_job(row)

    def finish(self, job: UUID, status: str, result: str) -> None:
        with session_factory().begin() as session:
            session.execute(
                update(Job)
                .where(Job.id == job, Job.status == "running")
                .values(status=status, result=result)
            )
