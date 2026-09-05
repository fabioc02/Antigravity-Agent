import json
import re
from typing import List, Dict
from agent.tools.filesystem import ListDirectoryTool, ReadFileTool, WriteFileTool
from agent.tools.terminal import TerminalExecuteTool
from agent.security.sandbox import SecuritySandbox
from agent.llm.provider import LLMProvider

class AgentCore:
    def __init__(self, llm_provider: LLMProvider, workspace_root: str):
        self.llm = llm_provider
        self.sandbox = SecuritySandbox(workspace_root)
        self.tools = {
            "filesystem.list": ListDirectoryTool(self.sandbox),
            "filesystem.read": ReadFileTool(self.sandbox),
            "filesystem.write": WriteFileTool(self.sandbox),
            "terminal.execute": TerminalExecuteTool(self.sandbox)
        }
        self.history = []

    def run(self, task: str, max_iterations: int = 15) -> str:
        system_prompt = "You are an autonomous agent. Available tools:\n"
        for name, t in self.tools.items():
            system_prompt += f"- {name}: {t.description}\n"
        system_prompt += "\nFormat calls as JSON block: ```json\n{\"tool\": \"name\", \"args\": {}}\n```. If done, say TAREFA CONCLUIDA."
        
        prompt = f"SYSTEM: {system_prompt}\n\nUSER: {task}\n\nASSISTANT: "
        
        for i in range(max_iterations):
            print(f"--- Iteration {i+1} ---")
            try:
                response = self.llm.generate(prompt)
                print(f"[LLM] {response}")
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
                        prompt += f"USER: Tool Result:\n{result}\n\nASSISTANT: "
                    else:
                        prompt += f"USER: Error: Tool {tool_name} not found.\n\nASSISTANT: "
                else:
                    prompt += "USER: Error: No valid JSON tool call found.\n\nASSISTANT: "
            except Exception as e:
                print(f"Loop error: {e}")
                return "ERROR"
        return "MAX_ITERATIONS_REACHED"
