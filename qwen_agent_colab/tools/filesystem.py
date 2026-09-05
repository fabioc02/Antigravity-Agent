from qwen_agent_colab.tools.bridge_client import bridge

def read_file(path: str) -> str:
    """Reads the content of a file."""
    res = bridge.read_file(path)
    if "error" in res: return f"Error: {res['error']}"
    return res["content"]

def write_file(path: str, content: str) -> str:
    """Writes content to a file."""
    res = bridge.write_file(path, content)
    if "error" in res: return f"Error: {res['error']}"
    return "Success"

def list_directory(path: str = ".") -> str:
    """Lists files and directories in the specified path."""
    res = bridge.list_dir(path)
    if "error" in res: return f"Error: {res['error']}"
    files = res.get("files", [])
    return "\n".join([f"{'[DIR] ' if f['isDirectory'] else '[FILE] '}{f['name']}" for f in files])
