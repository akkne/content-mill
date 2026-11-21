"""Read-only stdio tools for the current montage's staged clips."""

import base64
import json
import sys
from pathlib import Path
from uuid import UUID

from mcp.server.fastmcp import FastMCP, Image
from mcp.types import AudioContent

from app.infrastructure.asset_preview import AssetPreview
from app.infrastructure.video_edit import ffmpeg


def montage_server(directory: Path) -> FastMCP:
    server = FastMCP("Content Mill editing room")

    def clip(scene: int, at_ms: int) -> str:
        path = directory / f"scene-{scene:02}.mp4"
        if scene < 1 or not path.is_file() or not 0 <= at_ms < 8000:
            raise ValueError("Unknown shot or time outside source")
        return path.name

    @server.tool(structured_output=False)
    def inspect_frame(scene: int, at_ms: int):
        """Inspect a source video frame at the given millisecond before choosing a cut."""
        picture = ffmpeg(
            directory,
            [
                "-ss",
                str(at_ms / 1000),
                "-f",
                "mov",
                "-i",
                clip(scene, at_ms),
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
        return Image(data=picture, format="jpeg")

    @server.tool(structured_output=False)
    def listen(scene: int):
        """Get the native dialogue and ambient audio of the selected source shot."""

        audio = ffmpeg(
            directory,
            [
                "-f",
                "mov",
                "-i",
                clip(scene, 0),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-f",
                "mp3",
                "pipe:1",
            ],
        )
        return AudioContent(
            type="audio", data=base64.b64encode(audio).decode(), mimeType="audio/mpeg"
        )

    @server.tool(structured_output=False)
    def inspect_material(version_id: UUID, at_ms: int = 0):
        """Read a selected source document, preview an image or clip, or listen to an audio excerpt."""
        key = str(version_id)
        catalog = json.loads((directory / "catalog.json").read_text())
        fmt = catalog[key]
        file = directory / key
        if fmt in {"plain", "markdown"}:
            return file.read_text()[:20000]
        if fmt.startswith(("image/", "video/")):
            return Image(
                data=AssetPreview().render(file.read_bytes(), fmt), format="jpeg"
            )
        if fmt.startswith("audio/"):
            if not 0 <= at_ms <= 86_400_000:
                raise ValueError("Invalid audio offset")
            demuxer = {"audio/mp4": "mov", "audio/wav": "wav", "audio/mpeg": "mp3"}[fmt]
            audio = ffmpeg(
                directory,
                [
                    "-ss",
                    str(at_ms / 1000),
                    "-f",
                    demuxer,
                    "-i",
                    key,
                    "-t",
                    "8",
                    "-vn",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-f",
                    "mp3",
                    "pipe:1",
                ],
            )
            return AudioContent(
                type="audio",
                data=base64.b64encode(audio).decode(),
                mimeType="audio/mpeg",
            )
        return f"{fmt}, {file.stat().st_size} bytes"

    return server


if __name__ == "__main__":
    montage_server(Path(sys.argv[1])).run(transport="stdio")
