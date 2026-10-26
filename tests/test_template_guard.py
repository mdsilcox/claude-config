"""The project template guards acceptance tests with the draft-aware hook, not a blanket deny (owner, 2026-10-26).

A test or fixture in main's tree is locked; one not on main yet is a draft and stays editable; when git can't
tell, it counts as locked.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "project" / ".claude"
HOOK = TEMPLATE / "hooks" / "guard_tests.py"


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def put(repo, rel):
    path = Path(repo) / "tests" / "acceptance" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x\n", "utf-8")
    return path


def run_hook(path):
    payload = {"tool_name": "Edit", "tool_input": {"file_path": str(path)}, "cwd": str(path.parent)}
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), text=True,
                          capture_output=True).returncode


class TemplateSettings(unittest.TestCase):
    def test_settings_run_the_guard_instead_of_denying_edits(self):
        settings = json.loads((TEMPLATE / "settings.json").read_text("utf-8"))
        deny = settings.get("permissions", {}).get("deny", [])
        self.assertFalse([rule for rule in deny if "tests/acceptance" in rule])
        commands = [hook["command"] for entry in settings["hooks"]["PreToolUse"] for hook in entry["hooks"]]
        self.assertTrue(any("guard_tests.py" in command for command in commands))


@unittest.skipIf(shutil.which("git") is None, "needs git")
class TemplateGuard(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)

    def init_main(self):
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "t@example.invalid")
        git(self.repo, "config", "user.name", "t")
        put(self.repo, "test_merged.py")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-q", "-m", "main")

    def test_a_test_on_main_is_locked(self):
        self.init_main()
        self.assertEqual(run_hook(self.repo / "tests" / "acceptance" / "test_merged.py"), 2)

    def test_a_test_not_on_main_is_a_draft(self):
        self.init_main()
        self.assertEqual(run_hook(put(self.repo, "test_draft.py")), 0)

    def test_outside_a_repository_a_test_is_locked(self):
        self.assertEqual(run_hook(put(self.repo, "test_loose.py")), 2)


if __name__ == "__main__":
    unittest.main()
