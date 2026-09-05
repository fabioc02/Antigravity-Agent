#!/bin/bash
set -e

echo "=== AGENT BOOTSTRAP ==="

DRIVE_ROOT=$(cd "$(dirname "$0")/.." && pwd)
REQUIREMENTS_BASE="$DRIVE_ROOT/requirements/requirements-base.txt"
REQUIREMENTS_QWEN="$DRIVE_ROOT/requirements/requirements-qwen.txt"

echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "Python3 is required but not installed."
    exit 1
fi

echo "Checking pip..."
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is required but not installed."
    exit 1
fi

echo "Installing base requirements..."
pip3 install -q --break-system-packages -r "$REQUIREMENTS_BASE"

echo "Detecting GPU..."
HAS_GPU=0
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi | grep -q "Tesla"; then
        HAS_GPU=1
        echo "GPU Detected (Tesla). Installing Qwen requirements..."
        pip3 install -q --break-system-packages -r "$REQUIREMENTS_QWEN"
    else
        echo "GPU Detected but not Tesla. Proceeding with caution."
        HAS_GPU=1
    fi
else
    echo "No GPU detected. Running in API Fallback mode."
fi

# Ensure bin is executable
chmod +x "$DRIVE_ROOT/bin/agent"
# Optionally, add to PATH if running in an interactive shell
# export PATH="$DRIVE_ROOT/bin:$PATH"

echo "Bootstrap complete."
