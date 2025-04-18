# OP25 Vehicle Scanner GUI

<p><img src="help/screenshot-updated.png" width="300"/> <img src="help/screenshot-animated.gif" width="300"/></p>

## Overview
This project adds a touchscreen-friendly graphical interface to OP25, a software-defined radio (SDR) scanner for the Raspberry Pi. Designed for public safety personnel and radio enthusiasts, it offers a low-cost alternative to expensive commercial scanners like the Bearcat. The interface simplifies talkgroup scanning and monitoring in a vehicle without the high price tag.

## User Interface
The project serves the `/html` folder for the UI and uses `api.py` to handle interaction between the webpage and OP25. This setup uses fewer resources and allows layout flexibility based on screen size.

## Features
- **Graphical Interface**: HTML-based UI for controlling OP25
- **Talkgroup Management**: Supports whitelist, blacklist, and dynamic selection
- **Scan Mode**: Reloads OP25’s whitelist dynamically
- **System Integration**: Currently supports one system; future updates will address multi-system support
- **Active Voice Calls**: View the active talkgroup name or number (if not defined).
- **Volume Adjustment** Allows you to control the output volume on the home screen. 
- **Direct Programming**: Web-based utilities now handles software configuration directly, eliminating the need to manually copy configuration files. When the software is loaded, press the Info button. This will display the device's configuration panel that you can navigate to.

### Features Coming Soon
- **Advanced Keypad Entry**: Enter a known TAC or OPS channel directly using the corresponding button.
- **Multiple P25 System Support**: A future release will allow use of channels from multiple P25 systems simultaneously.
- **Default Configuration at Launch**: Audio defaults to your system’s primary output (AUX on a Pi 4; HDMI on a Pi 5). An option to select a different audio device will be added later.
- **Auto Screen Off**: The display powers off after 5 minutes of inactivity. An option to change this is in the works.
- **OP25 Parameter Adjustments**: Values set in config.ini will be passed to the software. Currently, parameters are hardcoded in the Python script.

## Requirements

### Hardware
- Raspberry Pi 4 
- RTL-SDR USB dongle 
- Touchscreen display (or any monitor with a mouse)
- **MicroSD Card**: Use a new card to avoid data loss. Install Ubuntu Server on its own MicroSD card. This script is in beta and may not be fully stable.

### Pi 5 Compatibility
- The Raspberry Pi 5 ran more reliably with increased memory. However, OP25 had trouble outputting audio through an AUX-to-USB adapter. A future update will allow selection of the default playback device. The OP25 back-end is still temperamental, and since it is not my script, solutions to common issues are limited and poorly documented online.

## Installation
Follow the installation wizard at [/html/utilities/wizard.md](https://github.com/TheMrNaab/op25-headunit/blob/main/html/utilities/wizard.md). 

**Be sure to follow all configuration steps including the replacement of terminal.py in the OP25 installation.**

### Software
- **Operating System**: Ubuntu Server (recommended for OP25 compatibility).
- **PI OS** The OP25 struggles with Pi OS and is not reccomdended.
- **Tested On** ### Raspberry Pi 4 with Ubuntu Server installed, Freenove 5" Touchscreen Monitor (800x480) and RTL-SDR Blog V4 RTL2832U SDR
- **Dependencies**:  
  - `OP25` (installed at `/home/(user)/op25`)    
  - `pyttsx3` for text-to-speech (upcoming feature)  
  - `firefox-esr` for interface display
  - `flash` for serving API and webpages
  - `openbox` for Firefox's GUI

### Notes for Ubuntu Server Users
- Ubuntu Server lacks a graphical interface by default and you must a GUI app to run this app.
- This is covered in the installation wizard.




