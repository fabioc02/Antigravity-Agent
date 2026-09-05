import json
import urllib.request
import urllib.error

class LocalBridgeClient:
    def __init__(self, endpoint_url: str = "http://localhost:3000"):
        self.endpoint_url = endpoint_url

    def _post(self, path: str, data: dict):
        req = urllib.request.Request(
            f"{self.endpoint_url}{path}",
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        try:
            with urllib.request.urlopen(req) as f:
                return json.loads(f.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            return {"error": json.loads(e.read().decode('utf-8')).get('error', str(e))}
        except Exception as e:
            return {"error": str(e)}

    def execute(self, executable: str, args: list, cwd: str = ".") -> dict:
        return self._post("/api/bridge/execute", {"executable": executable, "args": args, "cwd": cwd})

    def read_file(self, path: str) -> dict:
        return self._post("/api/bridge/fs/read", {"path": path})

    def write_file(self, path: str, content: str) -> dict:
        return self._post("/api/bridge/fs/write", {"path": path, "content": content})

    def list_dir(self, path: str) -> dict:
        return self._post("/api/bridge/fs/list", {"path": path})

bridge = LocalBridgeClient()
