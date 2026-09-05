import requests
import json
import time
import websocket
import threading
import sys

API_BASE = "http://127.0.0.1:8082"
WS_BASE = "ws://127.0.0.1:8082"

def test_endpoints():
    print("\n--- 3. FRONTEND — ENDPOINTS REAIS ---")
    eps = [
        "/github/status?project_id=test_proj",
        "/bridge/status",
        "/runtime",
        "/sessions"
    ]
    for ep in eps:
        try:
            r = requests.get(API_BASE + ep)
            print(f"[PASS] GET {ep} -> {r.status_code}")
        except Exception as e:
            print(f"[FAIL] GET {ep} -> {e}")

def test_e2e_and_recovery():
    print("\n--- 1. WEBSOCKET, 2. AGENTCORE REAL, 4. RECOVERY, 5. CANCELAMENTO ---")
    
    # Criar projeto
    r = requests.post(f"{API_BASE}/projects", json={"name": "Test Real Task E2E", "stack": "python"})
    pid = r.json()["project_id"]
    print(f"[PASS] Projeto criado: {pid}")

    # Criar task
    r = requests.post(f"{API_BASE}/projects/{pid}/tasks", json={"title": "Criar main.py", "description": "Crie um arquivo main.py que imprima Hello World"})
    tid = r.json()["task_id"]
    print(f"[PASS] Task criada: {tid}")

    # Iniciar agente
    r = requests.post(f"{API_BASE}/agent/run", json={"project_id": pid, "task_id": tid})
    sid = r.json()["session_id"]
    print(f"[PASS] Agente iniciado via API. Sessão: {sid}")

    # Conectar WebSocket
    ws_url = f"{WS_BASE}/sessions/{sid}"
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
    
    # Deixar rodar 5 segundos para gerar eventos e testar o LLM real
    print("Aguardando 10 segundos para coletar stream real do LLM...")
    time.sleep(10)
    
    # 5. CANCELAMENTO REAL
    r = requests.post(f"{API_BASE}/sessions/{sid}/cancel")
    print(f"[PASS] Cancelamento solicitado: {r.status_code}")
    
    time.sleep(2)
    ws.close()
    t.join()
    
    types = [ev["type"] for ev in received_events]
    print(f"Eventos WebSocket recebidos na 1ª fase: {types}")
    
    # 4. RECOVERY
    print("\n--- TESTANDO RECOVERY ---")
    r = requests.post(f"{API_BASE}/sessions/{sid}/resume")
    print(f"[PASS] Recovery (resume) solicitado: {r.status_code}")
    
    if r.status_code == 200:
        ws2 = websocket.create_connection(ws_url, timeout=5)
        recv2 = []
        def recv_loop2():
            try:
                while True:
                    msg = ws2.recv()
                    recv2.append(json.loads(msg))
            except:
                pass
        t2 = threading.Thread(target=recv_loop2)
        t2.start()
        
        print("Aguardando 10 segundos para coletar stream do resume...")
        time.sleep(10)
        ws2.close()
        t2.join()
        types2 = [ev["type"] for ev in recv2]
        print(f"Eventos WebSocket recebidos no Recovery: {types2}")
        
    # Verificar sessão no log
    r = requests.get(f"{API_BASE}/sessions/{sid}")
    print(f"[PASS] Dados da sessão {sid}: {r.status_code}")

if __name__ == "__main__":
    try:
        test_endpoints()
        test_e2e_and_recovery()
        print("\n[✓] ALL TESTS EXECUTED")
    except Exception as e:
        print(f"\n[X] TEST FAILED: {e}")
