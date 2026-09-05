import os
import sys

def get_hardware_profile():
    profile = {
        "gpu": False,
        "gpu_name": None,
        "vram_total_gb": 0,
        "ram_total_gb": 0,
        "cpu_cores": 0,
        "cuda_available": False,
        "recommended_model": None,
        "recommended_backend": None
    }
    
    # Check RAM
    try:
        import psutil
        ram = psutil.virtual_memory()
        profile["ram_total_gb"] = ram.total / (1024**3)
        profile["cpu_cores"] = psutil.cpu_count(logical=True)
    except ImportError:
        # Fallback if psutil not installed
        pass

    # Check GPU
    try:
        import torch
        if torch.cuda.is_available():
            profile["gpu"] = True
            profile["cuda_available"] = True
            profile["gpu_name"] = torch.cuda.get_device_name(0)
            profile["vram_total_gb"] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    except ImportError:
        pass

    # Model Selection Logic
    if profile["gpu"] and profile["vram_total_gb"] >= 15:
        # T4 16GB
        profile["recommended_model"] = "Qwen/Qwen2.5-Coder-7B-Instruct-AWQ"
        profile["recommended_backend"] = "vLLM"
        profile["notes"] = "Fits comfortably in 16GB VRAM. Fast inference with vLLM. Excellent tool calling."
    elif profile["gpu"] and profile["vram_total_gb"] >= 8:
        # 8GB VRAM
        profile["recommended_model"] = "Qwen/Qwen2.5-Coder-3B-Instruct-AWQ"
        profile["recommended_backend"] = "vLLM"
        profile["notes"] = "Good for 8GB GPUs."
    else:
        # CPU or Low RAM (Like our current 4GB container)
        profile["recommended_model"] = "Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF"
        profile["recommended_backend"] = "llama.cpp"
        profile["notes"] = "CPU fallback or extremely low RAM environment. Quantized GGUF required."

    return profile

if __name__ == "__main__":
    prof = get_hardware_profile()
    print("--- HARDWARE DIAGNOSTICS ---")
    for k, v in prof.items():
        print(f"{k}: {v}")
