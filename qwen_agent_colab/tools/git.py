from qwen_agent_colab.tools.terminal import execute_command

def git_status(cwd: str = ".") -> str:
    """Returns the current git status."""
    return execute_command("git status", cwd)

def git_commit(message: str, cwd: str = ".") -> str:
    """Commits all tracked and modified files."""
    execute_command("git add .", cwd)
    return execute_command(f"git commit -m '{message}'", cwd)
