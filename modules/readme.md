# Remote Control Interface for OP25

`remote.py` is a background Python process that listens for keypresses from a USB remote control or keyboard-like HID device. It intercepts and cancels the original keystrokes and sends API requests to the OP25 scanner web interface to trigger scanner functions.

This script enables full remote operation of the OP25 headunit, especially useful for touchscreen or embedded vehicle setups where physical buttons are used for channel and zone control.

## Features

- Detects and cancels keyboard events from a connected remote
- Sends API requests to trigger zone, channel, volume, and keypad actions
- Integrates with the existing OP25 JavaScript interface
- Runs in the background for seamless remote control

## Key Mappings

The following key names are captured and mapped to scanner actions:

### Navigation & Selection

- **`enter_ok`**  
  - Confirms selection in zone or channel modal  
  - If no modal is open, opens the keypad

- **`rewind`**  
  - Opens the **channel selection modal** (only if no modals are open)

- **`fastforward`**  
  - Opens the **zone selection modal** (only if no modals are open)

- **`skip back`**  
  - Opens the **keypad modal** for direct channel entry

- **`back`**  
  - Closes any open modal: zone, channel, or keypad

### Directional Control

- **`up`**  
  - Scrolls up in the channel or zone modal

- **`down`**  
  - Scrolls down in the channel or zone modal

- **`left`**  
  - Cycles backward through zone options in the keypad modal

- **`right`**  
  - Cycles forward through zone options in the keypad modal

### Volume

- **`vol down`**  
  - Lowers volume by 10%

- **`vol up`**  
  - Raises volume by 10%

### Keypad Input

- **`delete`**  
  - Deletes last digit entered in the keypad modal

- **Numeric Keys (`0â9`)**  
  - Appended to the current channel number input in the keypad modal

## Installation

1. Ensure the remote control device is recognized as a keyboard-type HID.
2. Install Python dependencies:
   ```bash
   pip install keyboard requests
   ```
3. Place `remote.py` alongside your OP25 project.
4. Ensure the script runs with elevated privileges (required by `keyboard`):
   ```bash
   sudo python3 remote.py
   ```

## Optional: Run as a Background Service

To run `remote.py` as a systemd service:

1. Create a service file `/etc/systemd/system/op25-remote.service`:
   ```ini
   [Unit]
   Description=OP25 Remote HID Listener
   After=network.target

   [Service]
   ExecStart=/usr/bin/python3 /opt/op25-project/modules/_remote.py
   WorkingDirectory=/opt/op25-project/modules
   Restart=always
   User=root

   [Install]
   WantedBy=multi-user.target
   ```

2. Enable and start the service:
   ```bash
   sudo systemctl enable op25-remote
   sudo systemctl start op25-remote
   ```
