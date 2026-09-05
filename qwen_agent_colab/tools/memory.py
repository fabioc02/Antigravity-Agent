from qwen_agent_colab.tools.filesystem import read_file, write_file

def read_memory(file_name: str, cwd: str = ".") -> str:
    """Reads a memory file (e.g., SESSION.md)."""
    return read_file(f"{cwd}/.ai/{file_name}")

def update_memory(file_name: str, content: str, cwd: str = ".") -> str:
    """Updates a memory file (e.g., SESSION.md)."""
    return write_file(f"{cwd}/.ai/{file_name}", content)
