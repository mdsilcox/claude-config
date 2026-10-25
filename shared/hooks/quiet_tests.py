"""Trim pytest output to what matters: failures, errors and the summary.

Reads a test run's combined output on stdin. If it is pytest output, it drops the progress lines
(rows of dots and percentages) and passing chatter, keeps the FAILURES and ERRORS sections (capped),
the short summary and the final count line. Anything that isn't pytest output passes through as is.
Used by quiet_tests_hook.py; the exit code comes from the test command itself (pipefail), not this.
"""

import re
import sys

MAX_DETAIL_LINES = 160  # traceback lines kept from the FAILURES/ERRORS sections

PROGRESS = re.compile(r"^\S*\s*[.FEsxX]+\s*(\[\s*\d+%\])?\s*$")
SECTION = re.compile(r"^=+ (.+?) =+$")
FINAL = re.compile(r"^=*\s*(\d+ (passed|failed|error|errors|skipped|xfailed|xpassed|deselected|warnings?)\b.*?)\s*=*$")


def main():
    text = sys.stdin.read()
    lines = text.splitlines()
    if not any(FINAL.match(x.strip()) for x in lines[-5:]) and "short test summary info" not in text:
        sys.stdout.write(text)  # not pytest output: leave it alone
        return
    out, detail, kept, section = [], [], 0, None
    for line in lines:
        m = SECTION.match(line.strip())
        if m:
            section = m.group(1).lower()
            if section in ("failures", "errors", "short test summary info"):
                (detail if section != "short test summary info" else out).append(line)
            continue
        if section in ("failures", "errors"):
            if kept < MAX_DETAIL_LINES:
                detail.append(line)
            kept += 1
        elif section == "short test summary info":
            out.append(line)
        elif FINAL.match(line.strip()):
            out.append(line)
        elif PROGRESS.match(line) or section in ("warnings summary", "test session starts"):
            continue
        elif line.strip().startswith(("ERROR ", "FAILED ", "ImportError", "ModuleNotFoundError", "SyntaxError")):
            out.append(line)
    if kept > MAX_DETAIL_LINES:
        detail.append(f"... {kept - MAX_DETAIL_LINES} more traceback lines trimmed (rerun the failing test alone for all of it)")
    result = detail + out if detail else out
    sys.stdout.write("\n".join(result or lines[-3:]) + "\n")


if __name__ == "__main__":
    main()
