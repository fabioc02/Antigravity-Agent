import os
import re
from agent.build.executor import SecureExecutor

class PushBlockedError(Exception):
    pass

class GitHubManager:
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.executor = SecureExecutor(workspace_root)
        self.sensitive_patterns = [
            r'^\.env.*', r'.*secret.*', r'.*token.*', 
            r'.*credential.*', r'.*id_rsa.*', r'.*api_key.*'
        ]

    def _run_git(self, args: list) -> dict:
        return self.executor.run(["git"] + args)

    def check_config(self) -> dict:
        res = self._run_git(["remote", "get-url", "origin"])
        has_remote = res["success"]
        remote_url = res["stdout"].strip() if has_remote else None
        
        return {
            "has_remote": has_remote,
            "remote_url": remote_url
        }

    def set_remote(self, url: str) -> bool:
        res = self._run_git(["remote", "add", "origin", url])
        if not res["success"]:
             res = self._run_git(["remote", "set-url", "origin", url])
        return res["success"]

    def fetch(self) -> bool:
        res = self._run_git(["fetch", "origin"])
        return res["success"]

    def get_status(self) -> dict:
        res = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        branch = res["stdout"].strip() if res["success"] else "unknown"

        ahead = 0
        behind = 0
        res = self._run_git(["rev-list", "--left-right", "--count", f"origin/{branch}...HEAD"])
        if res["success"]:
            parts = res["stdout"].strip().split()
            if len(parts) == 2:
                behind, ahead = int(parts[0]), int(parts[1])
        else:
            # Fallback if origin/branch doesn't exist yet
            res_all = self._run_git(["rev-list", "--count", "HEAD"])
            if res_all["success"]:
                ahead = int(res_all["stdout"].strip())

        res = self._run_git(["status", "--porcelain"])
        working_tree = res["stdout"].strip()
        is_clean = len(working_tree) == 0

        res = self._run_git(["log", "-1", "--oneline"])
        last_commit = res["stdout"].strip() if res["success"] else ""

        return {
            "branch": branch,
            "ahead": ahead,
            "behind": behind,
            "working_tree_clean": is_clean,
            "working_tree_changes": working_tree,
            "last_commit": last_commit
        }

    def check_secrets(self) -> list:
        branch_res = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if not branch_res["success"]: return []
        branch = branch_res["stdout"].strip()

        res = self._run_git(["diff", "--name-only", f"origin/{branch}...HEAD"])
        if not res["success"]:
            res = self._run_git(["ls-tree", "-r", "HEAD", "--name-only"])
            
        files = res["stdout"].strip().split('\n')
        flagged = []
        for f in files:
            if not f: continue
            for pat in self.sensitive_patterns:
                if re.match(pat, os.path.basename(f), re.IGNORECASE):
                    flagged.append(f)
                    break
        return flagged

    def prepare_push(self) -> dict:
        status = self.get_status()
        secrets = self.check_secrets()
        
        diff_res = self._run_git(["diff", "--stat", f"origin/{status['branch']}...HEAD"])
        diff_stat = diff_res["stdout"].strip() if diff_res["success"] else "New branch or no diff."

        return {
            "project": os.path.basename(self.workspace_root),
            "branch": status["branch"],
            "remote": self.check_config().get("remote_url"),
            "last_commit": status["last_commit"],
            "ahead": status["ahead"],
            "behind": status["behind"],
            "working_tree_clean": status["working_tree_clean"],
            "diff_summary": diff_stat,
            "secrets_flagged": secrets,
            "can_push": len(secrets) == 0 and status["ahead"] > 0
        }

    def push(self, authorized: bool = False) -> dict:
        if not authorized:
            raise PushBlockedError("PUSH BLOCKED: Explicit user authorization required.")
        
        secrets = self.check_secrets()
        if secrets:
            raise PushBlockedError(f"PUSH BLOCKED: Sensitive files detected: {', '.join(secrets)}")
            
        branch_res = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        branch = branch_res["stdout"].strip() if branch_res["success"] else "main"

        res = self._run_git(["push", "origin", branch])
        if not res["success"]:
            return {"success": False, "error": res["stderr"]}
        return {"success": True, "output": res["stdout"] + "\n" + res["stderr"]}

    def check_pushed(self) -> bool:
        """Recovery mechanism: checks if local HEAD matches remote HEAD without pushing."""
        branch_res = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if not branch_res["success"]: return False
        branch = branch_res["stdout"].strip()

        local_head_res = self._run_git(["rev-parse", "HEAD"])
        local_head = local_head_res["stdout"].strip()

        remote_head_res = self._run_git(["ls-remote", "origin", branch])
        if not remote_head_res["success"] or not remote_head_res["stdout"]:
            return False
        
        remote_head = remote_head_res["stdout"].split()[0]
        return local_head == remote_head
