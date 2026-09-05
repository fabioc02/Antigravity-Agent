import os
import uuid
import time
import json
from typing import List, Dict, Optional
from agent.core.utils import atomic_write_json
from agent.projects.detector import ProjectDetector

class ProjectManager:
    def __init__(self, drive_root: str):
        self.drive_root = os.path.abspath(drive_root)
        self.projects_dir = os.path.join(self.drive_root, "projects")
        os.makedirs(self.projects_dir, exist_ok=True)

    def create_project(self, name: str, project_type: str = "unknown") -> str:
        project_id = str(uuid.uuid4())
        pdir = os.path.join(self.projects_dir, project_id)
        os.makedirs(pdir, exist_ok=True)
        os.makedirs(os.path.join(pdir, "source"), exist_ok=True)
        os.makedirs(os.path.join(pdir, "checkpoints"), exist_ok=True)
        os.makedirs(os.path.join(pdir, "tasks"), exist_ok=True)
        os.makedirs(os.path.join(pdir, "memory"), exist_ok=True)
        
        meta = {
            "project_id": project_id,
            "name": name,
            "type": project_type,
            "created_at": time.time(),
            "updated_at": time.time(),
            "active": True
        }
        atomic_write_json(meta, os.path.join(pdir, "project.json"))
        return project_id

    def list_projects(self) -> List[Dict]:
        projects = []
        for pid in os.listdir(self.projects_dir):
            ppath = os.path.join(self.projects_dir, pid, "project.json")
            if os.path.exists(ppath):
                with open(ppath, "r") as f:
                    projects.append(json.load(f))
        return projects

    def get_project(self, project_id: str) -> Optional[Dict]:
        ppath = os.path.join(self.projects_dir, project_id, "project.json")
        if os.path.exists(ppath):
            with open(ppath, "r") as f:
                return json.load(f)
        return None

    def detect_project(self, project_id: str, local_workspace_root: str) -> dict:
        local_dir = os.path.join(local_workspace_root, project_id)
        return ProjectDetector.detect(local_dir)


class TaskManager:
    def __init__(self, drive_root: str):
        self.drive_root = os.path.abspath(drive_root)
        self.projects_dir = os.path.join(self.drive_root, "projects")

    def create_task(self, project_id: str, title: str, description: str) -> str:
        task_id = str(uuid.uuid4())
        tdir = os.path.join(self.projects_dir, project_id, "tasks", task_id)
        os.makedirs(tdir, exist_ok=True)
        
        task = {
            "task_id": task_id,
            "project_id": project_id,
            "title": title,
            "description": description,
            "status": "PENDING",
            "priority": "normal",
            "created_at": time.time(),
            "updated_at": time.time(),
            "session_id": None,
            "runtime_id": None,
            "iteration": 0
        }
        atomic_write_json(task, os.path.join(tdir, "task.json"))
        return task_id

    def get_task(self, project_id: str, task_id: str) -> Optional[Dict]:
        tpath = os.path.join(self.projects_dir, project_id, "tasks", task_id, "task.json")
        if os.path.exists(tpath):
            with open(tpath, "r") as f:
                return json.load(f)
        return None

    def update_task_status(self, project_id: str, task_id: str, status: str, session_id: str = None, iteration: int = None):
        task = self.get_task(project_id, task_id)
        if task:
            task["status"] = status
            task["updated_at"] = time.time()
            if session_id: task["session_id"] = session_id
            if iteration is not None: task["iteration"] = iteration
            atomic_write_json(task, os.path.join(self.projects_dir, project_id, "tasks", task_id, "task.json"))

    def list_tasks(self, project_id: str) -> List[Dict]:
        tasks = []
        tdir = os.path.join(self.projects_dir, project_id, "tasks")
        if os.path.exists(tdir):
            for tid in os.listdir(tdir):
                tpath = os.path.join(tdir, tid, "task.json")
                if os.path.exists(tpath):
                    with open(tpath, "r") as f:
                        tasks.append(json.load(f))
        return tasks
