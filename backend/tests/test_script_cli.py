import base64
import sys
from pathlib import Path

import pytest
from app.container import script_writer
from app.infrastructure.providers.text.claude_script import ClaudeCodeCli, ClaudeScript
from app.infrastructure.providers.text.codex_script import CodexScript
from app.infrastructure.providers.text.sol_script import SolCli


@pytest.mark.parametrize(
    ("name", "adapter"), [("claude", ClaudeCodeCli), ("codex", SolCli)]
)
def test_explicit_cli_runs_in_private_directory(monkeypatch, tmp_path, name, adapter):
    program = tmp_path / name
    program.write_text(
        f"#!{Path(sys.executable).resolve()}\n"
        + """
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
text = sys.stdin.read()
assert Path.cwd() == Path.home().resolve()
assert "DATABASE_URL" not in os.environ
if Path(sys.argv[0]).name == "codex":
    assert "ANTHROPIC_API_KEY" not in os.environ
    assert os.environ["CODEX_API_KEY"] == "codex-test"
    assert args[args.index("--model")+1] == "gpt-6.2-sol"
    assert 'model_reasoning_effort="high"' in args
    assert text == "brief" and args[0] == "exec"
    assert Path(args[args.index("--image")+1]).read_bytes() == b"jpeg"
    Path(args[args.index("--output-last-message")+1]).write_text(str(Path.cwd()))
else:
    assert "CODEX_API_KEY" not in os.environ
    assert os.environ["ANTHROPIC_API_KEY"] == "claude-test"
    blocks = json.loads(text)["message"]["content"]
    assert blocks[0]["text"] == "brief" and blocks[1]["source"]["data"] == "anBlZw=="
    assert "-p" in args and args[args.index("--tools")+1] == ""
    print(json.dumps({"type":"result", "subtype":"success", "result":str(Path.cwd())}))
"""
    )
    program.chmod(0o700)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "codex-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "claude-test")
    if name == "codex":
        monkeypatch.delenv("CONTENT_MILL_SCRIPT_PROVIDER", raising=False)
    else:
        monkeypatch.setenv("CONTENT_MILL_SCRIPT_PROVIDER", name)
    monkeypatch.setenv("CONTENT_MILL_SCRIPT_MODEL", "ignored-in-cli-mode")
    writer = script_writer()
    assert writer.selected == adapter.model
    assert {ClaudeScript.model, CodexScript.model} <= writer.models.keys()
    folder = writer.models[writer.selected].generate(
        "instructions", "brief", [base64.b64encode(b"jpeg").decode()]
    )
    assert not Path(folder).exists()


def test_provider_never_falls_back_to_other_key(monkeypatch):
    monkeypatch.setenv("CONTENT_MILL_SCRIPT_PROVIDER", "codex")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "claude-test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    writer = script_writer()
    assert writer.selected not in writer.models
    monkeypatch.setenv("CONTENT_MILL_SCRIPT_PROVIDER", "unknown")
    with pytest.raises(ValueError, match="CONTENT_MILL_SCRIPT_PROVIDER"):
        script_writer()


def test_local_chatgpt_login(monkeypatch, tmp_path):
    import json

    auth = tmp_path / "auth.json"
    data = {
        "auth_mode": "chatgpt",
        "tokens": {"access_token": "local-access", "refresh_token": "desktop-only"},
    }
    auth.write_text(json.dumps(data))
    monkeypatch.setenv("CONTENT_MILL_CODEX_AUTH_FILE", str(auth))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("CONTENT_MILL_SCRIPT_PROVIDER", "codex")
    monkeypatch.setattr("app.container.shutil.which", lambda name: name)

    def run(command, text, directory, env, *, timeout):
        login = json.loads((Path(env["CODEX_HOME"]) / "auth.json").read_text())
        assert login["tokens"] == {"access_token": "local-access", "refresh_token": ""}
        assert "CODEX_API_KEY" not in env
        Path(command[command.index("--output-last-message") + 1]).write_text("готово")

    monkeypatch.setattr("app.infrastructure.providers.text.codex_script.run_cli", run)
    writer = script_writer()
    assert writer.models[writer.selected].generate("test", "brief", []) == "готово"
    assert json.loads(auth.read_text()) == data


def test_montage_tools_can_read_only_the_staged_production(monkeypatch):
    import json
    from uuid import uuid4

    version = str(uuid4())

    def run(command, text, directory, env, *, timeout):
        assert timeout == 600
        approvals = [flag for flag in command if "approval_mode" in flag]
        assert set(approvals) == {
            f'mcp_servers.montage.tools.{tool}.approval_mode="approve"'
            for tool in ("inspect_frame", "listen", "inspect_material")
        }
        assert 'approval_policy="never"' in command
        footage = directory / "footage"
        assert (footage / "scene-01.mp4").read_bytes() == b"test clip"
        assert (footage / version).read_bytes() == b"test frame"
        assert json.loads((footage / "catalog.json").read_text()) == {
            version: "image/png"
        }
        Path(command[command.index("--output-last-message") + 1]).write_text("timeline")

    monkeypatch.setattr("app.infrastructure.providers.text.codex_script.run_cli", run)
    result = SolCli("test").generate_edit(
        "edit", "brief", [], [b"test clip"], [(version, "image/png", b"test frame")]
    )
    assert result == "timeline"


def test_storyboard_waits_without_deadline_and_exposes_original(monkeypatch):
    from uuid import uuid4

    version = str(uuid4())

    def run(command, text, directory, env, *, timeout):
        assert timeout is None
        assert (directory / "footage" / version).read_bytes() == b"source"
        Path(command[command.index("--output-last-message") + 1]).write_text("board")

    monkeypatch.setattr("app.infrastructure.providers.text.codex_script.run_cli", run)
    assert (
        SolCli("test").generate_storyboard(
            "plan", "brief", [], [(version, "video/mp4", b"source")]
        )
        == "board"
    )
