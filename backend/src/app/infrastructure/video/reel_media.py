from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from app.application.videos.production import ProductionError
from app.infrastructure.providers.speech.local_whisper import transcribe
from app.infrastructure.video.vector_motion import motion_design, render_layer
from app.infrastructure.video.video_edit import ffmpeg


class ReelMediaEditor:
    motion_design = staticmethod(motion_design)
    render_motion = staticmethod(render_layer)
    transcribe = staticmethod(transcribe)

    def rough_cut(
        self, sources: list[bytes], fmt: str, cuts: list[tuple[int, int, int]]
    ) -> bytes:
        with TemporaryDirectory(prefix="cm-rough-") as tmp:
            folder = Path(tmp)
            for i, source in enumerate(sources):
                (folder / f"source-{i}").write_bytes(source)
            parts = []
            for i, (scene, start, end) in enumerate(cuts):
                part = f"part-{i}.mp4"
                ffmpeg(
                    folder,
                    [
                        "-ss",
                        str(start / 1000),
                        "-f",
                        {"video/mp4": "mov", "video/webm": "matroska"}[fmt],
                        "-i",
                        f"source-{scene}",
                        "-t",
                        str((end - start) / 1000),
                        "-map",
                        "0:v:0",
                        "-map",
                        "0:a:0",
                        "-vf",
                        "fps=24,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1",
                        "-af",
                        "aresample=48000:async=1:first_pts=0,apad",
                        "-ac",
                        "2",
                        "-c:v",
                        "libx264",
                        "-preset",
                        "veryfast",
                        "-pix_fmt",
                        "yuv420p",
                        "-c:a",
                        "aac",
                        part,
                    ],
                )
                parts.append(part)
            (folder / "parts.txt").write_text("".join(f"file '{p}'\n" for p in parts))
            ffmpeg(
                folder,
                [
                    "-f",
                    "concat",
                    "-safe",
                    "1",
                    "-i",
                    "parts.txt",
                    "-c",
                    "copy",
                    "-movflags",
                    "+faststart",
                    "rough.mp4",
                ],
            )
            return (folder / "rough.mp4").read_bytes()

    def check_design(self, image: bytes) -> None:
        with Image.open(BytesIO(image), formats=["PNG"]) as raw:
            pixels = raw.convert("RGB").resize((64, 64)).getdata()
            green = sum(g > 85 and g > 1.4 * r and g > 1.4 * b for r, g, b in pixels)
            if not 0.18 < green / 4096 < 0.985:
                raise ProductionError("frame_rejected", reason="invalid_matte")

    def transparent(self, clip: bytes, length_ms: int) -> bytes:
        with TemporaryDirectory(prefix="cm-overlay-") as tmp:
            folder = Path(tmp)
            (folder / "source.mp4").write_bytes(clip)
            # Fit the full five-second movement to the spoken phrase.
            ffmpeg(
                folder,
                [
                    "-f",
                    "mov",
                    "-i",
                    "source.mp4",
                    "-map",
                    "0:v:0",
                    "-map",
                    "0:a:0?",
                    "-af",
                    f"atempo={5000 / length_ms:.6f}",
                    "-c:a",
                    "libopus",
                    "-vf",
                    f"setpts={length_ms / 5000:.6f}*PTS,fps=24,scale=360:640,format=rgba,colorkey=0x00ff00:0.30:0.12,despill=type=green,format=yuva420p,tpad=stop_mode=clone:stop_duration=0.2",
                    "-t",
                    str(length_ms / 1000),
                    "-c:v",
                    "libvpx-vp9",
                    "-deadline",
                    "realtime",
                    "-cpu-used",
                    "6",
                    "-auto-alt-ref",
                    "0",
                    "-b:v",
                    "0",
                    "-crf",
                    "27",
                    "layer.webm",
                ],
            )
            matte = ffmpeg(
                folder,
                [
                    "-c:v",
                    "libvpx-vp9",
                    "-i",
                    "layer.webm",
                    "-vf",
                    "alphaextract,scale=32:32",
                    "-pix_fmt",
                    "gray",
                    "-f",
                    "rawvideo",
                    "pipe:1",
                ],
            )
            for i in range(0, len(matte), 1024):
                frame = matte[i : i + 1024]
                if sum(v < 32 for v in frame) < 100 or sum(v > 200 for v in frame) < 3:
                    raise ProductionError("clip_rejected", reason="invalid_matte")
            if len(matte) // 1024 < max(1, round(length_ms * 24 / 1000) - 1):
                raise ProductionError("clip_rejected", reason="invalid_clip")
            return (folder / "layer.webm").read_bytes()
