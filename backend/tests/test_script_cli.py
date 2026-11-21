import base64
import sys
from pathlib import Path

import pytest
from app.container import script_writer
from app.infrastructure.astra_script import AstraCli
from app.infrastructure.claude_script import ClaudeCodeCli, ClaudeScript
from app.infrastructure.codex_script import CodexScript


@pytest.mark.parametrize(
    ("name", "adapter"), [("claude", ClaudeCodeCli), ("codex", AstraCli)]
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
    assert args[args.index("--model")+1] == "gpt-6.2-astra"
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

    def run(command, text, directory, env):
        login = json.loads((Path(env["CODEX_HOME"]) / "auth.json").read_text())
        assert login["tokens"] == {"access_token": "local-access", "refresh_token": ""}
        assert "CODEX_API_KEY" not in env
        Path(command[command.index("--output-last-message") + 1]).write_text("готово")

    monkeypatch.setattr("app.infrastructure.codex_script.run_cli", run)
    writer = script_writer()
    assert writer.models[writer.selected].generate("test", "brief", []) == "готово"
    assert json.loads(auth.read_text()) == data
