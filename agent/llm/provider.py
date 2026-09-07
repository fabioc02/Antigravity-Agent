import os
import sys
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass

class LocalQwenProvider(LLMProvider):
    def __init__(self, model_name: str):
        self.model_name = model_name
        import torch
        
        self.use_gpu = torch.cuda.is_available()
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
        else:
            print("[LLM] No GPU detected. Initializing Qwen in Chatbot mode (CPU).")
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="cpu",
                torch_dtype=torch.float32,
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

class ExternalAPIProvider(LLMProvider):
    def __init__(self, api_key: str = None):
        print("ExternalAPIProvider initialized as fallback. Real model failed to load.")
        pass
        
    def generate(self, prompt: str) -> str:
        return '```json\n{"tool": "terminal.execute", "args": {"command": "echo \'AVISO: O modelo Qwen falhou ao carregar (possivelmente falta o Pytorch/Transformers no ambiente). Para o agente funcionar de verdade, inicie o ambiente no Google Colab com as dependências corretas.\'"}}\n```\nTAREFA CONCLUIDA.'

