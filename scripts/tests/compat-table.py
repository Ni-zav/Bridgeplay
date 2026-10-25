#!/usr/bin/env python3
"""Offline checks for compatibility table totals and Markdown encoding."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "compat-table.py"
spec = importlib.util.spec_from_file_location("bridgeplay_compat_table", SCRIPT)
table = importlib.util.module_from_spec(spec)
spec.loader.exec_module(table)


class CompatTableTests(unittest.TestCase):
    def test_missing_or_null_status_is_untested_everywhere(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "compat").mkdir()
            (root / "compat" / "games.json").write_text(json.dumps([
                {"appid": 2, "name": "Missing status"},
                {"appid": 3, "name": "Null status", "status": None},
                {"appid": 1, "name": "Working", "status": "gold"},
            ]))
            with patch.object(table, "ROOT", str(root)):
                table.main()
            contents = (root / "compat" / "README.md").read_text()
        self.assertIn("gold: 1", contents)
        self.assertIn("untested: 2", contents)
        self.assertIn("| Missing status | 2 | untested |", contents)
        self.assertIn("| Null status | 3 | untested |", contents)
        self.assertLess(contents.index("Working | 1"), contents.index("Missing status | 2"))

    def test_markdown_cells_keep_backslashes_pipes_and_line_breaks_in_one_row(self):
        self.assertEqual(r"path\\\\\|pipe  next", table.cell("path\\|pipe\r\nnext"))
        self.assertEqual("-", table.cell(None))


if __name__ == "__main__":
    unittest.main()
