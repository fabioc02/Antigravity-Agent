import os
import json
import time
import uuid
from typing import Dict, Any, Optional, List
import psutil
from agent.core.utils import atomic_write_json

class RuntimeManager:
    def __init__(self, drive_root: str):
        self.drive_root = os.path.abspath(drive_root)
        self.state_dir = os.path.join(self.drive_root, "state")
        self.sessions_dir = os.path.join(self.drive_root, "sessions")
        self.locks_dir = os.path.join(self.state_dir, "locks")
        
        os.makedirs(self.state_dir, exist_ok=True)
        os.makedirs(self.sessions_dir, exist_ok=True)
        os.makedirs(self.locks_dir, exist_ok=True)
        
        self.runtime_id = str(uuid.uuid4())
        self.lock_file = os.path.join(self.locks_dir, "agent.lock")
        self.current_session = None

    def _get_hardware_profile(self) -> Dict[str, Any]:
        profile = {
            "ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "gpu": False,
            "gpu_name": None,
            "vram_gb": 0.0
        }
        try:
            import torch
            if torch.cuda.is_available():
                profile["gpu"] = True
                profile["gpu_name"] = torch.cuda.get_device_name(0)
                profile["vram_gb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
        except ImportError:
            pass
        return profile

    def register_runtime(self) -> None:
        profile = self._get_hardware_profile()
        runtime_state = {
            "runtime_id": self.runtime_id,
            "hardware": profile,
            "started_at": time.time(),
            "last_heartbeat": time.time()
        }
        state_path = os.path.join(self.state_dir, "runtime_state.json")
        atomic_write_json(runtime_state, state_path)
        print(f"[RuntimeManager] Runtime {self.runtime_id} registered.")

    def acquire_lock(self, timeout: int = 60) -> bool:
        if os.path.exists(self.lock_file):
            try:
                with open(self.lock_file, "r") as f:
                    lock_data = json.load(f)
                if time.time() - lock_data.get("last_heartbeat", 0) < timeout:
                    print(f"[RuntimeManager] Lock denied. Held by {lock_data.get('runtime_id')}")
                    return False
                else:
                    print(f"[RuntimeManager] Lock expired (Old: {lock_data.get('runtime_id')}). Taking over.")
            except Exception as e:
                print(f"[RuntimeManager] Error reading lock: {e}. Forcing takeover.")

        self.heartbeat()
        return True

    def heartbeat(self) -> None:
        lock_data = {
            "runtime_id": self.runtime_id,
            "last_heartbeat": time.time()
        }
        atomic_write_json(lock_data, self.lock_file)

    def release_lock(self) -> None:
        if os.path.exists(self.lock_file):
            try:
                with open(self.lock_file, "r") as f:
                    lock_data = json.load(f)
                if lock_data.get("runtime_id") == self.runtime_id:
                    os.remove(self.lock_file)
            except Exception:
                pass

    def start_session(self, task_id: str, project_id: str = "default") -> str:
        session_id = str(uuid.uuid4())
        self.current_session = {
            "session_id": session_id,
            "task_id": task_id,
            "project_id": project_id,
            "status": "RUNNING",
            "started_at": time.time(),
            "last_action": None,
            "iteration": 0,
            "workspace_hash": None
        }
        
        session_dir = os.path.join(self.sessions_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        self.save_session()
        self._update_current_session_ptr(session_id)
        return session_id

    def save_session(self) -> None:
        if self.current_session:
            session_dir = os.path.join(self.sessions_dir, self.current_session['session_id'])
            os.makedirs(session_dir, exist_ok=True)
            path = os.path.join(session_dir, "session.json")
            atomic_write_json(self.current_session, path)
            self.heartbeat()

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        path = os.path.join(self.sessions_dir, session_id, "session.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                self.current_session = json.load(f)
            return self.current_session
        return None

    def _update_current_session_ptr(self, session_id: str) -> None:
        ptr_path = os.path.join(self.state_dir, "current_session.json")
        atomic_write_json({"session_id": session_id}, ptr_path)

    def get_last_active_session(self) -> Optional[str]:
        ptr_path = os.path.join(self.state_dir, "current_session.json")
        if os.path.exists(ptr_path):
            with open(ptr_path, "r") as f:
                data = json.load(f)
                return data.get("session_id")
        return None

    def append_message(self, session_id: str, role: str, content: str, iteration: int, metadata: dict = None):
        session_dir = os.path.join(self.sessions_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)
        path = os.path.join(session_dir, "messages.jsonl")
        msg = {
            "timestamp": time.time(), 
            "role": role, 
            "content": content, 
            "iteration": iteration,
            "metadata": metadata or {}
        }
        with open(path, "a") as f:
            f.write(json.dumps(msg) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def load_messages(self, session_id: str) -> List[Dict]:
        path = os.path.join(self.sessions_dir, session_id, "messages.jsonl")
        msgs = []
        if os.path.exists(path):
            with open(path, "r") as f:
                for line in f:
                    if line.strip():
                        msgs.append(json.loads(line))
        return msgs
