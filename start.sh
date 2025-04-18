#!/bin/bash

# Usage: ./start.sh [-K]
# -K : Start keymap.py (requires sudo)

echo "[INFO] Activating virtual environment..."
source ~/op25-venv/bin/activate

# Capture venv Python path and site-packages
VENV_PYTHON=$(which python3)
export PYTHONPATH=$($VENV_PYTHON -c "import site; print(site.getsitepackages()[0])")
export PATH=$(dirname "$VENV_PYTHON"):$PATH

echo "[INFO] Starting api.py..."

# Start the API service
if "$VENV_PYTHON" api.py & then
    echo "[OK] api.py started successfully."
else
    echo "[ERROR] Failed to start api.py"
    exit 1
fi

# Parse arguments
START_KEYMAP=false
while getopts "K" opt; do
    case $opt in
        K) START_KEYMAP=true ;;
    esac
done

# Start keymap.py only if -K flag is present
if $START_KEYMAP; then
    echo "[INFO] Starting keymap.py..."
    if sudo -E "$VENV_PYTHON" modules/keymap.py & then
        echo "[OK] keymap.py started successfully."
    else
        echo "[ERROR] Failed to start keymap.py"
        exit 1
    fi
fi

echo "[INFO] All services started."