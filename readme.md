# OP25 Vehicle Scanner GUI

<p><img src="help/screenshot.png" width="300"/> <img src="help/screenshot-animated.gif" width="300"/></p>

## Overview
This project provides a graphical user interface (GUI) for OP25, a software-defined radio (SDR) scanner running on a Raspberry Pi. It integrates OP25 with a touchscreen interface to simplify scanning and monitoring talkgroups in a vehicle at low cost.

## User Interface
The project serves the `/html` folder for the UI and uses `api.py` to handle interaction between the webpage and OP25. This setup uses fewer resources and allows layout flexibility based on screen size.

## Features
- **Graphical Interface**: HTML-based UI for controlling OP25
- **Talkgroup Management**: Supports whitelist, blacklist, and dynamic selection
- **Scan Mode**: Reloads OP25’s whitelist dynamically
- **System Integration**: Currently supports one system; future updates will address multi-system support

## Requirements

### Hardware
- Raspberry Pi 5 (recommended)  
- RTL-SDR USB dongle  
- Touchscreen display (recommended)  
- AUX to USB dongle (Note: Pi5 does not include an AUX port)

### Software
- **Operating System**: Ubuntu Server (recommended for OP25 compatibility)  
- **Dependencies**:  
  - `OP25` (installed at `/home/(user)/op25`)    
  - `pyttsx3` for text-to-speech (upcoming feature)  
  - `firefox-esr` for interface display  

### Notes for Ubuntu Server Users
- Ubuntu Server lacks a graphical interface by default. To install one:

```bash
sudo apt install openbox firefox-esr xinit x11-xserver-utils
```

## Tested Hardware
- Raspberry Pi 4 with Ubuntu Server installed  
- Freenove 5" Touchscreen Monitor (800x480)  
- RTL-SDR Blog V4 R828D RTL2832U 1PPM TCXO SMA SDR  

## Installation
See the installation wizard in [/html/utilities/install-wizard.html](https://github.com/TheMrNaab/op25-headunit/blob/6022ac7fdb9acd2600f27025fefb03b12a39c06e/html/utilities/install-wizard.html)
