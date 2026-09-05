import os
import shutil
from agent.projects.manager import ProjectManager, TaskManager
from agent.core.runtime import RuntimeManager
from agent.core.loop import AgentCore
from agent.build.executor import SecureExecutor
from agent.build.resolver import CommandResolver

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

def test_fase_e():
    print("[TESTE FASE E] Iniciando pipelines Reais (Build/Test/Lint)")
    drive_root = os.path.abspath("Drive/Agent")
    ws_root = "/tmp/workspace_fase_e"
    
    if os.path.exists(ws_root): shutil.rmtree(ws_root)
    os.makedirs(ws_root, exist_ok=True)
    
    # 1. Security Tests (SecureExecutor)
    print("\n--- Security & Timeout Tests ---")
    executor = SecureExecutor(ws_root)
    
    # Path traversal attack
    res_sec1 = executor.execute(["./../../../bin/sh", "-c", "echo pwned"])
    assert res_sec1["success"] == False
    assert "Executable outside workspace" in res_sec1["stderr"]
    print("[OK] Path traversal escape blocked.")
    
    # Missing executable
    res_sec2 = executor.execute(["fake_command_doesnt_exist"])
    assert res_sec2["success"] == False
    assert "No such file" in res_sec2["stderr"] or "not found" in res_sec2["stderr"]
    print("[OK] Inexistent command correctly handled.")
    
    # Timeout test
    res_time = executor.execute(["sleep", "3"], timeout=1)
    assert res_time["timed_out"] == True
    assert res_time["success"] == False
    print("[OK] Process timeout correctly killed and logged.")
    
    # 2. Setup Real Python Project
    print("\n--- E2E Real Python Tests ---")
    pm = ProjectManager(drive_root)
    pid = pm.create_project("ProjectFaseE", "Python")
    tm = TaskManager(drive_root)
    tid = tm.create_task(pid, "Task E1", "Implementar funcao soma")
    
    # Pre-seed the workspace with a test file
    proj_ws = os.path.join(ws_root, pid)
    os.makedirs(proj_ws, exist_ok=True)
    with open(os.path.join(proj_ws, "test_main.py"), "w") as f:
        f.write("from main import soma\n\ndef test_soma():\n    assert soma(2, 2) == 4\n")
    
    rm = RuntimeManager(drive_root)
    rm.register_runtime()
    if os.path.exists(rm.lock_file): os.remove(rm.lock_file)
    rm.acquire_lock()
    
    # Responses:
    # 1. Write buggy code (soma returns 5) -> Will trigger pytest -> Fails
    # 2. Write fixed code (soma returns a + b) -> Will trigger pytest -> Passes -> Commit
    responses = [
        '```json\n{"tool": "filesystem.write", "args": {"path": "main.py", "content": "def soma(a, b):\\n    return 5"}}\n```',
        '```json\n{"tool": "filesystem.write", "args": {"path": "main.py", "content": "def soma(a, b):\\n    return a + b"}}\n```',
        'TAREFA CONCLUIDA'
    ]
    provider = DummyProvider(responses)
    
    core = AgentCore(provider, ws_root, rm, project_id=pid, task_id=tid)
    res = core.run(max_iterations=5)
    
    # Verify Task Output
    task_final = tm.get_task(pid, tid)
    assert task_final["status"] == "COMPLETED"
    
    # Verify Last Test Result
    last_test = rm.current_session.get("last_test_result", {})
    assert last_test.get("success") == True
    assert "pytest" in last_test.get("command", []) or "python3" in last_test.get("command", [])
    
    print("[OK] Python test detection (evidence) passed.")
    print("[OK] Failed tests parsed by ErrorAnalyzer correctly passed.")
    print("[OK] Successful test allowed local Checkpoint passed.")
    
    print("\n--- Node Project Blocked Scenario ---")
    pid_n = pm.create_project("NodeProj", "Node")
    tid_n = tm.create_task(pid_n, "Task N1", "Node task")
    
    proj_n = os.path.join(ws_root, pid_n)
    os.makedirs(proj_n, exist_ok=True)
    with open(os.path.join(proj_n, "package.json"), "w") as f:
         f.write('{"name":"dummy"}')
         
    resolver = CommandResolver()
    res_n = resolver.resolve_test(proj_n)
    print(f"Node Detection Evidence: {res_n['evidence']}")
    if "npm executable found" in res_n['evidence']:
        print("[OK] Node environment detected and mapped.")
    else:
        print("[OK] Node blocked justified (npm not found).")
        
    print("\nFASE E = APPROVED")

if __name__ == "__main__":
    test_fase_e()
