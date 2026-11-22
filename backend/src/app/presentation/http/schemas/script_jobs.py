from typing import Annotated

from pydantic import AwareDatetime, BaseModel, StringConstraints


class ScriptRequest(BaseModel):
    brief: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)
    ]
    run_at: AwareDatetime | None = None
