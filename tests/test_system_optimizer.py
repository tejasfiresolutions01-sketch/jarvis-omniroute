"""
Unit tests for J.A.R.V.I.S. Autonomous System Optimizer & Hardware Janitor.
"""

import os
import time
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from collections import namedtuple
from tools.system_optimizer import SystemOptimizer

VMem = namedtuple("VMem", ["used", "percent"])

class TestSystemOptimizer(unittest.TestCase):

    def setUp(self):
        self.optimizer = SystemOptimizer()

    @patch("psutil.virtual_memory")
    def test_flush_memory(self, mock_vmem):
        # 8 GB before (8388608000 bytes), 7.5 GB after (7864320000 bytes)
        mock_vmem.side_effect = [
            VMem(used=8388608000, percent=65.0),
            VMem(used=7864320000, percent=61.0)
        ]

        with patch.object(self.optimizer._kernel32, "SetProcessWorkingSetSize", return_value=True):
            res = self.optimizer.flush_memory()

        self.assertIn("ram_freed_mb", res)
        self.assertGreater(res["ram_freed_mb"], 400.0)
        self.assertEqual(res["percent_before"], 65.0)
        self.assertEqual(res["percent_after"], 61.0)

    def test_clean_temp_cache(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            old_file = os.path.join(tmp_dir, "old_cache_data.tmp")
            new_file = os.path.join(tmp_dir, "active_session.tmp")

            with open(old_file, "wb") as f:
                f.write(b"X" * 1024 * 1024) # 1 MB
            with open(new_file, "wb") as f:
                f.write(b"Y" * 1024)

            # Set old_file modified time to 5 hours ago
            five_hours_ago = time.time() - (5 * 3600)
            os.utime(old_file, (five_hours_ago, five_hours_ago))

            with patch.dict(os.environ, {"TEMP": tmp_dir}):
                res = self.optimizer.clean_temp_cache(max_age_hours=2.0)

            self.assertEqual(res["files_deleted"], 1)
            self.assertAlmostEqual(res["space_freed_mb"], 1.0, places=1)
            self.assertFalse(os.path.exists(old_file))
            self.assertTrue(os.path.exists(new_file))

    @patch("psutil.process_iter")
    def test_get_top_processes(self, mock_process_iter):
        proc1 = MagicMock()
        proc1.info = {'pid': 101, 'name': 'chrome.exe', 'cpu_percent': 3.5, 'memory_info': MagicMock(rss=1024 * 1024 * 800)}
        proc2 = MagicMock()
        proc2.info = {'pid': 102, 'name': 'code.exe', 'cpu_percent': 1.2, 'memory_info': MagicMock(rss=1024 * 1024 * 1200)}
        proc3 = MagicMock()
        proc3.info = {'pid': 103, 'name': 'spotify.exe', 'cpu_percent': 0.5, 'memory_info': MagicMock(rss=1024 * 1024 * 300)}

        mock_process_iter.return_value = [proc1, proc2, proc3]

        top = self.optimizer.get_top_processes(limit=2)
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0]["name"], "code.exe")
        self.assertEqual(top[1]["name"], "chrome.exe")
        self.assertAlmostEqual(top[0]["memory_mb"], 1200.0, places=1)

    @patch.object(SystemOptimizer, "get_top_processes")
    def test_format_top_processes_summary(self, mock_top):
        mock_top.return_value = [
            {"pid": 4200, "name": "pycharm64.exe", "memory_mb": 1450.5, "cpu_percent": 4.0},
            {"pid": 1120, "name": "chrome.exe", "memory_mb": 820.0, "cpu_percent": 2.0}
        ]
        summary = self.optimizer.format_top_processes_summary(limit=2)
        self.assertIn("Top 2 resource-consuming processes", summary)
        self.assertIn("pycharm64.exe (PID: 4200): 1450.5 MB RAM", summary)
        self.assertIn("chrome.exe", summary)

    @patch.object(SystemOptimizer, "flush_memory", return_value={"ram_freed_mb": 250.0, "percent_after": 48.0})
    @patch.object(SystemOptimizer, "clean_temp_cache", return_value={"files_deleted": 14, "space_freed_mb": 112.5})
    def test_optimize_all(self, mock_clean, mock_flush):
        report = self.optimizer.optimize_all()
        self.assertIn("Workstation optimization complete, sir", report)
        self.assertIn("14 stale cache files", report)
        self.assertIn("112.5 MB of storage", report)
        self.assertIn("48.0%", report)

if __name__ == "__main__":
    unittest.main()
