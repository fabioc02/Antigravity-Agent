import json
from qwen_agent_colab.core.qwen_provider import QwenProvider

class AutonomousAgent:
    def __init__(self, provider: QwenProvider, tool_schemas: list, tool_funcs: dict):
        self.provider = provider
        self.tool_schemas = tool_schemas
        self.tool_funcs = tool_funcs
        self.history = []
        self.cwd = "."

    def run(self, task: str, max_iterations: int = 15):
        self.history = [
            {"role": "user", "parts": [{"text": task}]}
        ]
        
        print("\n==============================================")
        print("🤖 INICIANDO LOOP AUTÔNOMO")
        print(f"Task: {task}")
        print("==============================================\n")

        for i in range(max_iterations):
            print(f"--- Iteração {i+1} ---")
            res = self.provider.generate_content(self.history, self.tool_schemas)
            
            if "error" in res:
                print("🚨 ERRO NA INFERÊNCIA:", res)
                break
                
            try:
                candidate = res.get("candidates", [{}])[0]
                content = candidate.get("content", {})
                parts = content.get("parts", [])
                
                if not parts:
                    print("Agente retornou vazio.")
                    break
                    
                self.history.append({"role": "model", "parts": parts})
                
                has_tool_call = False
                for part in parts:
                    if "text" in part:
                        print(f"🧠 [Thought] {part['text'].strip()}")
                        
                    if "functionCall" in part:
                        has_tool_call = True
                        fc = part["functionCall"]
                        name = fc["name"]
                        args = fc.get("args", {})
                        print(f"🛠️  [Tool Call] {name}({args})")
                        
                        if name not in self.tool_funcs:
                            error_msg = f"Error: Tool {name} not found"
                            print(f"❌ [Tool Error] {error_msg}")
                            self.history.append({
                                "role": "user",
                                "parts": [{"functionResponse": {"name": name, "response": {"name": name, "content": error_msg}}}]
                            })
                            continue
                            
                        # Execute real tool
                        try:
                            # Inject CWD dynamically if the tool expects it
                            if "cwd" in args and name != "execute_command":
                                # Assuming tools expect explicit paths, or we inject it
                                pass
                            
                            func = self.tool_funcs[name]
                            result = func(**args)
                            
                            # Simple stringification of result
                            res_str = str(result)
                            
                            # Log exit codes for Error Analysis
                            if "Exit Code:" in res_str and "Exit Code: 0" not in res_str:
                                print(f"⚠️ [Error Analysis Triggered] {res_str.splitlines()[0]}")
                            else:
                                print(f"✅ [Tool Result] Sucesso (Tamanho: {len(res_str)} chars)")

                            self.history.append({
                                "role": "user",
                                "parts": [{"functionResponse": {"name": name, "response": {"name": name, "content": res_str}}}]
                            })
                            
                        except Exception as ex:
                            err_msg = f"Exception executing {name}: {str(ex)}"
                            print(f"❌ [Tool Exception] {err_msg}")
                            self.history.append({
                                "role": "user",
                                "parts": [{"functionResponse": {"name": name, "response": {"name": name, "content": err_msg}}}]
                            })
                
                if not has_tool_call:
                    print("\n🏁 Agente finalizou a tarefa (Nenhuma nova ferramenta chamada).")
                    break
                    
            except Exception as e:
                print("Exception no loop do agente:", e, res)
                break
