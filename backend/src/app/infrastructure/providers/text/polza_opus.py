import asyncio
from collections.abc import Iterable
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from app.infrastructure.video.montage_inputs import stage_montage
from app.infrastructure.video.montage_mcp import montage_server


def image_block(data: str, mime: str) -> dict:
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": mime, "data": data},
    }


class PolzaOpus:
    model = "anthropic/claude-opus-5.5"

    def __init__(self, key: str):
        self.key = key

    def generate(self, instructions: str, text: str, images: list[str]) -> str:
        return self.generate_edit(instructions, text, images, [])

    def generate_storyboard(
        self,
        instructions: str,
        text: str,
        images: list[str],
        materials: Iterable[tuple[str, str, bytes]],
    ) -> str:
        return self._generate(
            instructions, text, images, [], materials, max_tokens=65536
        )

    def generate_edit(
        self,
        instructions: str,
        text: str,
        images: list[str],
        clips: list[bytes],
        materials: Iterable[tuple[str, str, bytes]] = (),
    ) -> str:
        return self._generate(
            instructions, text, images, clips, materials, max_tokens=16384
        )

    def _generate(
        self,
        instructions: str,
        text: str,
        images: list[str],
        clips: list[bytes],
        materials: Iterable[tuple[str, str, bytes]],
        *,
        max_tokens: int,
    ) -> str:
        content = [{"type": "text", "text": text}]
        content.extend(image_block(image, "image/jpeg") for image in images)
        messages = [{"role": "user", "content": content}]
        request = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": instructions,
            "messages": messages,
        }
        with (
            TemporaryDirectory(prefix="cm-opus-") as temp,
            httpx.Client(
                headers={
                    "Authorization": "Bearer " + self.key,
                    "anthropic-version": "2023-06-01",
                },
                timeout=300,
            ) as client,
        ):
            directory = Path(temp) / "footage"
            allowed = stage_montage(directory, text, clips, materials)
            server = montage_server(directory) if allowed else None
            if server:
                request["tools"] = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                    for tool in asyncio.run(server.list_tools())
                    if tool.name in allowed
                ]
            for _ in range(32):
                response = client.post("https://polza.ai/api/v1/messages", json=request)
                response.raise_for_status()
                reply = response.json()
                blocks = reply["content"]
                if reply["stop_reason"] == "end_turn":
                    result = "".join(
                        part["text"] for part in blocks if part["type"] == "text"
                    )
                    if result.strip():
                        return result
                calls = [part for part in blocks if part["type"] == "tool_use"]
                if reply["stop_reason"] != "tool_use" or not calls or not server:
                    raise ValueError("Incomplete Polza montage response")
                results = [tool_result(server, allowed, call) for call in calls]
                messages.extend(
                    [
                        {"role": "assistant", "content": blocks},
                        {"role": "user", "content": results},
                    ]
                )
        raise ValueError("Polza montage exceeded the tool round limit")


def tool_result(server: FastMCP, allowed: list[str], call: dict) -> dict:
    result = {"type": "tool_result", "tool_use_id": call["id"]}
    if call["name"] not in allowed:
        return {**result, "is_error": True, "content": "Unknown montage tool"}
    args = dict(call["input"])
    if call["name"] in {"listen", "inspect_material"}:
        args["waveform"] = True
    try:
        parts = asyncio.run(server.call_tool(call["name"], args))
    except ToolError:
        return {
            **result,
            "is_error": True,
            "content": "Cannot inspect that source or offset",
        }
    # FastMCP also returns structured output for tools with a typed return value.
    if isinstance(parts, tuple):
        parts = parts[0]
    result["content"] = [
        image_block(part.data, part.mimeType)
        if part.type == "image"
        else {"type": "text", "text": part.text}
        for part in parts
    ]
    return result
