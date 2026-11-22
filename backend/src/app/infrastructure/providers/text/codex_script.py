import base64
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx

from app.infrastructure.providers.text.script_cli import run_cli


class CodexScript:
    model = "gpt-5.3-codex"

    def __init__(self, key: str):
        self.key = key

    def generate(self, instructions: str, text: str, images: list[str]) -> str:
        content = [{"type": "input_text", "text": text}]
        content.extend(
            {"type": "input_image", "image_url": "data:image/jpeg;base64," + image}
            for image in images
        )
        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": "Bearer " + self.key},
            json={
                "model": self.model,
                "store": False,
                "instructions": instructions,
                "input": [{"role": "user", "content": content}],
                "max_output_tokens": 6000,
            },
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()
        if data["status"] != "completed":
            raise ValueError("Incomplete response")
        return "".join(
            part["text"]
            for item in data["output"]
            if item["type"] == "message" and item.get("phase") != "commentary"
            for part in item["content"]
            if part["type"] == "output_text"
        )


class CodexCli:
    model_id = CodexScript.model
    model = "codex:" + model_id
    config_args: tuple[str, ...] = ()

    def __init__(self, key: str = "", *, auth_file: Path | None = None):
        self.key = key
        self.auth_file = auth_file

    def generate(self, instructions: str, text: str, images: list[str]) -> str:
        return self._session(instructions, text, images, [], ())

    def generate_storyboard(
        self,
        instructions: str,
        text: str,
        images: list[str],
        materials: Iterable[tuple[str, str, bytes]],
    ) -> str:
        return self._session(instructions, text, images, [], materials, timeout=None)

    def generate_edit(
        self,
        instructions: str,
        text: str,
        images: list[str],
        clips: list[bytes],
        materials: Iterable[tuple[str, str, bytes]] = (),
    ) -> str:
        return self._session(instructions, text, images, clips, materials, timeout=600)

    def _session(
        self,
        instructions: str,
        text: str,
        images: list[str],
        clips: list[bytes],
        materials: Iterable[tuple[str, str, bytes]] = (),
        *,
        timeout: int | None = 120,
    ) -> str:
        with TemporaryDirectory(prefix="cm-codex-") as folder:
            directory = Path(folder)
            home = directory / "config"
            home.mkdir()
            env = {"CODEX_HOME": str(home)}
            if self.auth_file is None:
                env["CODEX_API_KEY"] = self.key
            else:
                # The desktop client owns token refresh. Use only its current login.
                auth = json.loads(self.auth_file.read_text(encoding="utf-8"))
                if (
                    auth.get("auth_mode") != "chatgpt"
                    or not auth["tokens"]["access_token"]
                ):
                    raise ValueError("A ChatGPT login is required")
                auth["tokens"]["refresh_token"] = ""
                auth["OPENAI_API_KEY"] = None
                (home / "auth.json").write_text(json.dumps(auth), encoding="utf-8")
            command = [
                "codex",
                "exec",
                "--ephemeral",
                "--ignore-user-config",
                "--skip-git-repo-check",
                "--model",
                self.model_id,
                *self.config_args,
                "-c",
                "project_doc_max_bytes=0",
                "-c",
                'approval_policy="never"',
                "-c",
                'web_search="disabled"',
                "-c",
                'default_permissions="script"',
                "-c",
                'permissions.script.filesystem={":minimal"="read",":project_roots"="read"}',
                "-c",
                'shell_environment_policy.inherit="none"',
                "-c",
                "developer_instructions="
                + json.dumps(instructions, ensure_ascii=False),
            ]
            if clips or materials:
                footage = directory / "footage"
                footage.mkdir()
                for index, clip in enumerate(clips, start=1):
                    (footage / f"scene-{index:02}.mp4").write_bytes(clip)
                catalog = {}
                for version, fmt, data in materials:
                    (footage / version).write_bytes(data)
                    catalog[version] = fmt
                (footage / "catalog.json").write_text(json.dumps(catalog))
                command.extend(
                    [
                        "-c",
                        "mcp_servers.montage.command=" + json.dumps(sys.executable),
                        "-c",
                        "mcp_servers.montage.args="
                        + json.dumps(
                            ["-m", "app.infrastructure.video.montage_mcp", str(footage)]
                        ),
                        "-c",
                        "mcp_servers.montage.required=true",
                    ]
                )
                # Only these local, read-only tools can run unattended.
                for tool in (
                    ("inspect_frame", "listen", "inspect_material")
                    if clips
                    else ("inspect_material",)
                ):
                    command.extend(
                        [
                            "-c",
                            f'mcp_servers.montage.tools.{tool}.approval_mode="approve"',
                        ]
                    )
            for feature in (
                "shell_tool",
                "unified_exec",
                "multi_agent",
                "plugins",
                "view_image",
                "computer_use",
                "image_generation",
            ):
                command.extend(["--disable", feature])
            for index, image in enumerate(images):
                preview = directory / f"preview-{index}.jpg"
                preview.write_bytes(base64.b64decode(image, validate=True))
                command.extend(["--image", str(preview)])
            result = directory / "result.txt"
            command.extend(["--output-last-message", str(result), "-"])
            run_cli(command, text, directory, env, timeout=timeout)
            return result.read_text(encoding="utf-8")
