import os
import signal
import subprocess
from pathlib import Path


def run_cli(
    command: list[str], payload: str, directory: Path, key_env: dict[str, str]
) -> str:
    """Run one isolated CLI session, including its launcher and native children."""
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(directory),
        "TMPDIR": str(directory),
        **key_env,
    }
    with subprocess.Popen(
        command,
        cwd=directory,
        env=env,
        start_new_session=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
    ) as process:
        try:
            output, _ = process.communicate(payload, timeout=120)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise
        if process.returncode:
            raise RuntimeError(f"{command[0]} exited with status {process.returncode}")
    return output
