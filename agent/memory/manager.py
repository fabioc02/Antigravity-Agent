import os
import time
import json
from typing import List, Dict

class MemoryManager:
    def __init__(self, drive_root: str):
        self.drive_root = os.path.abspath(drive_root)
        self.global_mem_dir = os.path.join(self.drive_root, "memory", "global")
        os.makedirs(self.global_mem_dir, exist_ok=True)

    def _get_path(self, level: str, project_id: str = None, task_id: str = None) -> str:
        if level == "global":
            return os.path.join(self.global_mem_dir, "memory.jsonl")
        elif level == "project" and project_id:
            d = os.path.join(self.drive_root, "projects", project_id, "memory")
            os.makedirs(d, exist_ok=True)
            return os.path.join(d, "memory.jsonl")
        elif level == "task" and project_id and task_id:
            d = os.path.join(self.drive_root, "projects", project_id, "tasks", task_id)
            os.makedirs(d, exist_ok=True)
            return os.path.join(d, "memory.jsonl")
        raise ValueError("Invalid memory level or missing IDs")

    def append(self, level: str, content: str, project_id: str = None, task_id: str = None):
        path = self._get_path(level, project_id, task_id)
        entry = {"timestamp": time.time(), "content": content}
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def read(self, level: str, project_id: str = None, task_id: str = None) -> List[Dict]:
        path = self._get_path(level, project_id, task_id)
        memories = []
        if os.path.exists(path):
            with open(path, "r") as f:
                for line in f:
                    if line.strip():
                        memories.append(json.loads(line))
        return memories
