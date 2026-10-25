"""Stop hook: run the project's fast check before Claude finishes, and send failures back to it.

Active only where the project sets FAST_CHECK in the "env" block of its .claude/settings.json (the
env block waits for workspace trust, so an untrusted repo can't use this to run code). It runs only
when the working tree has changed since the last green check, so plain conversation costs nothing.
A failure blocks the stop once per tree state: if Claude stops again without changing anything, the
stop goes through with a warning to the user instead of looping.

The check runs through bash: Git Bash on Windows (never WSL's bash.exe), the system bash elsewhere.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

STATE_DIR = Path.home() / ".claude" / "state" / "fast-check"
CHECK_TIMEOUT = 270  # the hook's own timeout in settings.json is 300
TAIL_LINES = 60


def find_bash():
    if os.name == "nt":
        for p in (os.environ.get("CLAUDE_CODE_GIT_BASH_PATH"), r"C:\Program Files\Git\bin\bash.exe"):
            if p and Path(p).is_file():
                return p
        return None
    return shutil.which("bash") or "/bin/bash"


def git(proj, *args):
    return subprocess.run(["git", "-C", proj, *args], capture_output=True, timeout=30)


def tree_state(proj):
    """Hash of the uncommitted changes; '' for a clean tree, None outside a git repo."""
    status = git(proj, "status", "--porcelain=v1", "-uall")
    if status.returncode != 0:
        return None
    if not status.stdout.strip():
        return ""
    diff = git(proj, "diff", "HEAD", "--binary")
    if diff.returncode != 0:  # no commits yet
        diff = git(proj, "diff", "--binary")
    h = hashlib.sha256(status.stdout + diff.stdout)
    for line in status.stdout.decode("utf-8", "replace").splitlines():
        if line.startswith("?? "):
            try:
                st = Path(proj, line[3:].strip('"')).stat()
                h.update(f"{st.st_size}:{st.st_mtime_ns}".encode())
            except OSError:
                pass
    return h.hexdigest()


def state_file(proj):
    return STATE_DIR / (hashlib.sha1(str(Path(proj).resolve()).encode()).hexdigest()[:16] + ".json")


def load(proj):
    try:
        return json.loads(state_file(proj).read_text())
    except (OSError, ValueError):
        return {}


def save(proj, record):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file(proj).write_text(json.dumps(record))


def main():
    data = json.load(sys.stdin)
    command = os.environ.get("FAST_CHECK", "").strip()
    if not command:
        return
    proj = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    state = tree_state(proj)
    if not state:
        return  # not a repo, or nothing changed since the last commit
    record = load(proj)
    if state == record.get("green"):
        return
    if state == record.get("failed") and data.get("stop_hook_active"):
        print(json.dumps({"systemMessage": "Fast check still failing, and Claude stopped without "
                                           "changing anything since. Check it before committing."}))
        return
    bash = find_bash()
    if not bash:
        print(json.dumps({"systemMessage": "Fast check skipped: Git Bash not found."}))
        return
    try:
        run = subprocess.run([bash, "-c", command], cwd=proj, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=CHECK_TIMEOUT)
    except subprocess.TimeoutExpired:
        print(json.dumps({"systemMessage": f"Fast check timed out after {CHECK_TIMEOUT} s and was "
                                           "not enforced. Make FAST_CHECK faster."}))
        return
    if run.returncode == 0:
        record["green"] = state
        save(proj, record)
        return
    record["failed"] = state
    save(proj, record)
    tail = "\n".join((run.stdout + run.stderr).strip().splitlines()[-TAIL_LINES:])
    print(json.dumps({"decision": "block", "reason": (
        f"The fast check failed (exit {run.returncode}): `{command}`\n\n{tail}\n\n"
        "Fix the failures before finishing. If they predate your change or can't be fixed now, "
        "say so plainly in your reply instead of reporting success.")}))


if __name__ == "__main__":
    main()
