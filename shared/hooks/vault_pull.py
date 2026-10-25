"""SessionStart hook: fast-forward this machine's clone of the knowledge vault, so a session sees
notes written on the other machine. Silent on success; a failure becomes one line of context.

The vault folder comes from VAULT_DIR in the user settings' "env" block.
"""

import json
import os
import subprocess
from pathlib import Path


def main():
    vault = os.environ.get("VAULT_DIR", "")
    if not vault or not Path(vault, ".git").exists():
        return
    try:
        run = subprocess.run(["git", "-C", vault, "pull", "--ff-only", "--quiet"],
                             capture_output=True, text=True, timeout=15)
        problem = "" if run.returncode == 0 else ((run.stderr or run.stdout).strip().splitlines() or ["?"])[-1]
    except subprocess.TimeoutExpired:
        problem = "timed out after 15 s"
    if problem:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": f"Vault sync: git pull --ff-only failed in {vault} ({problem}). "
                                 "Vault notes may be out of date on this machine.",
        }}))


if __name__ == "__main__":
    main()
