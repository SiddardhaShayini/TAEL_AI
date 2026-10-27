#!/usr/bin/env bash
# TAEL V3 One-Command Setup & Launch Script for Linux / macOS
# Run via: bash setup.sh

set -e

echo "======================================================"
echo " TAEL V3: Task-Adaptive Efficient Language AI Setup   "
echo " 'Capable local AI, built for everyday hardware.'     "
echo "======================================================"

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "[!] Error: python3 is required but was not found on PATH."
    exit 1
fi

echo "[+] Python found: $(python3 --version)"

# 2. Check / Install uv
if ! command -v uv &> /dev/null; then
    echo "[*] Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# 3. Create Virtual Environment
if [ ! -d ".venv" ]; then
    echo "[*] Creating virtual environment (.venv)..."
    uv venv
fi

# 4. Install TAEL
echo "[*] Installing TAEL V3 dependencies..."
uv pip install -e ".[dev]"

# 5. Run Diagnostics
echo -e "\n[*] Running First-Run System Check..."
.venv/bin/tael doctor

echo -e "\n======================================================"
echo " TAEL V3 Setup Successfully Completed!"
echo " Start interactive coding: .venv/bin/tael chat"
echo " System status:            .venv/bin/tael status"
echo "======================================================"
