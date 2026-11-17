from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.domain.auth import RefreshSession, User
from app.infrastructure.database.models import (
    AccessTokenModel,
    LoginAttemptModel,
    RefreshSessionModel,
    UserModel,
)


def as_user(model: UserModel) -> User:
    return User(model.id, model.email, model.display_name, model.password_hash)


class SqlAlchemyAuthRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def user_by_email(self, email: str) -> User | None:
        model = self.session.scalar(select(UserModel).where(UserModel.email == email))
        return as_user(model) if model else None

    def user_by_access(self, token_hash: str, now: datetime) -> User | None:
        model = self.session.scalar(
            select(UserModel)
            .join(RefreshSessionModel, RefreshSessionModel.user_id == UserModel.id)
            .join(
                AccessTokenModel, AccessTokenModel.session_id == RefreshSessionModel.id
            )
            .where(
                AccessTokenModel.token_hash == token_hash,
                AccessTokenModel.expires_at > now,
                RefreshSessionModel.revoked_at.is_(None),
                RefreshSessionModel.expires_at > now,
            )
        )
        return as_user(model) if model else None

    def save_user(self, email: str, display_name: str, password_hash: str) -> User:
        model = self.session.scalar(select(UserModel).where(UserModel.email == email))
        if model is None:
            model = UserModel(
                email=email, display_name=display_name, password_hash=password_hash
            )
            self.session.add(model)
        else:
            model.display_name = display_name
            model.password_hash = password_hash
        self.session.flush()
        return as_user(model)

    def revoke_user_sessions(self, user_id: UUID, now: datetime) -> None:
        self.session.execute(
            update(RefreshSessionModel)
            .where(
                RefreshSessionModel.user_id == user_id,
                RefreshSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )

    def clear_old_attempts(self, since: datetime) -> None:
        self.session.execute(
            delete(LoginAttemptModel).where(LoginAttemptModel.attempted_at < since)
        )

    def count_attempts(self, key: str, since: datetime) -> int:
        return (
            self.session.scalar(
                select(func.count())
                .select_from(LoginAttemptModel)
                .where(
                    LoginAttemptModel.attempt_key == key,
                    LoginAttemptModel.attempted_at >= since,
                )
            )
            or 0
        )

    def record_attempt(self, key: str, now: datetime) -> None:
        self.session.add(LoginAttemptModel(attempt_key=key, attempted_at=now))

    def clear_attempts(self, key: str) -> None:
        self.session.execute(
            delete(LoginAttemptModel).where(LoginAttemptModel.attempt_key == key)
        )

    def session_by_refresh(self, token_hash: str) -> RefreshSession | None:
        model = self.session.scalar(
            select(RefreshSessionModel)
            .where(RefreshSessionModel.refresh_hash == token_hash)
            .with_for_update()
        )
        if model is None:
            return None
        return RefreshSession(
            model.id,
            model.user_id,
            model.family_id,
            model.expires_at,
            model.revoked_at,
            model.rotated_at,
        )

    def save_session(
        self,
        session_id: UUID,
        user_id: UUID,
        family_id: UUID,
        refresh_hash: str,
        refresh_expires_at: datetime,
        access_hash: str,
        access_expires_at: datetime,
    ) -> None:
        self.session.add(
            RefreshSessionModel(
                id=session_id,
                user_id=user_id,
                family_id=family_id,
                refresh_hash=refresh_hash,
                expires_at=refresh_expires_at,
            )
        )
        self.session.flush()
        self.session.add(
            AccessTokenModel(
                token_hash=access_hash,
                session_id=session_id,
                expires_at=access_expires_at,
            )
        )

    def rotate_session(self, session_id: UUID, now: datetime) -> None:
        self.session.execute(
            update(RefreshSessionModel)
            .where(RefreshSessionModel.id == session_id)
            .values(revoked_at=now, rotated_at=now)
        )

    def revoke_family(self, family_id: UUID, now: datetime) -> None:
        self.session.execute(
            update(RefreshSessionModel)
            .where(
                RefreshSessionModel.family_id == family_id,
                RefreshSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
