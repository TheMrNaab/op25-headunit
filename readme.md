# OP25 Vehicle Scanner GUI

![Screen Shot](help/screenshot.png)
![Screen Shot](help/screenshot-animated.gif)

## Overview
This project provides a graphical user interface (GUI) for OP25, a software-defined radio (SDR) scanner running on a Raspberry Pi. It integrates OP25 with a touchscreen interface to simplify scanning and monitoring talkgroups in a vehicle at low cost.

## User Interface
The project serves the `/html` folder for the UI and uses `api.py` to handle interaction between the webpage and OP25. This setup uses fewer resources and allows layout flexibility based on screen size.

After installing `firefox-esr`, add the following command to your system startup:

```bash
firefox-esr --kiosk http://localhost:8000/
```

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

### Software
- **Operating System**: Ubuntu Server (recommended for OP25 compatibility)  
- **Dependencies**:  
  - `OP25` (installed at `/home/(user)/op25`)  
  - `PySide6` for GUI  
  - `pyttsx3` for text-to-speech (upcoming feature)  
  - `firefox-esr` for interface display  

### Notes for Ubuntu Server Users
Ubuntu Server lacks a graphical interface by default. To install one:

```bash
sudo apt install xfce4 xfce4-goodies firefox-esr
```

## Tested Hardware
- Raspberry Pi 5 with Ubuntu Server installed  
- Freenove 5" Touchscreen Monitor (800x480)  
- RTL-SDR Blog V4 R828D RTL2832U 1PPM TCXO SMA SDR  
- AUX to USB Adapter

## Installation

### 1. Install OP25
```bash
cd ~
git clone https://github.com/boatbod/op25.git
cd op25
./install.sh
```

### 2. Install Required Python Packages
```bash
pip install PySide6 pyttsx3
```

### 3. Clone This Project
```bash
git clone https://github.com/TheMrNaab/op25-headunit
sudo mv op25-vehicle-scanner /opt/op25-project
```

### 4. Configure OP25 Files
Place the following files in:

```bash
/home/(user)/op25/op25/gr-op25_repeater/apps/
```

- `_trunk.tsv`  
- `_whitelist.tsv`  
- `_tgroups.csv`  
- `_blist.tsv`  

Utilities to generate these files are available in the `/html` folder.

See [op25-config.md](https://github.com/TheMrNaab/op25-headunit/blob/main/help/op25-config.md) for details.

### 5. Create system.json
Place your configuration file in:

```bash
/opt/op25-project/system-2.json
```

### 6. Set Up Auto-Start
- Enable auto-login on your Linux system  
- Create a shell script to:
  - Run `start.py`  
  - Launch the UI:  
    ```bash
    firefox-esr --kiosk http://localhost:8000/
    ```

## Future Plans
- Add full IR remote support  
- Improve UI responsiveness  
- Expand customization options  

## License
This project is licensed under the MIT License.

## Credits
Developed by David Naab.
