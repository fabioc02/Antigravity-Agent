import os
import sys
import time
import json

DRIVE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, DRIVE_ROOT)

from agent.core.runtime import RuntimeManager
from agent.core.workspace import WorkspaceManager
from agent.core.loop import AgentCore
from agent.llm.provider import LLMProvider

class MockInfrastructureProvider(LLMProvider):
    """
    TESTE DE INFRAESTRUTURA - SEM GPU
    Mock apenas para simular as strings JSON da infraestrutura, 
    provando que o AgentCore serializa, salva, persiste histórico 
    e envia ferramentas sem falhas transacionais.
    """
    def __init__(self):
        self.call_count = 0
        
    def generate(self, prompt: str) -> str:
        self.call_count += 1
        if self.call_count == 1:
            # Generate a write tool call
            return '```json\n{"tool": "filesystem.write", "args": {"path": "main.py", "content": "print(1)"}}\n```'
        elif self.call_count == 2:
            return '```json\n{"tool": "terminal.execute", "args": {"command": "python3 main.py", "cwd": "."}}\n```'
        else:
            return 'TAREFA CONCLUIDA'

def test_fase_f1():
    print("\n[TESTE DE INFRAESTRUTURA FASE F.1]")
    print("Testando Persistencia, Workspace, Hash, Lock, e Messages ChatML\n")
    
    workspace_root = "/tmp/test_workspace_f1"
    
    # 1. Start Runtime A
    rm_a = RuntimeManager(DRIVE_ROOT)
    assert rm_a.acquire_lock()
    rm_a.register_runtime()
    
    provider_a = MockInfrastructureProvider()
    core_a = AgentCore(provider_a, workspace_root, rm_a, project_id="proj_test_f1")
    
    print("[TEST] Inciando Tarefa (Runtime A)")
    # Vai rodar as duas iterações e depois simulamos morte:
    # A primeira iteração fará o WriteFileTool e deve causar Workspace Sync e Update de Hash.
    core_a.run("Make a python script and run it", max_iterations=1) 
    
    session_id = rm_a.get_last_active_session()
    assert session_id is not None
    
    # Checar hash
    session_data = rm_a.load_session(session_id)
    hash_a = session_data.get('workspace_hash')
    assert hash_a is not None, "Workspace Hash nao foi salvo no Checkpoint"
    print(f"[TEST] Workspace Hash apos iteracao 1: {hash_a}")
    
    # Checar chat history
    msgs = rm_a.load_messages(session_id)
    assert len(msgs) >= 3, "ChatML messages.jsonl nao persistiu!"
    print(f"[TEST] Historico ChatML persistido com {len(msgs)} mensagens.")
    
    # Simular Morte do Runtime A
    print("\n[TEST] ---> SIMULANDO MORTE DO RUNTIME A <---")
    rm_a.release_lock() # Removemos o lock para simular lease expired
    
    # Runtime B - Resume
    print("\n[TEST] Inciando Runtime B (Resume)")
    rm_b = RuntimeManager(DRIVE_ROOT)
    assert rm_b.acquire_lock()
    rm_b.register_runtime()
    
    provider_b = MockInfrastructureProvider()
    # O provider B tem seu counter resetado, mas nós vamos resumir.
    core_b = AgentCore(provider_b, workspace_root, rm_b, project_id="proj_test_f1")
    
    core_b.run("RESUMING", max_iterations=3, session_id=session_id)
    
    # Checar novo hash
    session_data_b = rm_b.load_session(session_id)
    hash_b = session_data_b.get('workspace_hash')
    assert hash_b == hash_a, "Hash mismatch - integridade comprometida!"
    print(f"[TEST] Workspace Hash restaurado via Drive: {hash_b}")
    
    msgs_b = rm_b.load_messages(session_id)
    assert len(msgs_b) > len(msgs), "Novas iteracoes nao foram appendadas ao historico!"
    print(f"[TEST] Historico ChatML continuou com sucesso! Agora tem {len(msgs_b)} mensagens.")
    
    print("\n✅ FASE F.1 APROVADA: Infraestrutura E2E Test (Sync/Lock/Recovery/ChatML) Passou.")
    rm_b.release_lock()

if __name__ == "__main__":
    test_fase_f1()
