# OP25 Vehicle Scanner GUI

<p><img src="help/screenshot-updated.png" width="300"/> <img src="help/screenshot-animated.gif" width="300"/></p>

## Table of Contents
- [Overview](#overview)
- [User Interface](#user-interface)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running the Interface](#running-the-interface)

## Overview
![Relationship](/html/static/images/op25_root_relationship_corrected.png)

This project adds a touchscreen-friendly graphical interface to OP25, a software-defined radio (SDR) scanner. Designed for public safety personnel and radio enthusiasts, it offers a low-cost alternative to expensive commercial scanners like the Bearcat. The interface simplifies talkgroup scanning and monitoring in a vehicle without the high price tag.

## User Interface
The project serves the `/html` folder for the UI and uses `api.py` to handle interaction between the webpage and OP25. This setup uses fewer resources and allows layout flexibility based on screen size.

## Features
- **Touch-Friendly Interface**: HTML-based UI designed for in-vehicle use with touchscreen or mouse.
- **Talkgroup Management**: Supports whitelist, blacklist, and direct channel entry.
- **Scan Mode**: Dynamically reloads active talkgroups without restarting OP25.
- **Audio & Display**: Volume control and auto screen-off after inactivity (adjustable soon).
- **System Support**: Current version supports one P25 system; multi-system functionality is in development.
- **Direct Configuration**: Web-based setup replaces manual file edits; Info button opens settings panel.
- **Default Audio Routing**: Defaults to system's primary output; device selection coming in a future update.
- **Configurable Parameters**: Future versions will pull from `config.ini`; current version uses hardcoded values.

## Requirements

### Hardware
- SDR-compatible Linux-based device (x86 or ARM)  
- RTL-SDR USB dongle  
- Touchscreen display (or any monitor with mouse input)  

### Software
- **Operating System**: Lightweight Linux OS recommended (e.g., Ubuntu Server).
- **Dependencies**:  
  - `OP25` (installed at `/home/(user)/op25`)    
  - `pyttsx3` for text-to-speech (upcoming feature)  
  - `firefox-esr` for interface display in kiosk mode  
  - `flask` for serving API and webpages  
  - `openbox` for graphical session management (if no GUI installed)

## Installation Steps

## Managed Systems (e.g., PiOS)

1. Ensure Python tools are installed:
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv -y
   ```

2. Use a virtual environment to isolate dependencies:
   ```bash
   cd /opt/op25-project
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. After reboot or logout, reactivate the environment:
   ```bash
   source /opt/op25-project/venv/bin/activate
   ```

## Running the Interface

### Managed Systems

1. Activate the virtual environment:
   ```bash
   source /opt/op25-project/venv/bin/activate
   ```

2. Run the API server:
   ```bash
   python api.py
   ```

3. Launch Firefox in kiosk mode:
   ```bash
   firefox-esr --kiosk http://localhost:8000
   ```

4. If using an air mouse HID remote (new feature), add the following line:
   ```bash
   # NOTE: This script will disable keyboard entry; it is in beta.
   sudo python modules/keymap.py &
   ```
   Read additional remote documentation [here](/modules/readme_remote.md).

## Configuration

1. After launching `api.py`, open a web browser on the Linux system and navigate to:  
   `http://localhost:8000/admin/index.html`

2. In the Admin Portal, adjust OP25 settings to match your hardware and system preferences.

3. Configure the radio system, save your changes, and restart the device to apply the configuration. 

## Contributing
Pull requests are welcome. For major changes, open an issue first to discuss what you would like to change.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

