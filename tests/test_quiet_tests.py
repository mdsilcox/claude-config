"""Tests for quiet_tests_hook: which commands get their pytest output trimmed.

    python -m unittest discover -s tests -v
"""

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared" / "hooks"))

import quiet_tests_hook  # noqa: E402


def rewritten(command):
    stdin = io.StringIO(json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}))
    out = io.StringIO()
    with mock.patch.object(sys, "stdin", stdin), redirect_stdout(out):
        quiet_tests_hook.main()
    result = json.loads(out.getvalue())
    return result.get("hookSpecificOutput", {}).get("updatedInput", {}).get("command")


class QuietTests(unittest.TestCase):
    def test_plain_pytest_runs_are_trimmed(self):
        for cmd in ("pytest", "pytest tests/unit -q -x", "python -m pytest -q",
                    "uv run pytest -q", "uv run --python 3.12 pytest tests", "uv run python -m pytest",
                    "PYTHONUTF8=1 uv run pytest -k parser"):
            with self.subTest(cmd=cmd):
                wrapped = rewritten(cmd)
                self.assertIsNotNone(wrapped)
                assert wrapped is not None
                self.assertTrue(wrapped.startswith("set -o pipefail; "))
                self.assertIn("quiet_tests.py", wrapped)

    def test_everything_else_passes_untouched(self):
        for cmd in ("uv run ruff check .", "pytest | tee log.txt", "pytest && git commit -am x",
                    "pytest > out.txt", "pytest  # full-output", "npm test", "uv run app.py"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(rewritten(cmd))


if __name__ == "__main__":
    unittest.main()
