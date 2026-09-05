import os
import shutil
from agent.tools.base import Tool

class ListDirectoryTool(Tool):
    name = "filesystem.list"
    description = "List files in a directory"
    permission_level = "READ"
    
    def execute(self, path: str = ".") -> str:
        safe_path = self.sandbox.validate_path(path)
        try:
            return "\n".join(os.listdir(safe_path))
        except Exception as e:
            return f"Error: {e}"

class ReadFileTool(Tool):
    name = "filesystem.read"
    description = "Read a file"
    permission_level = "READ"
    
    def execute(self, path: str) -> str:
        safe_path = self.sandbox.validate_path(path)
        try:
            with open(safe_path, "r") as f: return f.read()
        except Exception as e:
            return f"Error: {e}"

class WriteFileTool(Tool):
    name = "filesystem.write"
    description = "Write content to a file"
    permission_level = "WRITE"
    
    def execute(self, path: str, content: str) -> str:
        safe_path = self.sandbox.validate_path(path)
        try:
            os.makedirs(os.path.dirname(safe_path), exist_ok=True)
            with open(safe_path, "w") as f: f.write(content)
            return f"Successfully wrote {len(content)} bytes to {path}"
        except Exception as e:
            return f"Error: {e}"
