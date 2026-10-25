"""Tests for the hook scripts. Standard library only, so they run with any Python 3.10+:

    python -m unittest discover -s tests -v

Run from the repo root. The stop-gate tests need git, and bash (Git Bash on Windows); they skip
themselves when either is missing.
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared" / "hooks"))

import guard_deletes  # noqa: E402
import statusline  # noqa: E402
import stop_gate  # noqa: E402


def verdict(command, tool="Bash"):
    return guard_deletes.check(command, tool)[0]


class GuardDeletes(unittest.TestCase):
    def test_reported_windows_wipes_are_denied(self):
        # Shapes of the September and October 2026 incident reports.
        self.assertEqual(verdict(r'rm -rf "\\"'), "deny")
        self.assertEqual(verdict("rm -rf \\"), "deny")
        self.assertEqual(verdict("rm -rf /c/"), "deny")
        self.assertEqual(verdict('rm -rf "C:\\Users\\MIKHA~1"'), "deny")
        self.assertEqual(verdict("cd /tmp && rm -rf ~"), "deny")
        self.assertEqual(verdict("Remove-Item -Recurse -Force C:\\Users\\mikha", "PowerShell"), "deny")
        self.assertEqual(verdict("Remove-Item -LiteralPath $env:USERPROFILE -Recurse", "PowerShell"), "deny")

    def test_roots_and_system_folders_are_denied(self):
        for cmd in ("rm -rf /", "rm -rf /*", "sudo rm -fr /home/mdsilcox", "rm -r -f /etc",
                    "rm -rf /mnt/c", "find / -delete", "rm -rf $HOME", 'rm -rf "$HOME"/*'):
            with self.subTest(cmd=cmd):
                self.assertEqual(verdict(cmd), "deny")

    def test_cmd_style_deletes(self):
        self.assertEqual(verdict("rd /s /q C:\\", "PowerShell"), "deny")
        self.assertIsNone(verdict("rd /s /q build", "PowerShell"))

    def test_possibly_empty_variables_ask(self):
        self.assertEqual(verdict('rm -rf "$SP"/*'), "ask")
        self.assertEqual(verdict("rm -rf $BUILD_DIR"), "ask")
        self.assertEqual(verdict("rm -rf *"), "ask")
        self.assertIsNone(verdict('rm -rf "${BUILD_DIR:?}"/out'))
        self.assertIsNone(verdict("rm -rf $HOME/.cache/pip"))

    def test_ordinary_deletes_pass(self):
        for cmd in ("rm -rf node_modules dist", "rm -rf ./build/*", "rm -rf /tmp/claude-test",
                    "rm file.txt", "rm -f *.log", "git clean -fd", "find . -name '*.pyc' -delete"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(verdict(cmd))
        self.assertEqual(verdict("find . -delete"), "ask")
        self.assertIsNone(verdict("Remove-Item -Recurse .\\build", "PowerShell"))
        self.assertIsNone(verdict("Remove-Item notes.txt", "PowerShell"))

    def test_docker_host_mounts(self):
        self.assertEqual(verdict("docker run --rm -v C:/:/host alpine sh"), "deny")
        self.assertEqual(verdict("docker run -v /:/host alpine"), "deny")
        self.assertEqual(verdict("docker run --mount type=bind,source=/home/mdsilcox,target=/h x"), "deny")
        self.assertIsNone(verdict("docker run -v ./data:/data -p 127.0.0.1:8010:8010 app"))
        self.assertIsNone(verdict("docker compose up -d"))

    def test_hook_output_shape(self):
        stdin = io.StringIO(json.dumps({"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}))
        out = io.StringIO()
        with mock.patch.object(sys, "stdin", stdin), redirect_stdout(out):
            guard_deletes.main()
        decision = json.loads(out.getvalue())["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertEqual(decision["hookEventName"], "PreToolUse")


class StatusLine(unittest.TestCase):
    def test_full_line(self):
        data = {"model": {"display_name": "Opus 5.5"}, "effort": {"level": "high"},
                "context_window": {"used_percentage": 33.6},
                "rate_limits": {"five_hour": {"used_percentage": 12.2},
                                "seven_day": {"used_percentage": 40}}}
        out = io.StringIO()
        with mock.patch.object(sys, "stdin", io.StringIO(json.dumps(data))), redirect_stdout(out):
            statusline.main()
        self.assertEqual(out.getvalue().strip(), "Opus 5.5 high | ctx 34% | 5h 12% | 7d 40%")

    def test_missing_fields(self):
        out = io.StringIO()
        with mock.patch.object(sys, "stdin", io.StringIO(json.dumps({"model": {"display_name": "Sonnet 5.5"}}))), \
                redirect_stdout(out):
            statusline.main()
        self.assertEqual(out.getvalue().strip(), "Sonnet 5.5")


@unittest.skipUnless(shutil.which("git") and stop_gate.find_bash(), "needs git and bash")
class StopGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = Path(self.tmp, "repo")
        self.repo.mkdir()
        for args in (["init", "-q"], ["config", "user.email", "t@example.com"], ["config", "user.name", "t"]):
            subprocess.run(["git", "-C", str(self.repo), *args], check=True)
        (self.repo / "a.txt").write_text("one\n")
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "init"], check=True)
        self.state = mock.patch.object(stop_gate, "STATE_DIR", Path(self.tmp, "state"))
        self.state.start()

    def tearDown(self):
        self.state.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_gate(self, check, active=False):
        env = {"FAST_CHECK": check, "CLAUDE_PROJECT_DIR": str(self.repo)}
        stdin = io.StringIO(json.dumps({"stop_hook_active": active, "cwd": str(self.repo)}))
        out = io.StringIO()
        with mock.patch.dict(os.environ, env), mock.patch.object(sys, "stdin", stdin), redirect_stdout(out):
            stop_gate.main()
        return json.loads(out.getvalue()) if out.getvalue().strip() else None

    def test_clean_tree_skips_the_check(self):
        self.assertIsNone(self.run_gate("exit 1"))

    def test_failure_blocks_once_then_lets_go(self):
        (self.repo / "a.txt").write_text("two\n")
        first = self.run_gate("echo broken test; exit 1")
        assert first is not None
        self.assertEqual(first["decision"], "block")
        self.assertIn("broken test", first["reason"])
        again = self.run_gate("echo broken test; exit 1", active=True)
        assert again is not None
        self.assertNotIn("decision", again)
        self.assertIn("still failing", again["systemMessage"])

    def test_green_check_is_remembered(self):
        (self.repo / "a.txt").write_text("three\n")
        self.assertIsNone(self.run_gate("exit 0"))
        self.assertIsNone(self.run_gate("exit 1"))  # same tree state as the green run: not re-run
        (self.repo / "b.txt").write_text("new file\n")
        blocked = self.run_gate("exit 1")
        assert blocked is not None
        self.assertEqual(blocked["decision"], "block")

    def test_no_fast_check_means_no_op(self):
        (self.repo / "a.txt").write_text("four\n")
        self.assertIsNone(self.run_gate(""))


if __name__ == "__main__":
    unittest.main()
