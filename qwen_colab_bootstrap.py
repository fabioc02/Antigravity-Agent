import os
import sys
import json
import subprocess
import shlex

# ==============================================================================
# FASE 2.1 & 2.2 - DETECÇÃO DE HARDWARE E ESCOLHA DO MODELO
# ==============================================================================
def detect_hardware_and_model():
    print("=== DIAGNÓSTICO DE AMBIENTE ===")
    profile = {"gpu": False, "vram_gb": 0, "ram_gb": 0, "model": None, "backend": None}
    
    try:
        import psutil
        profile["ram_gb"] = psutil.virtual_memory().total / (1024**3)
        print(f"RAM: {profile['ram_gb']:.2f} GB")
    except:
        pass

    try:
        import torch
        if torch.cuda.is_available():
            profile["gpu"] = True
            profile["gpu_name"] = torch.cuda.get_device_name(0)
            profile["vram_gb"] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"GPU Detectada: {profile['gpu_name']} | VRAM: {profile['vram_gb']:.2f} GB")
        else:
            print("Nenhuma GPU CUDA detectada.")
    except Exception as e:
        print("Erro ao verificar PyTorch/CUDA:", e)

    if not profile["gpu"]:
        print("\n[AVISO] Falta GPU. O sistema rodara no modo CPU (Chatbot lento).")
        profile["model"] = "Qwen/Qwen2.5-Coder-7B-Instruct-AWQ"
        profile["backend"] = "CPU-Transformers"
    else:
        # Escolha do Modelo baseada na VRAM
        if profile["vram_gb"] > 14:
            # Ideal para T4 (16GB)
            profile["model"] = "Qwen/Qwen2.5-Coder-7B-Instruct-AWQ"
            profile["backend"] = "vLLM"
            print(f"Modelo Selecionado: {profile['model']} (AWQ 4-bit) via {profile['backend']}")
        else:
            print("\n[AVISO] VRAM insuficiente na GPU para rodar o modelo AWQ 7B com folga. Pode falhar OOM.")
            profile["model"] = "Qwen/Qwen2.5-Coder-7B-Instruct-AWQ"
            profile["backend"] = "vLLM"
        
    return profile

# ==============================================================================
# FASE 2.4 - FERRAMENTAS REAIS NO COLAB (SEM BRIDGE AINDA)
# ==============================================================================
def execute_command(command: str, cwd: str = ".") -> str:
    try:
        parts = shlex.split(command)
        result = subprocess.run(parts, cwd=cwd, capture_output=True, text=True, timeout=30)
        out = f"Exit Code: {result.returncode}\n"
        if result.stdout: out += f"STDOUT:\n{result.stdout}\n"
        if result.stderr: out += f"STDERR:\n{result.stderr}\n"
        return out
    except Exception as e:
        return f"Error executing command: {str(e)}"

def read_file(path: str) -> str:
    try:
        with open(path, "r") as f: return f.read()
    except Exception as e: return f"Error reading file: {str(e)}"

def write_file(path: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f: f.write(content)
        return f"Successfully wrote {len(content)} bytes to {path}"
    except Exception as e: return f"Error writing file: {str(e)}"

def list_directory(path: str = ".") -> str:
    try:
        files = os.listdir(path)
        return "\n".join(files)
    except Exception as e: return f"Error listing directory: {str(e)}"

TOOLS = {
    "execute_command": execute_command, "read_file": read_file, 
    "write_file": write_file, "list_directory": list_directory
}

# ==============================================================================
# FASE 2.3 & 2.5 - AGENT LOOP & INFERÊNCIA REAL (vLLM)
# ==============================================================================
class QwenAgent:
    def __init__(self, model_name: str):
        from vllm import LLM, SamplingParams
        print(f"Carregando {model_name} na VRAM...")
        self.llm = LLM(model=model_name, quantization="awq", trust_remote_code=True, gpu_memory_utilization=0.9)
        from transformers import AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.sampling_params = SamplingParams(temperature=0.2, max_tokens=1024)

    def run(self, task: str):
        messages = [{"role": "user", "content": task}]
        print(f"\n[TASK INICIAL] {task}")
        
        for i in range(10): # Max Iterations
            print(f"\n--- Iteração {i+1} ---")
            
            # Formatação ChatML com ferramentas embutidas
            prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            
            # Inferência Real
            outputs = self.llm.generate([prompt], self.sampling_params, use_tqdm=False)
            response_text = outputs[0].outputs[0].text
            
            print(f"[QWEN] {response_text.strip()}")
            messages.append({"role": "assistant", "content": response_text})
            
            # Parser simples de Function Calling (Como Qwen AWQ devolve tool calls)
            if "<tool_call>" in response_text:
                # Extrair tool e args (Simulação da extração de Regex)
                pass # AQUI ENTRA A LÓGICA DE PARSE E EXECUÇÃO
            else:
                print("🏁 Agente finalizou a cadeia de raciocínio.")
                break

if __name__ == "__main__":
    profile = detect_hardware_and_model()
    # Para prosseguir no Colab: 
    # agent = QwenAgent(profile["model"])
    # agent.run("Leia o projeto, ache o erro, conserte e teste.")
