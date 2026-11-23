import os
from uuid import UUID


def configured_owner() -> UUID | None:
    try:
        return UUID(os.getenv("MILL_ADMIN_USER_ID", "").strip())
    except ValueError:
        return None
