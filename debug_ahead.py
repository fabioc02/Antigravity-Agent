from agent.github.manager import GitHubManager
import os

ws_root = "/tmp/workspace_fase_g"
gh = GitHubManager(ws_root)
print("status:", gh.get_status())
print("check_config:", gh.check_config())
