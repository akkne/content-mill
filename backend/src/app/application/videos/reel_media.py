from typing import Annotated, Protocol

from pydantic import BaseModel, Field

from app.application.videos.motion_score import MotionScore

Index = Annotated[int, Field(ge=0)]


class Word(BaseModel):
    start_ms: Index
    end_ms: int = Field(gt=0)
    text: str = Field(min_length=1)


class ReelMedia(Protocol):
    def transcribe(self, media: bytes, fmt: str, language: str) -> list[Word]: ...
    def rough_cut(
        self, sources: list[bytes], fmt: str, cuts: list[tuple[int, int, int]]
    ) -> bytes: ...
    def motion_design(self, score: MotionScore) -> bytes: ...
    def render_motion(self, score: MotionScore, length_ms: int) -> bytes: ...
    def check_design(self, image: bytes) -> None: ...
    def transparent(self, clip: bytes, length_ms: int) -> bytes: ...
