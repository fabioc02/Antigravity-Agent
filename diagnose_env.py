import os
import psutil
import shutil

print("--- SYSTEM DIAGNOSTICS ---")

# CPU
print(f"CPU Cores: {psutil.cpu_count(logical=True)}")

# RAM
ram = psutil.virtual_memory()
print(f"Total RAM: {ram.total / (1024**3):.2f} GB")
print(f"Available RAM: {ram.available / (1024**3):.2f} GB")

# Disk
disk = shutil.disk_usage('/')
print(f"Total Disk: {disk.total / (1024**3):.2f} GB")
print(f"Free Disk: {disk.free / (1024**3):.2f} GB")

# GPU
has_gpu = False
try:
    import subprocess
    nvidia_smi = subprocess.check_output("nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader", shell=True).decode()
    print("GPU Info:\n" + nvidia_smi.strip())
    has_gpu = True
except Exception as e:
    print("GPU Info: No NVIDIA GPU detected or nvidia-smi failed.")

if not has_gpu:
    print("\nWARNING: No GPU detected. Running local LLMs will be extremely slow (CPU-bound).")
