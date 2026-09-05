import requests
import json
import time
import websocket
import threading

def test_fase_i():
    print("[TESTE FASE I] Validando Interface e API do AgentCore")
    
    base_url = "http://127.0.0.1:8082/api"
    
    # 1. GET /health
    print("\\n--- Test Health ---")
    r = requests.get(f"{base_url}/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"
    print("[PASS] API /health funcionando.")
    
    # 2. Criar projeto
    print("\\n--- Test Projeto ---")
    r = requests.post(f"{base_url}/projects", json={"name": "ProjWeb"})
    assert r.status_code == 200
    pid = r.json()["project_id"]
    print(f"[PASS] Projeto criado via API: {pid}")
    
    r = requests.get(f"{base_url}/projects")
    projs = [p["project_id"] for p in r.json()["projects"]]
    assert pid in projs
    print("[PASS] Listagem de projetos via API.")
    
    # 3. Criar tarefa
    print("\\n--- Test Tarefa ---")
    r = requests.post(f"{base_url}/projects/{pid}/tasks", json={"title": "Fazer Web UI"})
    assert r.status_code == 200
    tid = r.json()["task_id"]
    print(f"[PASS] Tarefa criada via API: {tid}")
    
    r = requests.get(f"{base_url}/projects/{pid}/tasks")
    tasks = [t["task_id"] for t in r.json()["tasks"]]
    assert tid in tasks
    print("[PASS] Listagem de tarefas via API.")
    
    # 4. Iniciar agente
    print("\\n--- Test Execucao AgentCore (WebSocket) ---")
    r = requests.post(f"{base_url}/agent/run", json={"project_id": pid, "task_id": tid})
    assert r.status_code == 200
    sid = r.json()["session_id"]
    print(f"[PASS] Agente iniciado via API. Sessão: {sid}")
    
    # 5. WebSocket events
    ws_url = f"ws://127.0.0.1:8082/ws/sessions/{sid}"
    ws = websocket.create_connection(ws_url, timeout=5)
    
    received_events = []
    def recv_loop():
        try:
            while True:
                msg = ws.recv()
                received_events.append(json.loads(msg))
        except:
            pass
            
    t = threading.Thread(target=recv_loop)
    t.start()
    
    time.sleep(2)
    
    # 6. Cancelar agente
    print("\\n--- Test Cancelar Sessao ---")
    r = requests.post(f"{base_url}/sessions/{sid}/cancel")
    assert r.status_code == 200
    print("[PASS] Pedido de cancelamento processado via API.")
    
    time.sleep(1)
    ws.close()
    t.join()
    
    types = [ev["type"] for ev in received_events]
    print(f"Eventos recebidos: {types}")
    assert len(types) > 0
    # Since agent is running locally, it might immediately complete or error due to DummyProvider not existing, 
    # but the test checks if event piping is alive.
    
    print("\\nFASE I = APPROVED")

if __name__ == "__main__":
    test_fase_i()
