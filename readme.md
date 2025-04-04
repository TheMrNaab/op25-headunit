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
- **Dedicated Storage**: Use a dedicated SSD or SD card to avoid data loss.  

### Software
- **Operating System**: Lightweight Linux OS recommended (e.g., Ubuntu Server).
- **Dependencies**:  
  - `OP25` (installed at `/home/(user)/op25`)    
  - `pyttsx3` for text-to-speech (upcoming feature)  
  - `firefox-esr` for interface display in kiosk mode  
  - `flask` for serving API and webpages  
  - `openbox` for graphical session management (GUI-based systems only)


## Installation Steps

1. Clone and install Boatbod's OP25 software
2. Clone this repository to `/opt/op25-project`
3. Install missing dependencies using `requirements.txt`

## Running the Interface

1. Run `api.py` in a terminal window, then open `http://localhost:8000` in your web browser.  
2. To launch this automatically at startup and open in kiosk mode, install `firefox-esr` and use a startup script like the one below:

```bash
#!/bin/bash

# Start API server
cd /opt/op25-project
python3 api.py &

# Wait briefly to ensure the server starts
sleep 5

# Launch Firefox in kiosk mode
firefox-esr --kiosk http://localhost:8000
’’’

## Contributing
Pull requests are welcome. For major changes, open an issue first to discuss what you would like to change.

## License
This project is licensed under the MIT License. See the LICENSE file for details.