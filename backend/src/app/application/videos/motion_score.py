"""A GPT-authored foreground composition. Time is normalized to the spoken cue."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

Unit = Annotated[float, Field(ge=0, le=1)]
Offset = Annotated[float, Field(ge=-1200, le=1200)]


class Pose(BaseModel):
    t: Unit
    x: Offset = 0
    y: Offset = 0
    scale: float = Field(default=1, ge=0.02, le=5)
    rotation: float = Field(default=0, ge=-720, le=720)
    opacity: Unit = 1
    wipe: Unit = 1
    ease: Literal["linear", "out", "smooth"] = "out"


class MotionLayer(BaseModel):
    artwork: str = Field(min_length=1, max_length=12000)
    pivot_x: Offset = 300
    pivot_y: Offset = 180
    keys: list[Pose] = Field(min_length=1, max_length=16)

    @model_validator(mode="after")
    def ordered(self):
        times = [p.t for p in self.keys]
        if times != sorted(set(times)):
            raise ValueError("Keyframes must be in increasing time order")
        return self


class SoundCue(BaseModel):
    t: Unit
    kind: Literal["tap", "chime", "swish"]


class MotionScore(BaseModel):
    white_cutaway: bool = False
    layers: list[MotionLayer] = Field(min_length=2, max_length=18)
    sounds: list[SoundCue] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def animated(self):
        if not any(
            a.model_dump(exclude={"t", "ease"}) != b.model_dump(exclude={"t", "ease"})
            for layer in self.layers
            for a, b in zip(layer.keys, layer.keys[1:])
        ):
            raise ValueError("The illustration needs a visible change of pose")
        return self


AUTHOR = """You are the motion designer. Author an original, finished layered animation as JSON matching schema.
Stage: a transparent 600 x 360 vector canvas over the lower torso in a vertical talking-head film. Captions have their own track below. First input image shows the footage. Compose for legibility at phone size. Use the selected language for any typography.
Tell the spoken idea in pictures: a before and after, a changing measurement, an object revealing its mechanism. Stage a clear visual premise, develop it at the relevant spoken words and resolve on a readable hero image. Design the art and its actual keyframes yourself. Build silhouettes or detailed cut-paper objects with custom paths; pair restrained technical linework with a prominent focal point, selective blue accent and warm white. Integrate lettering into the diagram only where it explains a fact; use 30–56px type, strong contrast, avoid duplicate captions, decorative microtext and generic emoji. Use interface elements only when they illustrate the subject. Use a thin dark contour or bounded paper backing if the footage is busy. Preserve generous transparent margins. Keep the top face unobstructed. Follow supplied brand direction.
"""

WHITE_AUTHOR = """Author an original full-screen 9:16 animation on pure white. The avatar disappears and the existing narration continues. Draw only the concrete tool, object or process described by the cue. Use supplied brand references when relevant; otherwise derive the design from the brief. Show the initial state immediately, one meaningful operation on the spoken word and a readable result held through the very last frame. The editor hard-cuts back to the presenter; never animate the whole illustration out or fade to blank white. Translate the supplied spatial positions and relative cue times into artwork, pivots and normalized keyframes. Keep anchored parts still and make the final visible state match the described result. Design for 1–2 seconds. No people, presenters, portraits, dialogue or background music. Use dark contours or colored fills on the supplied white canvas. Stage is 360 x 640, reserve outer margins and the bottom 100 px for captions. Center the action in the middle of the portrait canvas. Set pivot_x and pivot_y for every moving object. The first input image is timing context only. Return JSON matching the schema.
"""

VECTOR_RULES = """Each layer's artwork is an SVG fragment in the shared stage coordinates. Supported elements: g, path, rect, circle, ellipse, line, polygon, polyline, text, tspan, defs, linearGradient, radialGradient, stop. Use presentation attributes, no style, external files, scripts, filters or images. Prefer DejaVu Sans and DejaVu Serif. Internal gradients may use fill="url(#uniqueId)" with unique IDs. The first layer is at the back. Add a separate layer for each independently moving part. Keyframe t is fraction of cue duration; absolute pose values interpolate until the next key (ease on destination). x/y are translations in pixels, rotation in degrees about pivot, scale uniform. wipe reveals from canvas left to right. Before the first key its pose is held; start at opacity zero if a reveal is delayed. Stagger entrances. Retain the readable settled scene for the last quarter. Optional soft tap, swish or chime precisely on a visual impact. Return only JSON."""

AUTHOR += VECTOR_RULES
WHITE_AUTHOR += VECTOR_RULES
