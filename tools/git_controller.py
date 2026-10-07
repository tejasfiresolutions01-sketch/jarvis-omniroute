"""
J.A.R.V.I.S. Autonomous Git & Codebase Engineering Sentinel.
Enables J.A.R.V.I.S. to inspect repository health, review diffs, examine commit chronology,
and autonomously stage, commit, and push updates across local and remote repositories.
"""

import os
import shutil
import subprocess
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import config

class GitController:
    """
    Stark Engineering Git Custodian.
    Manages version control, status audits, branch transitions, and GitHub pushes.
    """

    CANDIDATE_PATHS = [
        r"C:\Users\venka\AppData\Local\Programs\Git\cmd\git.exe",
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe"
    ]

    def __init__(self, default_cwd: str = "."):
        self.default_cwd = default_cwd
        self.git_bin = self._resolve_git()

    def _resolve_git(self) -> str:
        """Finds valid git executable on system PATH or standard install directories."""
        found = shutil.which("git")
        if found:
            return found
        for cand in self.CANDIDATE_PATHS:
            if os.path.exists(cand):
                return cand
        return "git" # Fallback to system invocation

    def _run_git(self, args: List[str], cwd: Optional[str] = None, timeout: float = 15.0) -> Tuple[int, str, str]:
        """Executes git command with environment protection."""
        target_cwd = cwd or self.default_cwd
        env = os.environ.copy()
        # Guarantee Git bin directory is on PATH
        git_dir = os.path.dirname(self.git_bin)
        if git_dir and git_dir not in env.get("PATH", ""):
            env["PATH"] = f"{git_dir};{env.get('PATH', '')}"

        try:
            res = subprocess.run(
                [self.git_bin] + args,
                cwd=target_cwd,
                capture_output=True,
                text=True,
                env=env,
                timeout=timeout
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", "Git execution timed out after 15 seconds."
        except Exception as e:
            return -1, "", str(e)

    def is_git_repo(self, cwd: Optional[str] = None) -> bool:
        """Checks if current directory is inside a valid git repository."""
        code, out, _ = self._run_git(["rev-parse", "--is-inside-work-tree"], cwd=cwd)
        return code == 0 and out.lower() == "true"

    def get_status(self, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Audits current git status and file modifications."""
        if not self.is_git_repo(cwd):
            return {"is_repo": False, "error": "Not a Git repository."}

        # Current branch
        code_b, branch, _ = self._run_git(["branch", "--show-current"], cwd=cwd)
        branch_name = branch if code_b == 0 and branch else "HEAD (detached)"

        # Porcelain status
        code_s, status_out, _ = self._run_git(["status", "--porcelain"], cwd=cwd)
        
        staged = []
        modified = []
        untracked = []

        if status_out:
            for line in status_out.splitlines():
                if len(line) < 3:
                    continue
                code_xy = line[:2]
                filename = line[3:].strip()
                if code_xy.startswith("?"):
                    untracked.append(filename)
                elif code_xy[0] in ["M", "A", "D", "R", "C"]:
                    staged.append(filename)
                if code_xy[1] in ["M", "D"]:
                    modified.append(filename)

        is_clean = len(staged) == 0 and len(modified) == 0 and len(untracked) == 0

        return {
            "is_repo": True,
            "branch": branch_name,
            "is_clean": is_clean,
            "staged_count": len(staged),
            "modified_count": len(modified),
            "untracked_count": len(untracked),
            "staged": staged,
            "modified": modified,
            "untracked": untracked
        }

    def format_status_summary(self, cwd: Optional[str] = None) -> str:
        """Generates an articulate butler summary of working repository status."""
        status = self.get_status(cwd)
        if not status.get("is_repo"):
            return "Current workspace is not recognized as a Git repository, sir."

        branch = status["branch"]
        if status["is_clean"]:
            return (
                f"Repository diagnostics are spotless, sir. Active on branch '{branch}', "
                f"working tree is clean, and all changes are committed."
            )

        details = []
        if status["staged_count"] > 0:
            details.append(f"{status['staged_count']} staged for commit")
        if status["modified_count"] > 0:
            details.append(f"{status['modified_count']} modified")
        if status["untracked_count"] > 0:
            details.append(f"{status['untracked_count']} untracked")

        changes_summary = ", ".join(details)
        return (
            f"Repository status for branch '{branch}', sir: {changes_summary}. "
            f"Would you like me to stage and commit these changes?"
        )

    def get_recent_commits(self, limit: int = 5, cwd: Optional[str] = None) -> List[Dict[str, str]]:
        """Extracts recent commit chronology."""
        code, out, _ = self._run_git(["log", f"-n{limit}", "--pretty=format:%h|%an|%ar|%s"], cwd=cwd)
        commits = []
        if code == 0 and out:
            for line in out.splitlines():
                parts = line.split("|", 3)
                if len(parts) == 4:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "time": parts[2],
                        "subject": parts[3]
                    })
        return commits

    def format_log_summary(self, limit: int = 5, cwd: Optional[str] = None) -> str:
        """Formats recent commit history into butler prose."""
        commits = self.get_recent_commits(limit, cwd=cwd)
        if not commits:
            return "No previous commit history located in this repository, sir."

        lines = [f"Chronology of the last {len(commits)} commits, sir:"]
        for c in commits:
            lines.append(f"- [{c['hash']}] ({c['time']}): {c['subject']}")
        return "\n".join(lines)

    def get_diff_summary(self, cwd: Optional[str] = None) -> str:
        """Returns statistics on pending uncommitted diffs."""
        code, out, _ = self._run_git(["diff", "--stat"], cwd=cwd)
        if code != 0 or not out:
            return "No pending uncommitted differences detected in the working tree, sir."
        return f"Pending repository differences, sir:\n{out}"

    def commit_and_push(self, message: str, add_all: bool = True, cwd: Optional[str] = None) -> Tuple[bool, str]:
        """
        Stages all changes, creates a commit with the specified message,
        and pushes to the remote upstream branch.
        """
        clean_msg = message.strip()
        if not clean_msg:
            return False, "Commit directive aborted, sir. A commit message is required."

        status = self.get_status(cwd)
        if status.get("is_clean"):
            return True, "Working tree is already completely clean, sir. There are no changes to commit."

        # 1. Stage changes
        if add_all:
            code_a, _, err_a = self._run_git(["add", "-A"], cwd=cwd)
            if code_a != 0:
                return False, f"Failed to stage changes, sir: {err_a}"

        # 2. Commit
        code_c, out_c, err_c = self._run_git(["commit", "-m", clean_msg], cwd=cwd)
        if code_c != 0:
            return False, f"Commit operation encountered an anomaly, sir: {err_c or out_c}"

        branch = status.get("branch", "main")

        # 3. Push to remote
        code_p, out_p, err_p = self._run_git(["push", "origin", branch], cwd=cwd)
        if code_p != 0:
            # Commit succeeded locally but push failed
            return True, (
                f"Changes committed locally with message '{clean_msg}', sir. "
                f"However, remote push to origin/{branch} encountered a notice: {err_p or out_p}"
            )

        return True, (
            f"Changes committed with message '{clean_msg}' and pushed cleanly "
            f"to origin/{branch}, sir. Repository is fully synchronized."
        )

    def create_or_switch_branch(self, branch_name: str, create: bool = False, cwd: Optional[str] = None) -> Tuple[bool, str]:
        """Creates or switches to a specified branch."""
        clean_name = branch_name.strip()
        if not clean_name:
            return False, "Branch name is required, sir."

        args = ["checkout", "-b", clean_name] if create else ["checkout", clean_name]
        code, out, err = self._run_git(args, cwd=cwd)
        if code == 0:
            verb = "created and activated" if create else "activated"
            return True, f"Branch '{clean_name}' successfully {verb}, sir."
        return False, f"Branch operation encountered an anomaly: {err or out}"

# Global singleton
git_controller = GitController()
