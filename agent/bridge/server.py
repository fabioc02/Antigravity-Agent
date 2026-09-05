import os
import json
import time
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - Bridge - %(levelname)s - %(message)s')
logger = logging.getLogger("Bridge")

class BridgeSecurity:
    def __init__(self, allowed_dirs: list, auth_token: str, level: str = "DEVELOPMENT"):
        self.allowed_dirs = [os.path.realpath(d) for d in allowed_dirs]
        self.auth_token = auth_token
        self.level = level # READ_ONLY, DEVELOPMENT, DESTRUCTIVE
        self.blocked_commands = {'sudo', 'su', 'rm', 'shutdown', 'reboot', 'mkfs', 'dd', 'chmod', 'chown', 'mv'}

    def validate_auth(self, token: str) -> bool:
        return token == self.auth_token

    def validate_path(self, target_path: str, must_exist: bool = False) -> str:
        abs_path = os.path.realpath(target_path)
        
        allowed = False
        for d in self.allowed_dirs:
            if abs_path == d or abs_path.startswith(d + os.sep):
                allowed = True
                break
                
        if not allowed:
            raise PermissionError(f"Security Error: Path {target_path} is outside allowed directories.")
            
        if must_exist and not os.path.exists(abs_path):
            raise FileNotFoundError(f"Path not found: {target_path}")
            
        return abs_path

    def validate_command(self, cmd_args: list) -> None:
        if self.level == "READ_ONLY":
            raise PermissionError("Server is in READ_ONLY mode. Command execution blocked.")
        if not isinstance(cmd_args, list) or not cmd_args:
            raise ValueError("Empty or invalid command")
        
        cmd = cmd_args[0]
        if cmd in self.blocked_commands:
            if self.level != "DESTRUCTIVE":
                 raise PermissionError(f"Command '{cmd}' is blocked in {self.level} mode.")
        if "&&" in cmd_args or ";" in cmd_args or "|" in cmd_args:
             raise PermissionError("Shell metacharacters are not allowed.")

class BridgeHandler(BaseHTTPRequestHandler):
    security = None 
    
    def log_message(self, format, *args):
        pass # Suppress default HTTP logging to keep stdout clean, we use our own

    def _send_response(self, status_code, payload):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode('utf-8'))

    def do_POST(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            self._send_response(401, {"error": "Missing or invalid authorization header"})
            return
            
        token = auth_header.split(" ")[1]
        if not self.security.validate_auth(token):
            self._send_response(401, {"error": "Unauthorized"})
            return

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            req = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            self._send_response(400, {"error": "Invalid JSON payload"})
            return
            
        action = req.get("action")
        args = req.get("args", {})
        
        logger.info(f"Action: {action}")
        
        try:
            if action == "list_dir":
                path = self.security.validate_path(args.get("path", ""), must_exist=True)
                items = os.listdir(path)
                self._send_response(200, {"success": True, "items": items})
                
            elif action == "read_file":
                path = self.security.validate_path(args.get("path", ""), must_exist=True)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self._send_response(200, {"success": True, "content": content})
                
            elif action == "write_file":
                if self.security.level == "READ_ONLY":
                    raise PermissionError("Write operations blocked in READ_ONLY mode.")
                path = self.security.validate_path(args.get("path", ""))
                
                parent = os.path.dirname(path)
                if parent and not os.path.exists(parent):
                    self.security.validate_path(parent)
                    os.makedirs(parent, exist_ok=True)
                    
                with open(path, "w", encoding="utf-8") as f:
                    f.write(args.get("content", ""))
                self._send_response(200, {"success": True, "message": "File written."})
                
            elif action == "delete":
                if self.security.level != "DESTRUCTIVE":
                    raise PermissionError("Delete blocked. Requires DESTRUCTIVE mode.")
                path = self.security.validate_path(args.get("path", ""), must_exist=True)
                if os.path.isdir(path):
                    os.rmdir(path)
                else:
                    os.remove(path)
                self._send_response(200, {"success": True, "message": "Deleted."})
                
            elif action == "execute":
                cmd = args.get("command", [])
                cwd = args.get("cwd")
                if cwd:
                    cwd = self.security.validate_path(cwd, must_exist=True)
                else:
                    cwd = self.security.allowed_dirs[0] if self.security.allowed_dirs else os.getcwd()
                    
                self.security.validate_command(cmd)
                timeout = int(args.get("timeout", 30))
                
                try:
                    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, shell=False)
                    self._send_response(200, {
                        "success": proc.returncode == 0,
                        "exit_code": proc.returncode,
                        "stdout": proc.stdout,
                        "stderr": proc.stderr,
                        "timed_out": False
                    })
                except subprocess.TimeoutExpired as e:
                    self._send_response(200, {
                        "success": False,
                        "exit_code": -1,
                        "stdout": e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or ""),
                        "stderr": e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or ""),
                        "timed_out": True
                    })
            else:
                self._send_response(400, {"error": f"Unknown action: {action}"})
                
        except PermissionError as e:
            logger.warning(f"Permission denied: {str(e)}")
            self._send_response(403, {"error": str(e)})
        except FileNotFoundError as e:
            self._send_response(404, {"error": str(e)})
        except Exception as e:
            logger.error(f"Internal error: {str(e)}")
            self._send_response(500, {"error": str(e)})

def run_server(host="127.0.0.1", port=8080, allowed_dirs=None, auth_token="secret", level="DEVELOPMENT"):
    if not allowed_dirs: allowed_dirs = [os.getcwd()]
    BridgeHandler.security = BridgeSecurity(allowed_dirs, auth_token, level)
    httpd = HTTPServer((host, port), BridgeHandler)
    logger.info(f"Bridge server running on {host}:{port} in {level} mode")
    httpd.serve_forever()
