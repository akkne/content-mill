from argon2 import PasswordHasher, exceptions


class Argon2Passwords:
    def __init__(self) -> None:
        self.hasher = PasswordHasher()
        self.dummy_hash = self.hasher.hash("unusable-dummy-password")

    def hash(self, password: str) -> str:
        return self.hasher.hash(password)

    def verify(self, password_hash: str | None, password: str) -> bool:
        try:
            return self.hasher.verify(password_hash or self.dummy_hash, password)
        except (exceptions.VerifyMismatchError, exceptions.VerificationError):
            return False
