"""SessionStart hook: set up new projects automatically.

When a session starts in a git repo that isn't set up for this workspace yet (no CLAUDE.md, or no
FAST_CHECK in .claude/settings.json), it tells Claude to set the repo up first. A fixed template
can't do this, because each project's fast check and formatter differ. When FAST_CHECK was left
empty and the repo has since gained tests, it reminds Claude to fill it in. Otherwise it prints
nothing.

It skips folders that aren't git repos, the home folder, anything under ~/.claude, the app's
scratch workspaces, and repos with a .claude/no-auto-setup file.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

TESTS = re.compile(r"(^|/)tests?/|(^|/)test_[^/]*\.py$|_test\.(py|go)$|\.(test|spec)\.[cm]?[jt]sx?$")

SETUP = """Workspace setup: this repo ({root}) isn't set up for the owner's Claude workspace yet ({missing}). The owner wants this done automatically, so do it first and quickly, then tell them in one or two lines what you set. Don't commit.
1. CLAUDE.md at the repo root, following ~/.claude/templates/project/CLAUDE.md: the real commands with their measured timings, which machine runs them, gotchas and pointers, in under 150 lines and with no overview. If a CLAUDE.md exists, keep it and add only what's missing.
2. .claude/settings.json, following ~/.claude/templates/project/.claude/settings.json. FAST_CHECK is the project's quickest meaningful check (unit tests and lint, under about a minute: time it once); the Stop hook runs it. Use "" if there are no tests yet. FORMAT_RULES maps file globs to the formatter the project already uses, with {{file}} for the edited file; use "" if there is none. If the project uses tests/acceptance, copy ~/.claude/templates/project/.claude/hooks/guard_tests.py to the same path in the repo and keep the PreToolUse hook that runs it, with the Python this machine's hooks use in ~/.claude/settings.json; otherwise leave both out. Merge into an existing settings file without dropping keys.
3. .gitattributes with `* text=auto eol=lf`, unless the repo already has one.
If the owner says not to set this repo up, create an empty .claude/no-auto-setup instead."""

REMINDER = ("Workspace setup: FAST_CHECK in {root}/.claude/settings.json is empty, but the repo now has "
            "tests. Set it to the quickest meaningful check (under about a minute) so the Stop hook can "
            "verify work, and mention it to the owner in one line.")


def repo_root(cwd):
    try:
        run = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    out = run.stdout.strip()
    return Path(out).resolve() if run.returncode == 0 and out else None


def skipped(root):
    home = Path.home().resolve()
    return (root == home or root.is_relative_to(home / ".claude")
            or "scratch-workspaces" in root.parts
            or (root / ".claude" / "no-auto-setup").exists())


def fast_check(root):
    """'missing' when there's no FAST_CHECK key, otherwise 'empty' or 'set'."""
    try:
        settings = json.loads((root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "missing"
    env = settings.get("env") or {}
    if "FAST_CHECK" not in env:
        return "missing"
    return "set" if str(env["FAST_CHECK"]).strip() else "empty"


def has_tests(root):
    try:
        files = subprocess.run(["git", "-C", str(root), "ls-files"],
                               capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.TimeoutExpired):
        return False
    return any(TESTS.search(f) for f in files.splitlines())


def message(cwd):
    root = repo_root(cwd)
    if root is None or skipped(root):
        return None
    state = fast_check(root)
    missing = [name for name, gone in (("CLAUDE.md", not (root / "CLAUDE.md").exists()),
                                       ("FAST_CHECK", state == "missing")) if gone]
    if missing:
        return SETUP.format(root=root, missing=" and ".join(missing) + " missing")
    if state == "empty" and has_tests(root):
        return REMINDER.format(root=root)
    return None


def main():
    data = json.load(sys.stdin)
    text = message(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())
    if text:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}))


if __name__ == "__main__":
    main()
