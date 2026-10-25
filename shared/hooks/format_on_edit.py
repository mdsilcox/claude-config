"""PostToolUse hook (Edit|Write|MultiEdit): run the project's formatter on the file Claude just wrote.

Active only where the project sets FORMAT_RULES in the "env" block of its .claude/settings.json: a
';'-separated list of glob=command pairs, with {file} standing for the edited file, for example
"*.py=uv run ruff format {file}; *.ts,*.css=npx prettier --write {file}". Failures are ignored:
formatting is a convenience, and the fast check is the gate.
"""

import fnmatch
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

from stop_gate import find_bash


def rules():
    for pair in os.environ.get("FORMAT_RULES", "").split(";"):
        if "=" in pair:
            globs, command = pair.split("=", 1)
            yield [g.strip() for g in globs.split(",") if g.strip()], command.strip()


def main():
    data = json.load(sys.stdin)
    path = (data.get("tool_input") or {}).get("file_path", "")
    if not path or not os.environ.get("FORMAT_RULES"):
        return
    name = Path(path).name
    for globs, command in rules():
        if any(fnmatch.fnmatch(name, g) for g in globs):
            bash = find_bash()
            if bash:
                full = command.replace("{file}", shlex.quote(path.replace("\\", "/")))
                proj = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
                try:
                    subprocess.run([bash, "-c", full], cwd=proj, capture_output=True, timeout=50)
                except subprocess.TimeoutExpired:
                    pass
            return


if __name__ == "__main__":
    main()
