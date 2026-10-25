#!/usr/bin/env python3
"""The optional anti-cheat feed must not block local compatibility inventories."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "np_lookup.py"
spec = importlib.util.spec_from_file_location("bridgeplay_np_lookup", SCRIPT)
lookup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lookup)


class AntiCheatLookupTests(unittest.TestCase):
    def test_feed_failure_does_not_abort_or_retry_for_every_game(self):
        with patch.object(lookup, "_awacy", None), \
                patch.object(lookup, "_get", side_effect=OSError("offline")) as get:
            self.assertEqual((None, []), lookup.awacy(123))
            self.assertEqual((None, []), lookup.awacy(456))
            self.assertEqual(1, get.call_count)

    def test_invalid_feed_is_treated_as_unavailable(self):
        with patch.object(lookup, "_awacy", None), \
                patch.object(lookup, "_get", return_value="not json") as get:
            self.assertEqual((None, []), lookup.awacy(123))
            self.assertEqual(1, get.call_count)

    def test_available_feed_still_supplies_anticheat(self):
        feed = [{"storeIds": {"steam": "123"}, "status": "Denied",
                 "anticheats": ["Easy Anti-Cheat"]}]
        with patch.object(lookup, "_awacy", None), \
                patch.object(lookup, "_get", return_value=json.dumps(feed)) as get:
            self.assertEqual(("Denied", ["Easy Anti-Cheat"]), lookup.awacy(123))
            self.assertEqual((None, []), lookup.awacy(456))
            self.assertEqual(1, get.call_count)


if __name__ == "__main__":
    unittest.main()
