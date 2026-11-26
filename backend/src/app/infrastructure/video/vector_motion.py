"""Rasterize declarative vector artwork and model keyframes into a transparent WebM."""

import math
import random
import re
import wave
from array import array
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree as ET

from PIL import Image
from resvg_py import svg_to_bytes

from app.application.videos.motion_score import MotionScore
from app.infrastructure.video.video_edit import ffmpeg

TAGS = {
    "g",
    "path",
    "rect",
    "circle",
    "ellipse",
    "line",
    "polygon",
    "polyline",
    "text",
    "tspan",
    "defs",
    "linearGradient",
    "radialGradient",
    "stop",
}
ATTRS = {
    "id",
    "d",
    "points",
    "x",
    "y",
    "dx",
    "dy",
    "x1",
    "y1",
    "x2",
    "y2",
    "cx",
    "cy",
    "r",
    "rx",
    "ry",
    "fx",
    "fy",
    "width",
    "height",
    "fill",
    "stroke",
    "stroke-width",
    "stroke-miterlimit",
    "paint-order",
    "stroke-linecap",
    "stroke-linejoin",
    "stroke-dasharray",
    "stroke-dashoffset",
    "fill-rule",
    "opacity",
    "fill-opacity",
    "stroke-opacity",
    "transform",
    "font-size",
    "font-weight",
    "font-style",
    "font-family",
    "text-anchor",
    "dominant-baseline",
    "letter-spacing",
    "offset",
    "stop-color",
    "stop-opacity",
    "gradientUnits",
    "gradientTransform",
}


def artwork(fragment: str) -> str:
    if "<!" in fragment or "<?" in fragment:
        raise ValueError("Unsupported SVG declaration")
    try:
        group = ET.fromstring(f"<g>{fragment}</g>")
    except ET.ParseError as error:
        raise ValueError("Malformed SVG") from error
    for element in group.iter():
        if element.tag not in TAGS:
            raise ValueError(f"Unsupported SVG element {element.tag}")
        if unsupported := element.attrib.keys() - ATTRS:
            raise ValueError(
                f"Unsupported attributes on {element.tag}: {sorted(unsupported)}"
            )
        for value in element.attrib.values():
            if "url" in value.lower() and not re.fullmatch(r"url\(#[\w.-]+\)", value):
                raise ValueError("Only local paint references are supported")
    return ET.tostring(group, encoding="unicode")


def pose_at(keys, t):
    end = next((i for i, p in enumerate(keys) if p.t >= t), len(keys) - 1)
    a, b = keys[max(0, end - 1)], keys[end]
    f = min(1, max(0, (t - a.t) / (b.t - a.t))) if b.t > a.t else 1
    if b.ease == "out":
        f = 1 - (1 - f) ** 3
    elif b.ease == "smooth":
        f = f * f * (3 - 2 * f)
    return [
        getattr(a, k) + (getattr(b, k) - getattr(a, k)) * f
        for k in ("x", "y", "scale", "rotation", "opacity", "wipe")
    ]


def frame_svg(layers, t):
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="360" viewBox="0 0 600 360">'
    ]
    for i, (layer, art) in enumerate(layers):
        x, y, scale, angle, opacity, wipe = pose_at(layer.keys, t)
        px, py = layer.pivot_x, layer.pivot_y
        parts.append(
            f'<defs><clipPath id="cm-wipe-{i}"><rect width="{600 * wipe:.3f}" height="360"/></clipPath></defs><g clip-path="url(#cm-wipe-{i})"><g opacity="{opacity:.4f}" transform="translate({x + px:.3f} {y + py:.3f}) rotate({angle:.3f}) scale({scale:.5f}) translate({-px} {-py})">{art}</g></g>'
        )
    return "".join(parts) + "</svg>"


def write_foley(path, cues, duration):
    rate = 24000
    samples = array("h", [0]) * round(duration * rate)
    noise = random.Random(13)
    for cue in cues:
        offset = round(cue.t * len(samples))
        length = {"tap": 0.09, "swish": 0.20, "chime": 0.32}[cue.kind]
        smooth_noise = 0.0
        for i in range(min(round(length * rate), len(samples) - offset)):
            t = i / rate
            if cue.kind == "swish":
                smooth_noise = 0.78 * smooth_noise + 0.22 * noise.uniform(-1, 1)
                sound = smooth_noise * math.sin(math.pi * t / length) ** 2
            else:
                freq = 820 if cue.kind == "chime" else 245
                sound = (
                    math.sin(2 * math.pi * freq * t)
                    * min(t * 500, 1)
                    * math.exp(-6 * t / length)
                )
            samples[offset + i] = max(
                -32767, min(32767, samples[offset + i] + round(sound * 7000))
            )
    with wave.open(str(path), "wb") as wav:
        wav.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        wav.writeframes(samples.tobytes())


def motion_design(score: MotionScore) -> bytes:
    layers = [(layer, artwork(layer.artwork)) for layer in score.layers]
    probes = []
    poster = None
    for time in (0, 0.2, 0.4, 0.6, 0.8, 1):
        png = svg_to_bytes(
            svg_string=frame_svg(layers, time), font_family="DejaVu Sans"
        )
        with Image.open(BytesIO(png)) as image:
            probe = image.convert("RGBA").resize((100, 60))
            probes.append(probe.tobytes())
            if 0.025 < 1 - probe.getchannel("A").histogram()[0] / 6000 < 0.97:
                poster = png
    if poster is None or len(set(probes)) < 2:
        raise ValueError("Illustration needs visible movement and transparent margins")
    return poster


def render_layer(score: MotionScore, length_ms: int) -> bytes:
    if not 500 <= length_ms <= 5000:
        raise ValueError("Unexpected animation duration")
    layers = [(layer, artwork(layer.artwork)) for layer in score.layers]
    frames = round(length_ms * 24 / 1000)
    with TemporaryDirectory(prefix="cm-vector-") as tmp:
        folder = Path(tmp)
        for i in range(frames):
            png = svg_to_bytes(
                svg_string=frame_svg(layers, i / (frames - 1)),
                font_family="DejaVu Sans",
            )
            (folder / f"{i:03}.png").write_bytes(png)
        args = ["-framerate", "24", "-i", "%03d.png"]
        if score.sounds:
            write_foley(folder / "foley.wav", score.sounds, frames / 24)
            args.extend(["-i", "foley.wav", "-c:a", "libopus"])
        ffmpeg(
            folder,
            [
                *args,
                "-c:v",
                "libvpx-vp9",
                "-pix_fmt",
                "yuva420p",
                "-auto-alt-ref",
                "0",
                "-row-mt",
                "1",
                "-deadline",
                "realtime",
                "-cpu-used",
                "6",
                "-b:v",
                "0",
                "-crf",
                "23",
                "layer.webm",
            ],
        )
        return (folder / "layer.webm").read_bytes()
