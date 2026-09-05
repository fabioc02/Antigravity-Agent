import os
import json
import urllib.request
import time
from typing import List, Dict, Any

class QwenProvider:
    def __init__(self, mode: str = "auto"):
        self.mode = mode
        self.local_llm = None
        self.model_name = "Qwen/Qwen2.5-Coder-7B-Instruct-AWQ"

    def initialize_local(self, model_path: str, backend: str):
        print(f"[QwenProvider] Inicializando modelo local {model_path} via {backend}...")
        try:
            import torch
            if torch.cuda.is_available():
                from vllm import LLM, SamplingParams
                self.local_llm = LLM(model=model_path, quantization="awq", trust_remote_code=True, gpu_memory_utilization=0.9, max_model_len=4096)
                self.mode = "local_gpu"
                print("[QwenProvider] GPU ativada com sucesso via vLLM.")
            else:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
                self.local_llm = AutoModelForCausalLM.from_pretrained(
                    model_path, device_map="cpu", torch_dtype=torch.float32, trust_remote_code=True
                )
                self.mode = "local_cpu"
                print("[QwenProvider] CPU ativada com sucesso.")
        except Exception as e:
            print(f"[QwenProvider] Erro ao inicializar modelo: {e}")
            self.mode = "error"

    def generate_content(self, messages: List[Dict], tools: List[Dict] = None) -> Dict:
        if self.mode == "fallback_api":
            return {"error": "API externa (Gemini) foi desativada. Qwen local eh obrigatorio."}
        
        # Fake interface to respect old call
        prompt = ""
        for m in messages:
            prompt += f"{m.get('role', 'user')}: {m.get('content', '')}\n"
            
        if self.mode == "local_gpu" and self.local_llm:
            from vllm import SamplingParams
            params = SamplingParams(temperature=0.1, max_tokens=1024)
            outputs = self.local_llm.generate([prompt], params, use_tqdm=False)
            return {"text": outputs[0].outputs[0].text}
            
        if self.mode == "local_cpu" and self.local_llm:
            inputs = self.tokenizer(prompt, return_tensors="pt").to("cpu")
            outputs = self.local_llm.generate(**inputs, max_new_tokens=1024, temperature=0.1)
            text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return {"text": text}
            
        return {"error": "Modo não suportado ou modelo nao inicializado."}
