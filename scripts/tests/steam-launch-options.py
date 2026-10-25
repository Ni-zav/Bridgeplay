#!/usr/bin/env python3
"""Offline file-preservation checks for Steam launch-option editing."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "steam-launch-options.py"
APPS = ('\t' * 4 + '"apps"\n'
        + '\t' * 5 + '"101"\n'
        + '\t' * 5 + '{\n'
        + '\t' * 6 + '"LaunchOptions"\t\t"VAR=1 %command%"\n'
        + '\t' * 5 + '}\n')


class SteamLaunchOptionsTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.path = Path(self.work.name) / "localconfig.vdf"
        self.path.write_bytes(APPS.replace("\n", "\r\n").encode())

    def run_editor(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.path), *args],
            capture_output=True, text=True, check=False,
        )

    def test_unknown_app_does_not_rewrite_file(self):
        before = self.path.read_bytes()
        self.assertEqual(0, self.run_editor("BRIDGEPLAY_X=1", "999").returncode)
        self.assertEqual(before, self.path.read_bytes())

    def test_existing_token_preserves_file(self):
        before = self.path.read_bytes()
        self.assertEqual(0, self.run_editor("VAR=1", "101").returncode)
        self.assertEqual(before, self.path.read_bytes())

    def test_edit_preserves_crlf_and_is_idempotent(self):
        self.assertEqual(0, self.run_editor("BRIDGEPLAY_X=1", "101").returncode)
        result = self.path.read_bytes()
        self.assertIn(b'BRIDGEPLAY_X=1 VAR=1 %command%', result)
        self.assertIn(b"\r\n", result)
        self.assertNotIn(b"\n", result.replace(b"\r\n", b""))
        self.assertEqual(0, self.run_editor("BRIDGEPLAY_X=1", "101").returncode)
        self.assertEqual(result, self.path.read_bytes())

    def test_unterminated_app_block_is_left_untouched(self):
        self.path.write_bytes(APPS[:-3].encode())
        before = self.path.read_bytes()
        self.assertNotEqual(0, self.run_editor("BRIDGEPLAY_X=1", "101").returncode)
        self.assertEqual(before, self.path.read_bytes())

    def test_bad_arguments_do_not_write(self):
        before = self.path.read_bytes()
        self.assertNotEqual(0, self.run_editor("BRIDGEPLAY_X=1", "not-an-id").returncode)
        self.assertNotEqual(0, self.run_editor().returncode)
        self.assertEqual(before, self.path.read_bytes())


if __name__ == "__main__":
    unittest.main()
