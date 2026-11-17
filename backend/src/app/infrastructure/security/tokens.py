import hashlib
import secrets


class SecureTokens:
    def create_access(self) -> str:
        return f"cm_at_{secrets.token_urlsafe(32)}"

    def create_refresh(self) -> str:
        return f"cm_rt_{secrets.token_urlsafe(32)}"

    def hash(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
