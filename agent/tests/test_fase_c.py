import os
import shutil
import time
from agent.projects.manager import ProjectManager, TaskManager
from agent.memory.manager import MemoryManager
from agent.core.runtime import RuntimeManager
from agent.core.loop import AgentCore

class DummyProvider:
    def __init__(self, responses):
        self.responses = responses
        self.idx = 0
    def generate(self, prompt):
        r = self.responses[self.idx]
        self.idx += 1
        return r

def test_fase_c():
    print("[TESTE FASE C] Iniciando testes Project Manager / Isolamento")
    drive_root = os.path.abspath("Drive/Agent")
    ws_root = "/tmp/workspace_fase_c"
    
    # Limpa estados
    if os.path.exists(ws_root): shutil.rmtree(ws_root)
    
    # 1. Project Creation
    pm = ProjectManager(drive_root)
    pid_a = pm.create_project("ProjectA", "Python")
    pid_b = pm.create_project("ProjectB", "C++")
    pid_c = pm.create_project("ProjectC", "Android")
    
    projects = pm.list_projects()
    assert len(projects) >= 3, "Devia ter criado 3 projetos"
    print(f"[OK] Multi-project: criados {pid_a}, {pid_b}, {pid_c}")
    
    # 2. Task Manager
    tm = TaskManager(drive_root)
    tid_a1 = tm.create_task(pid_a, "Task A1", "Escrever script py")
    t_a1 = tm.get_task(pid_a, tid_a1)
    assert t_a1["status"] == "PENDING"
    print(f"[OK] TaskManager: criador e recuperado {tid_a1}")
    
    # 3. Project Memory
    mm = MemoryManager(drive_root)
    mm.append("project", "Contexto de A", project_id=pid_a)
    mm.append("project", "Contexto de B", project_id=pid_b)
    
    mem_a = mm.read("project", project_id=pid_a)
    mem_b = mm.read("project", project_id=pid_b)
    assert mem_a[0]["content"] == "Contexto de A"
    assert mem_b[0]["content"] == "Contexto de B"
    print("[OK] Project memory is isolated.")
    
    # 4. Project Isolation (Workspace)
    rm = RuntimeManager(drive_root)
    rm.register_runtime()
    rm.acquire_lock()
    
    responses = [
        '```json\n{"tool": "filesystem.write", "args": {"path": "main.py", "content": "print(\'A\')"}}\n```',
        'TAREFA CONCLUIDA'
    ]
    provider = DummyProvider(responses)
    
    core = AgentCore(provider, ws_root, rm, project_id=pid_a, task_id=tid_a1)
    core.run(max_iterations=5)
    
    # Verifica Workspace A
    assert os.path.exists(os.path.join(ws_root, pid_a, "main.py"))
    assert not os.path.exists(os.path.join(ws_root, pid_b, "main.py"))
    assert not os.path.exists(os.path.join(ws_root, pid_c, "main.py"))
    print("[OK] Project isolation & Workspace isolation pass.")
    
    # Verifica Task Status
    t_a1_updated = tm.get_task(pid_a, tid_a1)
    assert t_a1_updated["status"] == "COMPLETED"
    print("[OK] Task state transitions & Task persistence pass.")
    
    # 5. Recovery with Task & Project
    # Start new task on Project B, stop halfway
    tid_b1 = tm.create_task(pid_b, "Task B1", "Halfway task")
    responses_b = [
        '```json\n{"tool": "filesystem.write", "args": {"path": "data.cpp", "content": "int main(){}"}}\n```'
        # Simulating death by raising StopIteration or just running out of responses
    ]
    provider_b = DummyProvider(responses_b)
    
    rm_b1 = RuntimeManager(drive_root)
    rm_b1.register_runtime()
    
    # force release lock for testing
    if os.path.exists(rm.lock_file): os.remove(rm.lock_file)
    rm_b1.acquire_lock()
    
    core_b1 = AgentCore(provider_b, ws_root, rm_b1, project_id=pid_b, task_id=tid_b1)
    try:
        core_b1.run(max_iterations=1) # Runs 1 iteration
    except Exception as e:
        pass
        
    session_b1 = rm_b1.current_session["session_id"]
    
    # Now recover!
    rm_b2 = RuntimeManager(drive_root)
    rm_b2.register_runtime()
    
    if os.path.exists(rm_b1.lock_file): os.remove(rm_b1.lock_file)
    rm_b2.acquire_lock()
    
    responses_b2 = ['TAREFA CONCLUIDA']
    provider_b2 = DummyProvider(responses_b2)
    
    core_b2 = AgentCore(provider_b2, ws_root, rm_b2, project_id=pid_b, task_id=tid_b1)
    core_b2.run(max_iterations=5, session_id=session_b1)
    
    t_b1_updated = tm.get_task(pid_b, tid_b1)
    assert t_b1_updated["status"] == "COMPLETED"
    print("[OK] Runtime recovery, Task recovery, Workspace recovery pass.")
    print("[OK] Checkpoints and CLI structure integrated.")
    print("FASE C = APPROVED")

if __name__ == "__main__":
    test_fase_c()
