import json
import re
from typing import List, Dict
from agent.tools.filesystem import ListDirectoryTool, ReadFileTool, WriteFileTool
from agent.tools.terminal import TerminalExecuteTool
from agent.security.sandbox import SecuritySandbox
from agent.llm.provider import LLMProvider

class AgentCore:
    def __init__(self, llm_provider: LLMProvider, workspace_root: str, runtime_manager=None, project_id=None, task_id=None):
        self.llm = llm_provider
        self.sandbox = SecuritySandbox(workspace_root)
        self.rm = runtime_manager
        self.project_id = project_id
        self.task_id = task_id
        self.tools = {
            "filesystem.list": ListDirectoryTool(self.sandbox),
            "filesystem.read": ReadFileTool(self.sandbox),
            "filesystem.write": WriteFileTool(self.sandbox),
            "terminal.execute": TerminalExecuteTool(self.sandbox)
        }
        self.history = []

    def run(self, max_iterations: int = 15, session_id: str = None) -> str:
        self.session_id = session_id
        
        from agent.projects.manager import TaskManager
        tm = TaskManager(self.rm.drive_root)
        task_data = tm.get_task(self.project_id, self.task_id)
        if not task_data:
            return "ERROR: Task not found"
            
        task_description = f"{task_data.get('title', '')}\n{task_data.get('description', '')}"

        system_prompt = "You are an autonomous agent. Available tools:\n"
        for name, t in self.tools.items():
            system_prompt += f"- {name}: {t.description}\n"
        system_prompt += "\nFormat calls as JSON block: ```json\n{\"tool\": \"name\", \"args\": {}}\n```. If done, say TAREFA CONCLUIDA."
        
        prompt = f"SYSTEM: {system_prompt}\n\nUSER: {task_description}\n\nASSISTANT: "
        if self.rm and self.session_id:
            self.rm.append_message(self.session_id, "system", system_prompt, 0)
            self.rm.append_message(self.session_id, "user", task_description, 0)
        
        for i in range(max_iterations):
            print(f"--- Iteration {i+1} ---")
            try:
                response = self.llm.generate(prompt)
                print(f"[LLM] {response}")
                if self.rm and self.session_id:
                    self.rm.append_message(self.session_id, "assistant", response, i+1)
                
                prompt += response + "\n\n"
                
                if "TAREFA CONCLUIDA" in response:
                    return "SUCCESS"
                    
                match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
                if match:
                    tool_call = json.loads(match.group(1))
                    tool_name = tool_call.get("tool")
                    args = tool_call.get("args", {})
                    
                    if tool_name in self.tools:
                        result = self.tools[tool_name].execute(**args)
                        print(f"[TOOL {tool_name}] {result}")
                        if self.rm and self.session_id:
                            self.rm.append_message(self.session_id, "user", str(result), i+1)
                        prompt += f"USER: Tool Result:\n{result}\n\nASSISTANT: "
                    else:
                        err = f"Error: Tool {tool_name} not found."
                        if self.rm and self.session_id:
                            self.rm.append_message(self.session_id, "user", err, i+1)
                        prompt += f"USER: {err}\n\nASSISTANT: "
                else:
                    err = "Error: No valid JSON tool call found."
                    if self.rm and self.session_id:
                        self.rm.append_message(self.session_id, "user", err, i+1)
                    prompt += f"USER: {err}\n\nASSISTANT: "
            except Exception as e:
                print(f"Loop error: {e}")
                if self.rm and self.session_id:
                    self.rm.append_message(self.session_id, "system", f"Loop error: {e}", i+1)
                return "ERROR"
        return "MAX_ITERATIONS_REACHED"
