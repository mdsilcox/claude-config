"""PreToolUse guard for tests/acceptance: test files and fixtures on main are never changed or overwritten.

The tests are the spec. Guarded are test files (test_*.py, *.test.mjs) and everything under fixtures/; shared
helpers such as support.py and conftest.py are ordinary code (owner, 2026-10-26). A guarded file that is not on
main yet is a draft and may still be revised (owner, 2026-10-26); when git can't tell, it counts as on main. A new
file is allowed through to the normal permission flow; an Edit, MultiEdit or NotebookEdit of a guarded file on
main, or a Write over one, is blocked (exit code 2). A test that a new request contradicts is retired with
`git rm`, never edited; if one looks wrong otherwise, the owner decides.
"""
import json
import os
import subprocess
import sys
from pathlib import Path


def guarded(path: Path) -> bool:
    parts = [p.lower() for p in path.parts]
    for i in range(len(parts) - 1):
        if parts[i:i + 2] == ["tests", "acceptance"]:
            rest, name = parts[i + 2:], parts[-1]
            return ("fixtures" in rest[:-1] or (name.startswith("test_") and name.endswith(".py"))
                    or name.endswith(".test.mjs"))
    return False


def on_main(path: Path) -> bool:
    """True when main's tree holds the file, or when git can't say (no repository, no main, no git)."""
    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], capture_output=True, text=True, timeout=5)

    try:
        top = git("-C", str(path.parent), "rev-parse", "--show-toplevel")
        if top.returncode != 0:
            return True
        root = top.stdout.strip()
        if git("-C", root, "rev-parse", "--verify", "-q", "refs/heads/main").returncode != 0:
            return True
        rel = Path(os.path.relpath(path, Path(root).resolve())).as_posix()
        if rel.startswith("../"):
            return True
        return git("-C", root, "cat-file", "-e", f"refs/heads/main:{rel}").returncode == 0
    except (OSError, subprocess.SubprocessError, ValueError):
        return True


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    tool = payload.get("tool_name", "")
    args = payload.get("tool_input") or {}
    raw = args.get("file_path") or args.get("notebook_path")
    if not raw:
        return 0
    path = Path(raw)
    if not path.is_absolute():
        path = Path(payload.get("cwd") or ".") / path
    path = path.resolve()
    if not guarded(path):
        return 0
    if tool == "Write" and not path.exists():
        return 0
    if not on_main(path):
        return 0
    print(f"{path.name} is an acceptance test on main and is never changed. If a new request contradicts it, "
          "retire it with git rm and write a new test; if it looks wrong otherwise, stop and ask the owner.",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
