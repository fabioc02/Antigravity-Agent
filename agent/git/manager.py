import subprocess
import os
from typing import Optional

class GitManager:
    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)

    def _run(self, cmd: list) -> subprocess.CompletedProcess:
        return subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)

    def init(self):
        if not os.path.exists(os.path.join(self.repo_path, ".git")):
            self._run(["git", "init"])
            self._run(["git", "config", "user.name", "Antigravity Agent"])
            self._run(["git", "config", "user.email", "agent@local.system"])
            self._run(["git", "add", "."])
            self._run(["git", "commit", "--allow-empty", "-m", "Initial commit from AgentCore"])

    def diff(self) -> str:
        # Get diff of tracked AND untracked files
        self._run(["git", "add", "-N", "."]) 
        res = self._run(["git", "diff"])
        return res.stdout.strip()

    def commit(self, message: str) -> bool:
        self._run(["git", "add", "."])
        res = self._run(["git", "commit", "--allow-empty", "-m", message])
        return res.returncode == 0

    def rollback(self):
        self._run(["git", "restore", "."])
        self._run(["git", "clean", "-fd"])
        
    def get_last_commit_msg(self) -> str:
        res = self._run(["git", "log", "-1", "--pretty=%B"])
        return res.stdout.strip()
