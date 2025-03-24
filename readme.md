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
- AUX to USB dongle (Note: Pi5 does not include an AUX port)

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
- Raspberry Pi 4 with Ubuntu Server installed  
- Freenove 5" Touchscreen Monitor (800x480)  
- RTL-SDR Blog V4 R828D RTL2832U 1PPM TCXO SMA SDR  

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
pip install PySide6 watchdog Flask flask-cors
```

### 3. Clone This Project
```bash
git clone https://github.com/TheMrNaab/op25-headunit
sudo mv op25-vehicle-scanner /opt/op25-project
```
### 4. Configure OP25
Use the provided utilities in `/html/utilities/` the generate a `_trunk.tsv` 
Place the file in the folder:
```bash
/home/(user)/op25/op25/gr-op25_repeater/apps/
```
Copy the remaining default files into the same directory: 
- `_whitelist.tsv`   
- `_tgroups.csv`  
- `_blist.tsv`  


See [op25-config.md](https://github.com/TheMrNaab/op25-headunit/blob/main/help/op25-config.md) for details.

### 5. Create a system2.json file (Zones and Channels)
- Generate your OP25 Headunit configuration file using the utility in `/html/utilities`
- Place the file inside this script's `/opt/op25-project/system-2.json` installation directory 

### 6. CLI autologin setup with Openbox
- Open your `.bash_profile` configuration file:
```bash
nano ~/.bash_profile
```
Append to the `.bashprofile`:
```bash
[[ -z $DISPLAY && $XDG_VTNR -eq 1 ]] && startx
```
Open your `.xinitrc` configuration file:
```bash
nano ~/.xinitrc
```
Open your `.xinitrc` configuration file:
```bash
exec openbox-session
```

### 7. Configure OpenBox's Autostart File
Openbox uses this file to start apps automatically on session launch:
```bash
nano ~/.config/openbox/autostart
```
Paste this at the end of the file:
```bash
python3 /opt/op25-project/api.py &            # Launch Flask API server in background
sleep 3                                       # Delay briefly to ensure Flask starts before browser launches
firefox-esr --kiosk http://localhost:8000/ &  # Launch Firefox in kiosk mode

```

### 8. Set Up Auto-Start
- Enable auto-login on your Linux system

## Future Plans
- Expand customization options  
- Implement `config.ini` fully
- Implement voice to text that scans for alert keywords
- Implement multi-system channels

## License
This project is licensed under the MIT License.

## Credits
Developed by David Naab.
