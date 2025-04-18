#!/bin/bash

SERVICE_NAME="op25-launcher"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME.service"

# Check if the service already exists
if [ -f "$SERVICE_PATH" ]; then
    echo "[INFO] Autostart service '$SERVICE_NAME' already exists."
    read -p "Do you want to uninstall it? [y/N]: " UNINSTALL

    case "$UNINSTALL" in
        [Yy]* )
            echo "[INFO] Disabling and removing service..."
            sudo systemctl disable "$SERVICE_NAME"
            sudo systemctl stop "$SERVICE_NAME"
            sudo rm -f "$SERVICE_PATH"
            sudo systemctl daemon-reload
            echo "[OK] Service removed."
            exit 0
            ;;
        * )
            echo "[INFO] Leaving existing service untouched."
            exit 0
            ;;
    esac
fi

echo "This script will configure OP25 to start automatically when Raspberry Pi OS boots."
echo ""
echo "It will:"
echo "  - Create a systemd service"
echo "  - Optionally include keymap.py (which runs with sudo)"
echo "  - Optionally launch the web interface in full screen"
echo ""
read -p "Do you want to continue? [y/N]: " CONTINUE

case "$CONTINUE" in
    [Yy]* ) ;;
    * ) echo "Aborted."; exit 0 ;;
esac

# Ask about keymap.py
read -p "Do you want to include keymap.py at boot? [y/N]: " INCLUDE_KEYMAP
KEYMAP_LINE=""
case "$INCLUDE_KEYMAP" in
    [Yy]* )
        KEYMAP_LINE="sudo /home/dnaab/op25-venv/bin/python3 /opt/op25-project/modules/keymap.py &"
        ;;
esac

# Ask about launching Chromium
read -p "Do you want to launch the web interface in Chromium kiosk mode? [y/N]: " LAUNCH_BROWSER
CHROMIUM_LINE=""
case "$LAUNCH_BROWSER" in
    [Yy]* )
        CHROMIUM_LINE="sleep 5 && DISPLAY=:0 /usr/bin/chromium-browser --kiosk http://localhost:8000"
        ;;
esac

echo "[INFO] Creating systemd service: $SERVICE_NAME"

sudo tee "$SERVICE_PATH" > /dev/null <<EOF
[Unit]
Description=Start OP25 Services at Boot
After=network.target graphical.target

[Service]
Type=simple
User=dnaab
WorkingDirectory=/opt/op25-project
ExecStart=/bin/bash -c '/home/dnaab/op25-venv/bin/python3 /opt/op25-project/api.py & $KEYMAP_LINE $CHROMIUM_LINE'
Restart=on-failure
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical.target
EOF

# Enable the service
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"

echo "[OK] Autostart service created and enabled."
echo "It will run on next boot."