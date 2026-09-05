import subprocess
import shlex
from agent.tools.base import Tool

class TerminalExecuteTool(Tool):
    name = "terminal.execute"
    description = "Execute a shell command"
    permission_level = "EXECUTE"
    
    def execute(self, command: str, cwd: str = ".") -> str:
        try:
            self.sandbox.validate_command(command)
            safe_cwd = self.sandbox.validate_path(cwd)
            parts = shlex.split(command)
            
            result = subprocess.run(parts, cwd=safe_cwd, capture_output=True, text=True, timeout=60)
            
            output = f"Exit Code: {result.returncode}\n"
            if result.stdout: output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr: output += f"STDERR:\n{result.stderr}\n"
            return output
        except Exception as e:
            return f"Error: {e}"
