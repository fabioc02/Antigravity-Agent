import urllib.request
import json
url = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-Coder-32B-Instruct/v1/chat/completions"
payload = {
    "model": "Qwen/Qwen2.5-Coder-32B-Instruct",
    "messages": [{"role": "user", "content": "Return the exact word 'QWEN_WORKS'"}],
    "max_tokens": 10
}
req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req) as f:
        print(json.loads(f.read().decode('utf-8')))
except Exception as e:
    if hasattr(e, 'read'): print("ERR:", e.read().decode())
    else: print("ERR:", e)
