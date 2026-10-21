"""Saving the settings page keeps the settings that live only in job.json.

Writes the test server's settings, so it runs only against a throwaway server
whose work directory is given (never the live one):

    MEA_TEST_URL=http://localhost:8767 MEA_TEST_WORK_DIR=/tmp/x/work \\
        python -m unittest test_api_settings

Start that server with a job.json holding non-default values for
memory_limit_gb, stall_minutes and the like, or the test proves little.
"""
import json
import os
import unittest
from pathlib import Path

from test_api import call, up

WORK = os.environ.get("MEA_TEST_WORK_DIR", "")
HIDDEN = ("memory_limit_gb", "stall_minutes", "max_runtime_hours", "kill_grace_seconds",
          "max_poll_seconds")


@unittest.skipUnless(WORK and up(), "needs MEA_TEST_WORK_DIR and a throwaway test server")
class SettingsSaveTest(unittest.TestCase):
    def test_hidden_settings_survive_a_save(self):
        job = Path(WORK) / "job.json"
        before = json.loads(job.read_text())
        code, cfg, _ = call("/api/config")
        self.assertEqual(code, 200)
        for k in ("env", "work_dir"):
            cfg.pop(k, None)
        code, res, _ = call("/api/config", cfg)
        self.assertEqual(code, 200, res)
        after = json.loads(job.read_text())
        for k in HIDDEN:
            self.assertEqual(after.get(k), before.get(k), k)


if __name__ == "__main__":
    unittest.main()
