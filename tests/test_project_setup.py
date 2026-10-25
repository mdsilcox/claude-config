"""Tests for project_setup: when a new session gets told to set the repo up.

    python -m unittest discover -s tests -v
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared" / "hooks"))

import project_setup  # noqa: E402


@unittest.skipUnless(shutil.which("git"), "needs git")
class ProjectSetup(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "app"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def settings(self, env):
        (self.repo / ".claude").mkdir(exist_ok=True)
        (self.repo / ".claude" / "settings.json").write_text(json.dumps({"env": env}))

    def track(self, name):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n")
        subprocess.run(["git", "-C", str(self.repo), "add", name], check=True)

    def test_new_repo_gets_the_setup_message(self):
        text = project_setup.message(str(self.repo))
        assert text is not None
        self.assertIn("CLAUDE.md and FAST_CHECK missing", text)
        self.assertIn("{file}", text)  # the literal placeholder survives formatting

    def test_existing_claude_md_without_fast_check(self):
        (self.repo / "CLAUDE.md").write_text("# app\n")
        text = project_setup.message(str(self.repo))
        assert text is not None
        self.assertIn("(FAST_CHECK missing)", text)

    def test_set_up_repo_is_quiet(self):
        (self.repo / "CLAUDE.md").write_text("# app\n")
        self.settings({"FAST_CHECK": "pytest -q", "FORMAT_RULES": ""})
        self.assertIsNone(project_setup.message(str(self.repo)))

    def test_empty_fast_check_reminds_only_once_tests_exist(self):
        (self.repo / "CLAUDE.md").write_text("# app\n")
        self.settings({"FAST_CHECK": ""})
        self.assertIsNone(project_setup.message(str(self.repo)))
        self.track("tests/test_app.py")
        text = project_setup.message(str(self.repo))
        assert text is not None
        self.assertIn("FAST_CHECK", text)
        self.assertIn("is empty", text)

    def test_test_file_patterns(self):
        for name in ("tests/x.py", "src/test_parser.py", "pkg/parse_test.go", "web/app.test.ts",
                     "web/ui.spec.jsx"):
            with self.subTest(name=name):
                self.assertTrue(project_setup.TESTS.search(name))
        for name in ("src/latest.py", "contest.md", "attestation.ts"):
            with self.subTest(name=name):
                self.assertFalse(project_setup.TESTS.search(name))

    def test_opt_out_and_non_repos_are_skipped(self):
        self.assertIsNone(project_setup.message(str(self.tmp)))  # not a git repo
        (self.repo / ".claude").mkdir()
        (self.repo / ".claude" / "no-auto-setup").write_text("")
        self.assertIsNone(project_setup.message(str(self.repo)))

    def test_scratch_workspaces_are_skipped(self):
        scratch = self.tmp / "scratch-workspaces" / "s1"
        scratch.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(scratch)], check=True)
        self.assertIsNone(project_setup.message(str(scratch)))


if __name__ == "__main__":
    unittest.main()
