import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.application.auth.ports import (
    AuthRepository,
    AuthUnitOfWorkFactory,
    PasswordPort,
    TokenPort,
)
from app.domain.auth import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidSession,
    TokenPair,
    TooManyAttempts,
    User,
)

ACCESS_LIFETIME = timedelta(minutes=15)
REFRESH_LIFETIME = timedelta(days=14)
ATTEMPT_WINDOW = timedelta(minutes=15)


class AuthService:
    def __init__(
        self,
        unit_of_work: AuthUnitOfWorkFactory,
        passwords: PasswordPort,
        tokens: TokenPort,
    ) -> None:
        self.unit_of_work = unit_of_work
        self.passwords = passwords
        self.tokens = tokens

    def issue_owner_setup(self, owner_id: UUID) -> str:
        token = secrets.token_urlsafe(32)
        with self.unit_of_work() as work:
            work.repository.store_owner_setup(
                owner_id,
                self.tokens.hash(token),
                datetime.now(UTC) + timedelta(minutes=60),
            )
            work.commit()
        return token

    def complete_owner_setup(
        self, owner_id: UUID, token: str, email: str, password: str
    ) -> TokenPair:
        now = datetime.now(UTC)
        with self.unit_of_work() as work:
            repo = work.repository
            if not repo.consume_owner_setup(owner_id, self.tokens.hash(token), now):
                raise InvalidSession
            repo.set_credentials(owner_id, email, self.passwords.hash(password))
            repo.revoke_user_sessions(owner_id, now)
            pair = self._issue_tokens(repo, owner_id, uuid4(), now)
            work.commit()
            return pair

    def create_or_reset_user(
        self, email: str, display_name: str, password: str
    ) -> User:
        now = datetime.now(UTC)
        with self.unit_of_work() as work:
            existing = work.repository.user_by_email(email)
            user = work.repository.save_user(
                email, display_name, self.passwords.hash(password)
            )
            if existing:
                work.repository.revoke_user_sessions(user.id, now)
            work.commit()
            return user

    def register(
        self, email: str, display_name: str, password: str, client_ip: str
    ) -> TokenPair:
        now = datetime.now(UTC)
        key = self.tokens.hash(f"register:{client_ip}")
        with self.unit_of_work() as work:
            repo = work.repository
            since = now - ATTEMPT_WINDOW
            repo.lock_attempt_bucket(key)
            repo.clear_old_attempts(since)
            if repo.count_attempts(key, since) >= 30:
                raise TooManyAttempts
            repo.record_attempt(key, now)
            work.commit()
        with self.unit_of_work() as work:
            repo = work.repository
            user = repo.create_user(email, display_name, self.passwords.hash(password))
            if user is None:
                raise EmailAlreadyRegistered
            pair = self._issue_tokens(repo, user.id, uuid4(), now)
            work.commit()
            return pair

    def login(self, email: str, password: str, client_ip: str) -> TokenPair:
        now = datetime.now(UTC)
        key = self.tokens.hash(f"{client_ip}:{email}")
        with self.unit_of_work() as work:
            repo = work.repository
            repo.clear_old_attempts(now - ATTEMPT_WINDOW)
            if repo.count_attempts(key, now - ATTEMPT_WINDOW) >= 10:
                raise TooManyAttempts
            user = repo.user_by_email(email)
            valid = self.passwords.verify(
                user.password_hash if user else None, password
            )
            if user is None or not valid:
                repo.record_attempt(key, now)
                work.commit()
                raise InvalidCredentials
            repo.clear_attempts(key)
            pair = self._issue_tokens(work.repository, user.id, uuid4(), now)
            work.commit()
            return pair

    def refresh(self, refresh_token: str) -> TokenPair:
        if not refresh_token.startswith("cm_rt_"):
            raise InvalidSession
        now = datetime.now(UTC)
        with self.unit_of_work() as work:
            repo = work.repository
            session = repo.session_by_refresh(self.tokens.hash(refresh_token))
            if not session:
                raise InvalidSession
            if session.rotated_at:
                repo.revoke_family(session.family_id, now)
                work.commit()
                raise InvalidSession
            if session.revoked_at or session.expires_at <= now:
                raise InvalidSession
            repo.rotate_session(session.id, now)
            pair = self._issue_tokens(repo, session.user_id, session.family_id, now)
            work.commit()
            return pair

    def logout(self, refresh_token: str) -> None:
        now = datetime.now(UTC)
        with self.unit_of_work() as work:
            session = work.repository.session_by_refresh(
                self.tokens.hash(refresh_token)
            )
            if session:
                work.repository.revoke_family(session.family_id, now)
                work.commit()

    def current_user(self, access_token: str) -> User:
        if not access_token.startswith("cm_at_") or len(access_token) > 256:
            raise InvalidSession
        with self.unit_of_work() as work:
            user = work.repository.user_by_access(
                self.tokens.hash(access_token), datetime.now(UTC)
            )
        if not user:
            raise InvalidSession
        return user

    def _issue_tokens(
        self, repo: AuthRepository, user_id: UUID, family_id: UUID, now: datetime
    ) -> TokenPair:
        access = self.tokens.create_access()
        refresh = self.tokens.create_refresh()
        access_expiry = now + ACCESS_LIFETIME
        refresh_expiry = now + REFRESH_LIFETIME
        repo.save_session(
            uuid4(),
            user_id,
            family_id,
            self.tokens.hash(refresh),
            refresh_expiry,
            self.tokens.hash(access),
            access_expiry,
        )
        return TokenPair(access, access_expiry, refresh, refresh_expiry)
