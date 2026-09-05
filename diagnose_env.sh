echo "--- SYSTEM DIAGNOSTICS ---"
echo "CPU:"
lscpu | grep "Model name\|CPU(s):"
echo -e "\nRAM:"
free -h
echo -e "\nDISK:"
df -h /
echo -e "\nGPU:"
nvidia-smi || echo "No nvidia-smi found. GPU not available."
