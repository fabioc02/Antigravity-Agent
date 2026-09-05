from qwen_agent_colab.tools.git import git_status, git_commit
print(git_status("project"))
print(git_commit("Fixed syntax error", "project"))
print(git_status("project"))
