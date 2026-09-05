import urllib.request
import urllib.error
import json

class BridgeClient:
    def __init__(self, endpoint: str, auth_token: str):
        self.endpoint = endpoint.rstrip("/")
        self.auth_token = auth_token
        
    def _request(self, action: str, args: dict) -> dict:
        url = f"{self.endpoint}"
        payload = json.dumps({"action": action, "args": args}).encode('utf-8')
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Authorization", f"Bearer {self.auth_token}")
        req.add_header("Content-Type", "application/json")
        
        try:
            with urllib.request.urlopen(req, timeout=35) as response:
                res_body = response.read().decode('utf-8')
                return json.loads(res_body)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            try:
                return json.loads(err_body)
            except:
                return {"error": f"HTTP {e.code}: {err_body}"}
        except urllib.error.URLError as e:
            return {"error": f"Connection failed: {str(e)}", "status": "BRIDGE_UNAVAILABLE"}
        except Exception as e:
            return {"error": str(e)}

    def list_dir(self, path: str):
        return self._request("list_dir", {"path": path})

    def read_file(self, path: str):
        return self._request("read_file", {"path": path})

    def write_file(self, path: str, content: str):
        return self._request("write_file", {"path": path, "content": content})

    def delete(self, path: str):
        return self._request("delete", {"path": path})

    def execute(self, command: list, cwd: str = None, timeout: int = 30):
        return self._request("execute", {"command": command, "cwd": cwd, "timeout": timeout})
