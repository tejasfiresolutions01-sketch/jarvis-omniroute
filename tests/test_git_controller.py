"""
Unit tests for J.A.R.V.I.S. Autonomous Git & Codebase Engineering Sentinel.
"""

import unittest
from unittest.mock import patch, MagicMock
from tools.git_controller import GitController

class TestGitController(unittest.TestCase):

    def setUp(self):
        self.git = GitController()

    @patch.object(GitController, "_run_git")
    def test_is_git_repo(self, mock_run):
        mock_run.return_value = (0, "true", "")
        self.assertTrue(self.git.is_git_repo())

        mock_run.return_value = (128, "", "fatal: not a git repository")
        self.assertFalse(self.git.is_git_repo())

    @patch.object(GitController, "_run_git")
    def test_get_status_clean(self, mock_run):
        # 1. rev-parse, 2. branch, 3. status
        mock_run.side_effect = [
            (0, "true", ""),
            (0, "main", ""),
            (0, "", "")
        ]
        status = self.git.get_status()
        self.assertTrue(status["is_repo"])
        self.assertEqual(status["branch"], "main")
        self.assertTrue(status["is_clean"])
        self.assertEqual(status["modified_count"], 0)

    @patch.object(GitController, "_run_git")
    def test_get_status_dirty(self, mock_run):
        mock_run.side_effect = [
            (0, "true", ""),
            (0, "feature/sensors", ""),
            (0, " M core/brain.py\n?? new_tool.py", "")
        ]
        status = self.git.get_status()
        self.assertFalse(status["is_clean"])
        self.assertEqual(status["modified_count"], 1)
        self.assertEqual(status["untracked_count"], 1)

    @patch.object(GitController, "_run_git")
    def test_get_recent_commits(self, mock_run):
        sample_log = (
            "7998fb4|Tony Stark|5 minutes ago|feat: local LAN perimeter scanner\n"
            "016998d|Tony Stark|15 minutes ago|feat: semantic vector memory"
        )
        mock_run.return_value = (0, sample_log, "")
        commits = self.git.get_recent_commits(limit=2)
        self.assertEqual(len(commits), 2)
        self.assertEqual(commits[0]["hash"], "7998fb4")
        self.assertEqual(commits[0]["subject"], "feat: local LAN perimeter scanner")

    @patch.object(GitController, "_run_git")
    def test_get_diff_summary(self, mock_run):
        mock_run.return_value = (0, " core/brain.py | 5 +----\n 1 file changed, 1 insertion(+), 4 deletions(-)", "")
        summary = self.git.get_diff_summary()
        self.assertIn("Pending repository differences", summary)
        self.assertIn("core/brain.py", summary)

    @patch.object(GitController, "_run_git")
    def test_commit_and_push_already_clean(self, mock_run):
        mock_run.side_effect = [
            (0, "true", ""),
            (0, "main", ""),
            (0, "", "")
        ]
        ok, msg = self.git.commit_and_push("test commit")
        self.assertTrue(ok)
        self.assertIn("already completely clean", msg)


if __name__ == "__main__":
    unittest.main()
