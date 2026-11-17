from app.application.auth_service import AuthService
from app.application.project_service import ProjectService
from app.infrastructure.database.project_unit_of_work import SqlAlchemyProjectUnitOfWork
from app.infrastructure.database.unit_of_work import SqlAlchemyAuthUnitOfWork
from app.infrastructure.security.passwords import Argon2Passwords
from app.infrastructure.security.tokens import SecureTokens

passwords = Argon2Passwords()
tokens = SecureTokens()


def auth_service() -> AuthService:
    return AuthService(SqlAlchemyAuthUnitOfWork, passwords, tokens)


def project_service() -> ProjectService:
    return ProjectService(SqlAlchemyProjectUnitOfWork)
