import json
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx

from app.infrastructure.script_cli import run_cli


class ClaudeScript:
    model = "claude-sonnet-4-6"

    def __init__(self, key: str):
        self.key = key

    def generate(self, instructions: str, text: str, images: list[str]) -> str:
        content = [{"type": "text", "text": text}]
        content.extend(
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": image},
            }
            for image in images
        )
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": self.key, "anthropic-version": "2023-06-01"},
            json={
                "model": self.model,
                "system": instructions,
                "max_tokens": 6000,
                "messages": [{"role": "user", "content": content}],
            },
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()
        if data["stop_reason"] != "end_turn":
            raise ValueError("Incomplete response")
        return "".join(
            part["text"] for part in data["content"] if part["type"] == "text"
        )


class ClaudeCodeCli:
    model = "claude:" + ClaudeScript.model

    def __init__(self, key: str):
        self.key = key

    def generate(self, instructions: str, text: str, images: list[str]) -> str:
        blocks = [{"type": "text", "text": text}]
        blocks.extend(
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": image},
            }
            for image in images
        )
        message = {"type": "user", "message": {"role": "user", "content": blocks}}
        with TemporaryDirectory(prefix="cm-claude-") as folder:
            output = run_cli(
                [
                    "claude",
                    "-p",
                    "--bare",
                    "--model",
                    ClaudeScript.model,
                    "--tools",
                    "",
                    "--strict-mcp-config",
                    "--no-session-persistence",
                    "--system-prompt",
                    instructions,
                    "--input-format",
                    "stream-json",
                    "--output-format",
                    "stream-json",
                    "--verbose",
                ],
                json.dumps(message) + "\n",
                Path(folder),
                {"ANTHROPIC_API_KEY": self.key},
            )
        for line in reversed(output.splitlines()):
            event = json.loads(line)
            if event.get("type") == "result":
                if event.get("subtype") == "success" and not event.get("is_error"):
                    return event["result"]
                break
        raise ValueError("Claude Code did not return a successful result")
