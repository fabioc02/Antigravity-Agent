import os
import shutil
import time
import threading
from http.server import HTTPServer
from agent.bridge.server import BridgeHandler, BridgeSecurity
from agent.bridge.client import BridgeClient

def test_fase_h():
    print("[TESTE FASE H] Iniciando testes do PC Bridge")
    
    ws_root = os.path.abspath("/tmp/bridge_allowed")
    if os.path.exists(ws_root): shutil.rmtree(ws_root)
    os.makedirs(ws_root, exist_ok=True)
    
    external_dir = os.path.abspath("/tmp/bridge_external")
    if os.path.exists(external_dir): shutil.rmtree(external_dir)
    os.makedirs(external_dir, exist_ok=True)
    with open(os.path.join(external_dir, "secret.txt"), "w") as f:
        f.write("SUPER_SECRET")
        
    # Symlink escape setup
    os.symlink(external_dir, os.path.join(ws_root, "escape_link"))
    
    # 1. Start Server in Thread
    host, port = "127.0.0.1", 8081
    token = "test_super_secret_token"
    
    BridgeHandler.security = BridgeSecurity([ws_root], token, level="DEVELOPMENT")
    httpd = HTTPServer((host, port), BridgeHandler)
    t = threading.Thread(target=httpd.serve_forever)
    t.daemon = True
    t.start()
    
    time.sleep(1) # wait for server to start
    
    endpoint = f"http://{host}:{port}"
    client = BridgeClient(endpoint, token)
    
    # 2. Test Unauthenticated Request
    print("\n--- Test Authentication ---")
    bad_client = BridgeClient(endpoint, "wrong_token")
    res_bad = bad_client.list_dir(ws_root)
    assert "error" in res_bad and res_bad["error"] == "Unauthorized"
    print("[PASS] Unauthenticated request BLOCKED.")
    
    res_good = client.list_dir(ws_root)
    assert res_good.get("success") == True
    print("[PASS] Authenticated request PASS.")
    
    # 3. Test Allowed Dir
    print("\n--- Test Directory Operations ---")
    client.write_file(os.path.join(ws_root, "test.txt"), "hello")
    res_read = client.read_file(os.path.join(ws_root, "test.txt"))
    assert res_read.get("content") == "hello"
    print("[PASS] Allowed directory file operations PASS.")
    
    # 4. Test Forbidden Dir
    res_forb = client.read_file(os.path.join(external_dir, "secret.txt"))
    assert "error" in res_forb and "outside allowed directories" in res_forb["error"]
    print("[PASS] Forbidden directory BLOCKED.")
    
    # 5. Path Traversal
    res_trav = client.read_file(os.path.join(ws_root, "..", "bridge_external", "secret.txt"))
    assert "error" in res_trav and "outside allowed directories" in res_trav["error"]
    print("[PASS] Path traversal BLOCKED.")
    
    # 6. Symlink Escape
    res_sym = client.read_file(os.path.join(ws_root, "escape_link", "secret.txt"))
    assert "error" in res_sym and "outside allowed directories" in res_sym["error"]
    print("[PASS] Symlink escape BLOCKED.")
    
    # 7. Terminal Allowed
    print("\n--- Test Terminal ---")
    res_exec = client.execute(["echo", "hello"], cwd=ws_root)
    assert res_exec.get("success") == True
    assert "hello" in res_exec.get("stdout", "")
    print("[PASS] Allowed terminal execution PASS.")
    
    # 8. Command Prohibited (Destructive)
    res_dest = client.execute(["rm", "-rf", "/"])
    assert "error" in res_dest and "blocked in DEVELOPMENT mode" in res_dest["error"]
    print("[PASS] Prohibited command BLOCKED in DEVELOPMENT mode.")
    
    # 9. Destructive Op Blocked
    res_del = client.delete(os.path.join(ws_root, "test.txt"))
    assert "error" in res_del and "Requires DESTRUCTIVE mode" in res_del["error"]
    print("[PASS] Destructive file operation BLOCKED in DEVELOPMENT mode.")
    
    # 10. Timeout
    res_time = client.execute(["sleep", "3"], timeout=1)
    assert res_time.get("timed_out") == True
    print("[PASS] Execution timeout successfully handled.")
    
    # 11. Destructive Mode Test
    print("\n--- Test Destructive Mode ---")
    BridgeHandler.security.level = "DESTRUCTIVE"
    res_del2 = client.delete(os.path.join(ws_root, "test.txt"))
    assert res_del2.get("success") == True
    print("[PASS] Destructive file operation ALLOWED in DESTRUCTIVE mode.")
    
    # 12. Bridge Offline
    print("\n--- Test Bridge Offline ---")
    httpd.shutdown()
    httpd.server_close()
    t.join(timeout=2)
    
    res_off = client.list_dir(ws_root)
    assert res_off.get("status") == "BRIDGE_UNAVAILABLE"
    print("[PASS] Offline bridge returns BRIDGE_UNAVAILABLE.")
    
    print("\nFASE H = APPROVED")

if __name__ == "__main__":
    test_fase_h()
