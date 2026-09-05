import os
import shutil
import time
from agent.projects.manager import ProjectManager, TaskManager
from agent.core.runtime import RuntimeManager
from agent.core.loop import AgentCore
from agent.build.executor import SecureExecutor
from agent.build.manager import TestManager
from agent.security.sandbox import SecuritySandbox

class DummyProvider:
    def __init__(self, responses):
        self.responses = responses
        self.idx = 0
    def generate(self, prompt):
        if self.idx < len(self.responses):
            r = self.responses[self.idx]
            self.idx += 1
            return r
        return "TAREFA CONCLUIDA"

def test_fase_e1():
    print("[TESTE FASE E.1] Iniciando Hardening e Validação")
    drive_root = os.path.abspath("Drive/Agent")
    ws_root = "/tmp/workspace_fase_e1"
    
    if os.path.exists(ws_root): shutil.rmtree(ws_root)
    os.makedirs(ws_root, exist_ok=True)
    
    # 1. Symlink Escape Test
    print("\n--- Symlink Escape Tests ---")
    pid_sec = "SecProject"
    os.makedirs(os.path.join(ws_root, pid_sec), exist_ok=True)
    os.makedirs("/tmp/external_secret", exist_ok=True)
    with open("/tmp/external_secret/secret.txt", "w") as f:
        f.write("SUPER_SECRET")
        
    os.symlink("/tmp/external_secret", os.path.join(ws_root, pid_sec, "escape_link"))
    
    sandbox = SecuritySandbox(os.path.join(ws_root, pid_sec))
    try:
        sandbox.validate_path("escape_link/secret.txt")
        assert False, "Symlink escape should have been blocked!"
    except PermissionError as e:
        assert "Security Error" in str(e)
        print("[OK] Symlink escape correctly blocked by Sandbox.")
        
    executor = SecureExecutor(os.path.join(ws_root, pid_sec))
    res_esc = executor.execute(["./escape_link/some_script.sh"])
    assert res_esc["success"] == False
    assert "outside workspace" in res_esc["stderr"]
    print("[OK] Symlink executable escape correctly blocked by SecureExecutor.")
    
    # 2. Build/Test Accumulated Writes & Recovery
    print("\n--- E2E Accumulated Writes & Interrupted Recovery ---")
    pm = ProjectManager(drive_root)
    pid = pm.create_project("ProjectFaseE1", "Python")
    tm = TaskManager(drive_root)
    tid = tm.create_task(pid, "Task E1", "Implementar mult e soma")
    
    proj_ws = os.path.join(ws_root, pid)
    os.makedirs(proj_ws, exist_ok=True)
    with open(os.path.join(proj_ws, "test_main.py"), "w") as f:
        f.write("from main import calc\n\ndef test_calc():\n    assert calc(2, 2) == 4\n")
    
    rm = RuntimeManager(drive_root)
    rm.register_runtime()
    if os.path.exists(rm.lock_file): os.remove(rm.lock_file)
    rm.acquire_lock()
    
    # Responses:
    # 1. WRITE file 1
    # 2. WRITE file 2 (fix)
    # 3. TEST (manual call)
    # 4. TAREFA CONCLUIDA
    responses = [
        '```json\n{"tool": "filesystem.write", "args": {"path": "main.py", "content": "def calc(a, b):\\n    return 0"}}\n```',
        '```json\n{"tool": "filesystem.write", "args": {"path": "main.py", "content": "def calc(a, b):\\n    return a + b"}}\n```',
        '```json\n{"tool": "project.test", "args": {}}\n```',
        'TAREFA CONCLUIDA'
    ]
    provider = DummyProvider(responses)
    
    core = AgentCore(provider, ws_root, rm, project_id=pid, task_id=tid)
    res = core.run(max_iterations=5)
    
    task_final = tm.get_task(pid, tid)
    assert task_final["status"] == "COMPLETED"
    print("[OK] Accumulated Writes -> Test -> Commit passed.")
    
    # 3. Test Interrupted Build
    print("\n--- Interrupted Build Recovery ---")
    tm_b = TestManager(proj_ws, os.path.join(drive_root, "projects", pid, "tasks", tid))
    # inject a fake running state
    tm_b._append_log({
        "session_id": rm.current_session["session_id"],
        "iteration": 99,
        "command": ["pytest"],
        "cwd": proj_ws,
        "start_time": time.time(),
        "status": "RUNNING"
    })
    
    interrupted = tm_b.check_interrupted()
    assert interrupted is not None
    assert interrupted["status"] == "INTERRUPTED"
    print("[OK] Recovery during build properly marked as INTERRUPTED.")
    
    print("\nFASE E.1 = APPROVED")

if __name__ == "__main__":
    test_fase_e1()
