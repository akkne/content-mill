"""Read-only stdio tools for the current montage's staged clips."""

import base64
import json
import sys
from pathlib import Path
from uuid import UUID

from mcp.server.fastmcp import FastMCP, Image
from mcp.types import AudioContent, ToolAnnotations

from app.infrastructure.asset_preview import AssetPreview
from app.infrastructure.video_edit import ffmpeg


def montage_server(directory: Path) -> FastMCP:
    server = FastMCP("Content Mill editing room")

    read_only = ToolAnnotations(
        readOnlyHint=True, destructiveHint=False, openWorldHint=False
    )

    def clip(scene: int, at_ms: int) -> str:
        path = directory / f"scene-{scene:02}.mp4"
        if scene < 1 or not path.is_file() or not 0 <= at_ms < 10000:
            raise ValueError("Unknown shot or time outside source")
        return path.name

    def video_frame(filename: str, demuxer: str, at_ms: int):
        if not 0 <= at_ms <= 86_400_000:
            raise ValueError("Invalid video offset")
        picture = ffmpeg(
            directory,
            [
                "-ss",
                str(at_ms / 1000),
                "-f",
                demuxer,
                "-i",
                filename,
                "-frames:v",
                "1",
                "-vf",
                "scale=320:-2",
                "-c:v",
                "mjpeg",
                "-f",
                "image2pipe",
                "pipe:1",
            ],
        )
        if not picture:
            raise ValueError("No frame at that time")
        return Image(data=picture, format="jpeg")

    @server.tool(structured_output=False, annotations=read_only)
    def inspect_frame(scene: int, at_ms: int):
        """Inspect a source video frame at the given millisecond before choosing a cut."""
        return video_frame(clip(scene, at_ms), "mov", at_ms)

    def audio_excerpt(inputs: list[str], waveform: bool):
        if waveform:
            picture = ffmpeg(
                directory,
                [
                    *inputs,
                    "-filter_complex",
                    "[0:a]aresample=16000:async=1:first_pts=0,aformat=channel_layouts=mono,showwavespic=s=800x160:colors=white[wave]",
                    "-map",
                    "[wave]",
                    "-frames:v",
                    "1",
                    "-c:v",
                    "png",
                    "-f",
                    "image2pipe",
                    "pipe:1",
                ],
            )
            return Image(data=picture, format="png")
        audio = ffmpeg(
            directory,
            [*inputs, "-vn", "-ac", "1", "-ar", "16000", "-f", "mp3", "pipe:1"],
        )
        return AudioContent(
            type="audio", data=base64.b64encode(audio).decode(), mimeType="audio/mpeg"
        )

    @server.tool(structured_output=False, annotations=read_only)
    def listen(scene: int, waveform: bool = True):
        """Show sound level across the shot (left=start, right=end). Audio-capable clients can request waveform=false for MP3."""
        return audio_excerpt(["-f", "mov", "-i", clip(scene, 0)], waveform)

    @server.tool(structured_output=False, annotations=read_only)
    def inspect_material(version_id: UUID, at_ms: int = 0, waveform: bool = True):
        """Read a selected source document, preview an image or clip, or inspect an audio excerpt (eight seconds from at_ms)."""
        key = str(version_id)
        catalog = json.loads((directory / "catalog.json").read_text())
        fmt = catalog[key]
        file = directory / key
        if fmt in {"plain", "markdown"}:
            return file.read_text()[:20000]
        if fmt.startswith("video/"):
            demuxer = {"video/mp4": "mov", "video/webm": "matroska"}[fmt]
            return video_frame(key, demuxer, at_ms)
        if fmt.startswith("image/"):
            return Image(
                data=AssetPreview().render(file.read_bytes(), fmt), format="jpeg"
            )
        if fmt.startswith("audio/"):
            if not 0 <= at_ms <= 86_400_000:
                raise ValueError("Invalid audio offset")
            demuxer = {"audio/mp4": "mov", "audio/wav": "wav", "audio/mpeg": "mp3"}[fmt]
            return audio_excerpt(
                ["-ss", str(at_ms / 1000), "-f", demuxer, "-t", "8", "-i", key],
                waveform,
            )
        return f"{fmt}, {file.stat().st_size} bytes"

    return server


if __name__ == "__main__":
    montage_server(Path(sys.argv[1])).run(transport="stdio")
