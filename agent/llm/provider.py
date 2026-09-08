import os
import sys
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    is_cpu_mode: bool = False
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass

class LocalQwenProvider(LLMProvider):
    def __init__(self, model_name: str):
        self.model_name = model_name
        import torch
        
        self.use_gpu = torch.cuda.is_available()
        self.is_cpu_mode = not self.use_gpu
        
        if self.use_gpu:
            print("[LLM] GPU detected. Initializing Qwen in Agent mode via vLLM.")
            try:
                from vllm import LLM, SamplingParams
                from transformers import AutoTokenizer
                self.llm = LLM(model=model_name, quantization="awq", trust_remote_code=True, gpu_memory_utilization=0.9, max_model_len=4096)
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.params = SamplingParams(temperature=0.1, max_tokens=1024)
            except ImportError:
                print("[LLM] vLLM not found. Falling back to Transformers on GPU.")
                from transformers import AutoModelForCausalLM, AutoTokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    device_map="auto",
                    torch_dtype=torch.float16,
                    trust_remote_code=True
                )
                self.use_gpu = False # Treat as standard huggingface model flow
                self.is_cpu_mode = False
        else:
            print("[LLM] No GPU detected. Initializing Qwen in Chatbot mode (CPU).")
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="cpu",
                torch_dtype=torch.float16,
                trust_remote_code=True
            )

    def generate(self, prompt: str) -> str:
        if self.use_gpu:
            outputs = self.llm.generate([prompt], self.params, use_tqdm=False)
            return outputs[0].outputs[0].text
        else:
            inputs = self.tokenizer(prompt, return_tensors="pt").to("cpu")
            outputs = self.model.generate(**inputs, max_new_tokens=1024, temperature=0.1)
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

import urllib.request
import json

class ExternalAPIProvider(LLMProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.is_cpu_mode = True # Default to CPU behavior (lightweight) if using external fallback without GPU
        
        if self.api_key:
            print("[LLM] ExternalAPIProvider initialized with Gemini API.")
        else:
            print("[LLM] ExternalAPIProvider initialized as fallback. Emulating responses without PyTorch.")
            
    def generate(self, prompt: str) -> str:
        if self.api_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
            data = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1}
            }
            req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(req) as response:
                    res_body = response.read()
                    res_json = json.loads(res_body)
                    return res_json['candidates'][0]['content']['parts'][0]['text']
            except Exception as e:
                return f"```json\n{{\"tool\": \"terminal.execute\", \"args\": {{\"command\": \"echo 'Erro ao acessar Gemini API: {e}'\"}}}}\n```\nTAREFA CONCLUIDA."

        # Mock logic to parse the user's intent from the prompt if no API key is provided
        if "index.html" in prompt and "Successfully wrote" in prompt:
            return 'O arquivo index.html foi criado com sucesso no seu workspace e salvo no Google Drive.\nTAREFA CONCLUIDA.'
            
        if "crie um jogo em html" in prompt.lower() or "crie do zero um aplicativo" in prompt.lower():
            return '```json\n{"tool": "filesystem.write", "args": {"path": "index.html", "content": "<html><body><h1>Jogo HTML Gerado (Mock CPU sem Chave)</h1></body></html>"}}\n```\n'
        
        # Default generic response for testing the UI
        return '```json\n{"tool": "terminal.execute", "args": {"command": "echo \'Fallback CPU executado com sucesso\'"}}\n```\nTAREFA CONCLUIDA.'


