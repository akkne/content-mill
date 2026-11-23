"""Draw a comparison or a percentage from exact phrases in the spoken copy."""

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


@lru_cache(maxsize=100)
def font(size: int, *, bold: bool = False):
    try:
        return ImageFont.truetype(
            "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size
        )
    except OSError:
        mac_font = Path("/System/Library/Fonts/Supplemental") / (
            "Arial Bold.ttf" if bold else "Arial.ttf"
        )
        if mac_font.is_file():
            return ImageFont.truetype(str(mac_font), size)
        raise


def graphic_frame(graphic, active: int) -> Image.Image:
    canvas = Image.new("RGB", (720, 1280), "#101115")
    draw = ImageDraw.Draw(canvas)
    ink, muted, lime = "#f5f5f0", "#777a82", "#deee65"
    if graphic.kind == "share":
        label = graphic.beats[0].label
        portion = float(label.rstrip("%").strip().replace(",", "."))
        bounds = (172, 323, 548, 699)
        draw.ellipse(bounds, fill="#35373d")
        if portion:
            draw.pieslice(bounds, -90, -90 + 3.6 * portion, fill=lime)
        draw.text((360, 770), label, font=font(78, bold=True), fill=ink, anchor="mm")
    else:
        top = 585 - len(graphic.beats) * 69
        for index, beat in enumerate(graphic.beats):
            y = top + index * 138
            chosen = index == active
            color = ink if chosen else muted
            draw.line((70, y, 650, y), fill="#42454c", width=2)
            draw.text(
                (72, y + 65),
                f"{index + 1:02}",
                font=font(29),
                fill=lime if chosen else muted,
                anchor="lm",
            )
            size = 59
            while (
                size > 20
                and draw.textlength(beat.label, font=font(size, bold=chosen)) > 480
            ):
                size -= 2
            draw.text(
                (157, y + 65),
                beat.label,
                font=font(size, bold=chosen),
                fill=color,
                anchor="lm",
            )
            if chosen:
                draw.rectangle((70, y, 145, y + 4), fill=lime)
    return canvas
