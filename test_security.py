import urllib.request
import urllib.parse
import json

def post(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as f:
            return json.loads(f.read().decode('utf-8')), f.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode('utf-8')), e.code

print("--- SECURITY TESTS ---")

print("\n1. Test Executable not in whitelist:")
res, code = post('http://localhost:3000/api/bridge/execute', {"executable": "rm", "args": ["-rf", "/"]})
print(f"Status {code}: {res}")

print("\n2. Test Path Traversal in CWD:")
res, code = post('http://localhost:3000/api/bridge/execute', {"executable": "ls", "cwd": "../../../etc"})
print(f"Status {code}: {res}")

print("\n3. Test Shell Operator Injection (&&):")
res, code = post('http://localhost:3000/api/bridge/execute', {"executable": "echo", "args": ["hello", "&&", "cat", "/etc/passwd"]})
print(f"Status {code}: {res}")

print("\n4. Test Safe Command Execution:")
res, code = post('http://localhost:3000/api/bridge/execute', {"executable": "ls", "args": ["-l", "project"], "cwd": "."})
print(f"Status {code}: {res['stdout'].strip()}")
