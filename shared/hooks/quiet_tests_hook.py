"""PreToolUse hook (Bash): route a plain pytest run through quiet_tests.py so only failures and the
summary reach the model. Follows the pattern in Claude Code's cost docs.

Only a command that is nothing but a pytest run is rewritten: optional VAR=value prefixes, then
`pytest ...` or `<python> -m pytest ...`, with no ; & | < > ` $( or newlines. Because the rewrite
returns permissionDecision "allow", anything more complex passes through untouched and goes through
the normal permission check. Opt out of filtering for one run by adding "# full-output".
"""

import json
import os
import re
import sys

FILTER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quiet_tests.py").replace("\\", "/")
PYTHON = sys.executable.replace("\\", "/")  # the hook's own interpreter: works on Windows and Linux
PLAIN_PYTEST = re.compile(
    r"^\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"           # optional env assignments
    r"(?:pytest|\S*python[0-9.]*(?:\.exe)?\s+-m\s+pytest)"  # pytest, or <python> -m pytest
    r"(?:\s+[^;&|<>`$\n]*)?\s*$"                          # arguments, nothing that chains or redirects
)


def main():
    data = json.load(sys.stdin)
    tool_input = data.get("tool_input") or {}
    cmd = tool_input.get("command", "")
    if "full-output" in cmd or "quiet_tests" in cmd or not PLAIN_PYTEST.match(cmd):
        print("{}")
        return
    wrapped = f'set -o pipefail; {cmd.strip()} 2>&1 | "{PYTHON}" "{FILTER}"'
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": "plain pytest run, output trimmed to failures and summary",
        "updatedInput": {**tool_input, "command": wrapped},
    }}))


if __name__ == "__main__":
    main()
