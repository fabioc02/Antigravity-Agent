import os
from qwen_agent_colab.tools.filesystem import list_directory

class ProjectManager:
    def __init__(self, workspace_root: str = "projects"):
        self.workspace_root = workspace_root

    def detect_project_type(self, path: str) -> str:
        files = list_directory(path)
        if "error" in files.lower():
            return "Unknown"
            
        if "build.gradle" in files or "build.gradle.kts" in files:
            return "Android/Kotlin"
        if "CMakeLists.txt" in files:
            return "C/C++ (CMake)"
        if "package.json" in files:
            return "Node.js"
        if "requirements.txt" in files or ".py" in files:
            return "Python"
            
        return "Unknown"
        
    def get_project_context(self, project_name: str) -> str:
        path = f"{self.workspace_root}/{project_name}"
        proj_type = self.detect_project_type(path)
        return f"Project: {project_name}\nType: {proj_type}\nWorkspace: {path}"
