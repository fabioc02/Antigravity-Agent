import os
import sys
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent.projects.manager import ProjectManager, TaskManager
from agent.core.runtime import RuntimeManager
from agent.core.loop import AgentCore
from agent.llm.provider import LocalQwenProvider

app = FastAPI(title="Antigravity Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_event(self, session_id: str, event: dict):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(event)
            except:
                self.disconnect(session_id)

ws_manager = ConnectionManager()

# Global state to keep track of running cores (for cancellation)
active_cores = {}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/projects")
def get_projects():
    drive_root = os.path.abspath("Drive/Agent")
    pm = ProjectManager(drive_root)
    # The pm stores projects in Drive/Agent/projects
    projs_dir = os.path.join(drive_root, "projects")
    projects = []
    if os.path.exists(projs_dir):
        for pid in os.listdir(projs_dir):
            if os.path.isdir(os.path.join(projs_dir, pid)):
                projects.append({"project_id": pid})
    return {"projects": projects}

@app.post("/projects")
async def create_project(request: Request):
    data = await request.json()
    drive_root = os.path.abspath("Drive/Agent")
    pm = ProjectManager(drive_root)
    pid = pm.create_project(data.get("name", "Untitled"), data.get("stack", "unknown"))
    return {"project_id": pid}

@app.post("/projects/{project_id}/tasks")
async def create_task(project_id: str, request: Request):
    data = await request.json()
    drive_root = os.path.abspath("Drive/Agent")
    tm = TaskManager(drive_root)
    tid = tm.create_task(project_id, data.get("title", "Task"), data.get("description", ""))
    return {"task_id": tid}

@app.get("/projects/{project_id}/tasks")
def get_tasks(project_id: str):
    drive_root = os.path.abspath("Drive/Agent")
    tm = TaskManager(drive_root)
    return {"tasks": tm.list_tasks(project_id)}

@app.websocket("/sessions/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await ws_manager.connect(session_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id)

def emit_event_sync(session_id: str, event_type: str, data: dict, loop=None):
    event = {"type": event_type, **data}
    if loop is None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # If no running loop in this thread, we can't emit easily without passing the main loop.
            pass
            
    if loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(ws_manager.send_event(session_id, event), loop)

@app.post("/agent/run")
async def run_agent(request: Request):
    data = await request.json()
    project_id = data["project_id"]
    task_id = data["task_id"]
    
    drive_root = os.path.abspath("Drive/Agent")
    ws_root = os.path.abspath(f"/tmp/workspace_{project_id}")
    
    rm = RuntimeManager(drive_root)
    rm.register_runtime()
    rm.acquire_lock()
    session_id = rm.start_session(task_id, project_id)
    
    from agent.llm.provider import LocalQwenProvider, ExternalAPIProvider
    try:
        provider = LocalQwenProvider("Qwen/Qwen2.5-Coder-7B-Instruct-AWQ")
    except Exception as e:
        print("Fallback to ExternalAPIProvider:", e)
        provider = ExternalAPIProvider()
    
    main_loop = asyncio.get_running_loop()
    
    # Custom emit callback wrapper
    def emit_cb(event_type, payload):
        emit_event_sync(session_id, event_type, payload, main_loop)

    core = AgentCore(provider, ws_root, rm, project_id=project_id, task_id=task_id)
    
    # Monkeypatch rm.append_message
    original_append = rm.append_message
    def append_with_events(sid, role, msg_content, iteration, metadata=None):
        original_append(sid, role, msg_content, iteration, metadata)
        if role == "assistant" or role == "system":
            emit_cb("llm_message", {"content": msg_content})
        elif role == "user":
            emit_cb("tool_result", {"result": msg_content})
            
    rm.append_message = append_with_events
    
    active_cores[session_id] = core
    
    # Run in background
    async def bg_task():
        # Wait 1 second to allow the frontend WebSocket to connect before emitting events
        await asyncio.sleep(1.0)
        
        emit_cb("session_started", {"project_id": project_id, "task_id": task_id})
        try:
            res = await asyncio.to_thread(core.run, 10, session_id)
            emit_cb("session_completed", {"result": res})
        except Exception as e:
            emit_cb("error", {"error": str(e)})
        finally:
            if session_id in active_cores:
                del active_cores[session_id]

    asyncio.create_task(bg_task())
    return {"session_id": session_id, "status": "running"}

@app.post("/sessions/{session_id}/cancel")
async def cancel_session(session_id: str):
    if session_id in active_cores:
        # We simulate cancellation by raising an exception or stopping loop.
        # Since loop is synchronous, hard to interrupt cleanly in python without threads.
        # For this prototype, we'll just remove it and mark.
        core = active_cores[session_id]
        core.status = "CANCELLED" # Assuming we can set a flag
        del active_cores[session_id]
        emit_event_sync(session_id, "session_completed", {"result": "CANCELLED"})
        return {"status": "cancelled"}
    return {"status": "not_found"}


from agent.bridge.client import BridgeClient
from agent.git.manager import GitManager
from agent.github.manager import GitHubManager

@app.get("/runtime")
def get_runtime():
    drive_root = os.path.abspath("Drive/Agent")
    rm = RuntimeManager(drive_root)
    state_path = os.path.join(rm.state_dir, "runtime_state.json")
    if os.path.exists(state_path):
        import json
        with open(state_path, "r") as f:
            return json.load(f)
    return {"status": "not_found"}

@app.get("/bridge/status")
def get_bridge_status():
    endpoint = os.environ.get('BRIDGE_ENDPOINT')
    token = os.environ.get('BRIDGE_TOKEN')
    if not endpoint or not token:
        return {"status": "BRIDGE_UNAVAILABLE", "error": "Bridge not configured"}
    client = BridgeClient(endpoint, token)
    res = client.list_dir("/")
    if "error" in res:
        return {"status": "OFFLINE", "details": res}
    return {"status": "ONLINE", "endpoint": endpoint}

@app.get("/github/status")
def get_github_status(project_id: str):
    ws_root = os.path.abspath(f"/tmp/workspace_{project_id}")
    if not os.path.exists(ws_root):
        return {"error": "Workspace not found"}
    git = GitManager(ws_root)
    gh = GitHubManager(ws_root)
    return {
        "remote": gh.check_config().get("remote_url"),
        "diff": git.diff()
    }

@app.get("/sessions")
def get_sessions():
    drive_root = os.path.abspath("Drive/Agent")
    sessions_dir = os.path.join(drive_root, "sessions")
    sessions = []
    if os.path.exists(sessions_dir):
        for sid in os.listdir(sessions_dir):
            if os.path.isdir(os.path.join(sessions_dir, sid)):
                import json
                spath = os.path.join(sessions_dir, sid, "session.json")
                if os.path.exists(spath):
                    with open(spath, "r") as f:
                        sessions.append(json.load(f))
    return {"sessions": sessions}

@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    drive_root = os.path.abspath("Drive/Agent")
    rm = RuntimeManager(drive_root)
    sess = rm.load_session(session_id)
    if sess: return sess
    return {"error": "not found"}

@app.post("/sessions/{session_id}/resume")
async def resume_session(session_id: str):
    drive_root = os.path.abspath("Drive/Agent")
    rm = RuntimeManager(drive_root)
    sess = rm.load_session(session_id)
    if not sess: return {"error": "not found"}
    
    project_id = sess["project_id"]
    task_id = sess["task_id"]
    ws_root = os.path.abspath(f"/tmp/workspace_{project_id}")
    
    rm.register_runtime()
    rm.acquire_lock()
    
    from agent.llm.provider import LocalQwenProvider, ExternalAPIProvider
    try:
        provider = LocalQwenProvider("Qwen/Qwen2.5-Coder-7B-Instruct-AWQ")
    except Exception as e:
        print("Fallback to ExternalAPIProvider:", e)
        provider = ExternalAPIProvider()
    
    main_loop = asyncio.get_running_loop()
    def emit_cb(event_type, payload):
        emit_event_sync(session_id, event_type, payload, main_loop)

    core = AgentCore(provider, ws_root, rm, project_id=project_id, task_id=task_id)
    
    original_append = rm.append_message
    def append_with_events(sid, role, msg_content, iteration, metadata=None):
        original_append(sid, role, msg_content, iteration, metadata)
        if role == "assistant" or role == "system":
            emit_cb("llm_message", {"content": msg_content})
        elif role == "user":
            emit_cb("tool_result", {"result": msg_content})
            
    rm.append_message = append_with_events
    active_cores[session_id] = core
    
    async def bg_task():
        await asyncio.sleep(1.0)
        emit_cb("session_resumed", {"project_id": project_id, "task_id": task_id})
        try:
            res = await asyncio.to_thread(core.run, 10, session_id)
            emit_cb("session_completed", {"result": res})
        except Exception as e:
            emit_cb("error", {"error": str(e)})
        finally:
            if session_id in active_cores:
                del active_cores[session_id]

    asyncio.create_task(bg_task())
    return {"session_id": session_id, "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)
