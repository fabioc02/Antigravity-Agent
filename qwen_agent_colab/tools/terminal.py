import shlex
from qwen_agent_colab.tools.bridge_client import bridge

def execute_command(command: str, cwd: str = ".") -> str:
    """Executes a command. Warning: Do not use shell operators like && or |. Pass clean commands."""
    try:
        parts = shlex.split(command)
    except Exception as e:
        return f"Error parsing command: {e}"
        
    if not parts:
        return "Error: Empty command"
        
    executable = parts[0]
    args = parts[1:]
    
    res = bridge.execute(executable, args, cwd)
    if res.get("error"):
        return f"Error: {res['error']}"
        
    out = []
    out.append(f"Exit Code: {res.get('exitCode')}")
    if res.get("stdout"): out.append(f"STDOUT:\n{res['stdout']}")
    if res.get("stderr"): out.append(f"STDERR:\n{res['stderr']}")
    return "\n".join(out)
