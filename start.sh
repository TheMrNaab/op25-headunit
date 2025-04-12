#!/bin/bash

# Launch the OP25 API and key mapping services
# Make this script executable with: chmod +x start.sh

echo "[INFO] Starting services..."

# Start the API service
if python3 api.py & then
    echo "[OK] api.py started successfully."
else
    echo "[ERROR] Failed to start api.py"
    exit 1
fi

# Start the keymap service (must be run as root)
if sudo python3 modules/keymap.py & then
    echo "[OK] keymap.py started successfully."
else
    echo "[ERROR] Failed to start keymap.py"
    exit 1
fi

echo "[INFO] All services started."