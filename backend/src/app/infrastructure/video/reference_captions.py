from app.application.videos.production import Subtitle
from app.domain.video import FACTS_STYLE

# Coordinates and type sizes refer to the final portrait frame.
HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Caption,DejaVu Sans,{size},&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,2.5,1,2,54,54,{margin},1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""


def timestamp(ms: int) -> str:
    centis = (ms + 5) // 10
    return f"{centis // 360000}:{centis // 6000 % 60:02}:{centis // 100 % 60:02}.{centis % 100:02}"


def reference_captions(subtitles: list[Subtitle], style: str) -> str:
    factual = style == FACTS_STYLE
    color = "&H54F2DB&" if factual else "&H63DFFF&"
    output = [HEADER.format(size=47 if factual else 42, margin=208 if factual else 352)]
    for sub in subtitles:
        text = sub.text
        # Caption text already excludes ASS control characters in the input schema.
        # Only highlight a literal substring of the approved caption.
        if sub.emphasis and sub.emphasis.strip() and sub.emphasis in text:
            start, emphasis, end = text.partition(sub.emphasis)
            accent = r"{\1c" + color + (r"\i1" if factual else "") + "}"
            text = start + accent + emphasis + r"{\rCaption}" + end
        output.append(
            f"Dialogue: 0,{timestamp(sub.start_ms)},{timestamp(sub.end_ms)},Caption,,0,0,0,,{text}"
        )
    return "\n".join(output) + "\n"
