from app.application.auth_service import AuthService
from app.infrastructure.database.unit_of_work import SqlAlchemyAuthUnitOfWork
from app.infrastructure.security.passwords import Argon2Passwords
from app.infrastructure.security.tokens import SecureTokens

passwords = Argon2Passwords()
tokens = SecureTokens()


def auth_service() -> AuthService:
    return AuthService(SqlAlchemyAuthUnitOfWork, passwords, tokens)
