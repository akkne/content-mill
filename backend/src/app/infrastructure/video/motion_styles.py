"""Browser-selectable motion treatments rendered by the regular montage worker."""

from PIL import Image, ImageDraw, ImageFilter

from app.application.videos.production import Subtitle
from app.domain.video import INTERFACE_STYLE
from app.infrastructure.video.reference_captions import HEADER, timestamp


def interface_frame() -> Image.Image:
    # Transparent window onto the composition, including any selected inserts.
    image = Image.new("RGBA", (720, 1280), "#f3f4f7")
    shadow = Image.new("RGBA", image.size)
    ImageDraw.Draw(shadow).rounded_rectangle((82, 416, 638, 1024), 32, fill="#1b294238")
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(22)))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((72, 400, 648, 1010), 30, fill="white")
    for x, color in [(104, "#fc8c89"), (124, "#f5c563"), (144, "#81cfa4")]:
        draw.ellipse((x, 423, x + 11, 434), fill=color)
    draw.rounded_rectangle((90, 451, 630, 980), 16, fill=(0, 0, 0, 0))
    return image


def _cue_time(cue: Subtitle, offset: int, total: int) -> int:
    return cue.start_ms + round((cue.end_ms - cue.start_ms) * offset / total)


def motion_captions(subtitles: list[Subtitle], style: str) -> str:
    interface = style == INTERFACE_STYLE
    output = [HEADER.format(size=43, margin=160)]
    for sub in subtitles:
        words = sub.text.split()
        # Keep a long imported caption readable. Reveal at word boundaries
        # within its existing time range, using word length as a pacing estimate.
        groups: list[list[str]] = []
        for word in words:
            if not groups or len(" ".join([*groups[-1], word])) > 29:
                groups.append([])
            groups[-1].append(word)
        total = sum(map(len, words))
        chars = 0

        for group in groups:
            start = _cue_time(sub, chars, total)
            if interface:
                parts = []
                for word in group:
                    delay = _cue_time(sub, chars, total) - start
                    parts.append(
                        r"{\alpha&HFF&\t("
                        + f"{max(0, delay - 1)},{max(1, delay)},"
                        + r"\alpha&H00&)}"
                        + word
                    )
                    chars += len(word)
                tags = r"{\an5\pos(360,300)\bord0\shad0\1c&H241E19&}"
                body = " ".join(parts)
            else:
                chars += sum(map(len, group))
                body = " ".join(group)
                if sub.emphasis and sub.emphasis in body:
                    body = body.replace(
                        sub.emphasis,
                        r"{\1c&H98F4CE&}" + sub.emphasis + r"{\1c&HFFFFFF&}",
                        1,
                    )
                tags = r"{\an2\move(360,1080,360,1052,0,160)\fad(80,65)\bord3\shad1}"
            output.append(
                f"Dialogue: 0,{timestamp(start)},{timestamp(_cue_time(sub, chars, total))},Caption,,0,0,0,,{tags}{body}"
            )
    return "\n".join(output) + "\n"
