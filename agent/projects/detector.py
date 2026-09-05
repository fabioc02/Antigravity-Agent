import os

class ProjectDetector:
    @staticmethod
    def detect(workspace_path: str) -> dict:
        info = {
            "project_type": "unknown",
            "build_system": "none",
            "language": "unknown",
            "framework": "none",
            "test_command": "none"
        }
        
        files = set(os.listdir(workspace_path)) if os.path.exists(workspace_path) else set()
        
        if "package.json" in files:
            info.update({"project_type": "Node.js", "build_system": "npm", "language": "TypeScript/JavaScript", "test_command": "npm test"})
        elif "build.gradle" in files or "build.gradle.kts" in files:
            info.update({"project_type": "Android/Java", "build_system": "gradle", "language": "Java/Kotlin", "test_command": "./gradlew test"})
        elif "CMakeLists.txt" in files:
            info.update({"project_type": "C++", "build_system": "cmake", "language": "C++", "test_command": "ctest"})
        elif "pyproject.toml" in files or "requirements.txt" in files or "setup.py" in files:
            info.update({"project_type": "Python", "build_system": "pip/poetry", "language": "Python", "test_command": "pytest"})
        elif "pom.xml" in files:
            info.update({"project_type": "Java", "build_system": "maven", "language": "Java", "test_command": "mvn test"})
        elif "Cargo.toml" in files:
            info.update({"project_type": "Rust", "build_system": "cargo", "language": "Rust", "test_command": "cargo test"})
            
        return info
