import urllib.request
import urllib.parse
import json
import asyncio
import time
try:
    import websockets
except ImportError:
    print("websockets not found, skipping ws test for now")

API_BASE = "http://127.0.0.1:8082"

def request(url, method="GET", data=None):
    req = urllib.request.Request(url, method=method)
    if data:
        data = json.dumps(data).encode('utf-8')
        req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, data=data) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def test_e2e():
    print("--- 1. Criar Projeto ---")
    status, data = request(f"{API_BASE}/projects", "POST", {"name": "Test Real Task", "stack": "python"})
    assert status == 200, data
    pid = data["project_id"]
    print(f"Projeto criado: {pid}")

    print("--- 2. Criar Task ---")
    status, data = request(f"{API_BASE}/projects/{pid}/tasks", "POST", {"title": "Criar main.py", "description": "Crie um arquivo main.py que imprima Hello World"})
    assert status == 200, data
    tid = data["task_id"]
    print(f"Task criada: {tid}")

    print("--- 3. Iniciar Agente ---")
    status, data = request(f"{API_BASE}/agent/run", "POST", {"project_id": pid, "task_id": tid})
    assert status == 200, data
    sid = data["session_id"]
    print(f"Sessão iniciada: {sid}")

    print("--- 5. Endpoints de Interface ---")
    endpoints = ["/sessions", f"/sessions/{sid}", "/runtime", f"/github/status?project_id={pid}", "/bridge/status"]
    for ep in endpoints:
        status, data = request(f"{API_BASE}{ep}")
        print(f"GET {ep}: {status} - {str(data)[:100]}")

if __name__ == "__main__":
    test_e2e()
