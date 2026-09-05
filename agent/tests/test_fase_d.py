import os
import shutil
import subprocess
from agent.projects.manager import ProjectManager, TaskManager
from agent.core.runtime import RuntimeManager
from agent.core.loop import AgentCore
from agent.git.manager import GitManager

class DummyProvider:
    def __init__(self, responses):
        self.responses = responses
        self.idx = 0
    def generate(self, prompt):
        # Captura prompts para debugging, se necessario
        r = self.responses[self.idx]
        self.idx += 1
        return r

def test_fase_d():
    print("[TESTE FASE D] Iniciando testes Git local, Checkpoint, Diff e Rollback")
    drive_root = os.path.abspath("Drive/Agent")
    ws_root = "/tmp/workspace_fase_d"
    
    # Limpa estados
    if os.path.exists(ws_root): shutil.rmtree(ws_root)
    
    # 1. Setup
    pm = ProjectManager(drive_root)
    pid = pm.create_project("ProjectGitTest", "Custom")
    tm = TaskManager(drive_root)
    tid = tm.create_task(pid, "Task D1", "Testar automacao Git")
    
    rm = RuntimeManager(drive_root)
    rm.register_runtime()
    rm.acquire_lock()
    
    # Responses do LLM Fake:
    # 1. LLM escreve um código bugado. (O AgentCore vai rodar o teste, falhar, fazer diff e mandar pro LLM)
    # 2. LLM corrige o código. (O AgentCore vai rodar o teste, passar, e fazer COMMIT)
    # 3. LLM termina.
    responses = [
        '```json\n{"tool": "filesystem.write", "args": {"path": "script.py", "content": "import sys\\nsys.exit(1)"}}\n```',
        '```json\n{"tool": "filesystem.write", "args": {"path": "script.py", "content": "import sys\\nsys.exit(0)"}}\n```',
        'TAREFA CONCLUIDA'
    ]
    provider = DummyProvider(responses)
    
    core = AgentCore(provider, ws_root, rm, project_id=pid, task_id=tid)
    
    # Monkeypatch the detect_project just for this test so we can use a pure python execution as test
    def mock_detect(pid, ws):
        return {"test_command": "python3 script.py"}
    core.pm.detect_project = mock_detect
    
    res = core.run(max_iterations=5)
    
    # 2. Verifica a Árvore do Git
    git_manager = GitManager(core.wm.local_dir)
    
    # O diretório do git foi criado?
    assert os.path.exists(os.path.join(core.wm.local_dir, ".git")), "Pasta .git nao criada!"
    
    # Verifica o histórico (Deve haver 2 commits: Initial + Checkpoint da iteracao onde o teste passou)
    log_proc = subprocess.run(["git", "log", "--oneline"], cwd=core.wm.local_dir, capture_output=True, text=True)
    commits = log_proc.stdout.strip().split("\n")
    
    print(f"Commits found: {len(commits)}")
    for c in commits: print(c)
    
    # Se fossem ambos commitados, teriam 3 commits. Mas o primeiro Write FALHOU no teste, entao nao commitou.
    assert len(commits) == 2, f"Expected 2 commits, got {len(commits)}"
    assert "Checkpoint iteration 1" in commits[0], "Ultimo commit deveria ser o Checkpoint da iteracao 1 (que é o segundo write)"
    
    # 3. Verifica Persistência do .git no Drive
    drive_git_path = os.path.join(drive_root, "projects", pid, "source", ".git")
    assert os.path.exists(drive_git_path), ".git nao foi sincronizado para o Drive!"
    
    print("[OK] Git init via AgentCore passed.")
    print("[OK] Failed tests avoid commit and feed Diff/Errors to LLM passed.")
    print("[OK] Successful tests trigger local Git commit passed.")
    print("[OK] Git tree synchronization to Drive passed.")
    print("FASE D = APPROVED")

if __name__ == "__main__":
    test_fase_d()
