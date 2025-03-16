# OP25 Vehicle Scanner GUI

## Overview
This project provides a graphical user interface (GUI) for OP25, a software-defined radio (SDR) scanner designed to run on a Raspberry Pi. It integrates OP25 with a touchscreen interface, making it easier to scan and monitor talkgroups in a vehicle at a low cost.

## Features
- **Graphical Interface**: Provides an interactive UI for controlling OP25.
- **Talkgroup Management**: Supports whitelisting, blacklisting, and dynamic talkgroup selection.
- **IR Remote Support** (Under Development): Enables control via an IR remote.
- **Text-to-Speech (TTS) Alerts**: Uses `pyttsx3` for audio feedback on talkgroup changes.
- **Log Monitoring**: Captures OP25 logs for troubleshooting.
- **Scan Mode**: Dynamically updates and reloads OP25’s whitelist.
- **System Integration**: Currently, the system supports only one system at a time. Future updates will aim to integrate OP25's multi-system capabilities.

## Requirements
### Hardware
- Raspberry Pi 4 (Recommended) 
- RTL-SDR USB Dongle
- Touchscreen Display (Optional)

### Software
- **Operating System**: Ubuntu Server (recommended for better OP25 support)
- **Dependencies**:
  - OP25 (Installed in `/home/(user)/op25`)
  - `PySide6` for GUI
  - `pyttsx3` for text-to-speech
  - `RPi.GPIO` (for IR remote control)

### Additional Notes for Ubuntu Server Users
- Since Ubuntu Server does not come with a GUI, you will need to install one to use this project effectively.
- You should also install a VNC server if you want to work on development and UI features remotely.
  ```bash
  sudo apt install xfce4 xfce4-goodies tightvncserver
  ```

## Tested Hardware
- **Raspberry Pi 4 (2GB Memory) with Ubuntu Server**  
  [Buy on Amazon](https://www.amazon.com/dp/B09TTNPB4J?ref=ppx_yo2ov_dt_b_fed_asin_title)
- **DWEII 6 Sets Infrared IR Wireless Remote Control Module Kits DIY Kit HX1838 for Arduino Raspberry Pi**  
  [Buy on Amazon](https://www.amazon.com/dp/B09ZTZQFP7?ref=ppx_yo2ov_dt_b_fed_asin_title)
- **A1 FFCs - Sample Pack Flex Cable for Raspberry Pi Camera - Black 8, 15, 30, and 60 cm**  
  [Buy on Amazon](https://www.amazon.com/dp/B097P6CMV1?ref=ppx_yo2ov_dt_b_fed_asin_title)
- **FREENOVE 5 Inch Touchscreen Monitor for Raspberry Pi 5 4 B 3 B+ A+, 800x480 Pixel IPS Display, 5-Point Touch Capacitive Screen, Driver-Free MIPI DSI Port**  
  [Buy on Amazon](https://www.amazon.com/dp/B0B455LDKH?ref=ppx_yo2ov_dt_b_fed_asin_title)
- **RTL-SDR Blog V4 R828D RTL2832U 1PPM TCXO SMA Software Defined Radio (Dongle Only)**  
  [Buy on Amazon](https://www.amazon.com/dp/B0CD745394?ref_=ppx_hzsearch_conn_dt_b_fed_asin_title_2)

## Installation
### 1. Install OP25
Ensure OP25 is installed in `/home/(user)/op25`:
```bash
cd ~
git clone https://github.com/boatbod/op25.git
cd op25
./install.sh
```
See [op25-config.md](https://github.com/TheMrNaab/op25-headunit/blob/main/help/op25-config.md) for additional details on this step. Installing OP25 on Raspberry Pi OS presented challenges, so I opted to install Ubuntu Server and manually configure the required modules. Since this is not my base code, I cannot provide support for this step, but there are plenty of online resources available.


### 2. Install Required Python Packages
```bash
pip install PySide6 pyttsx3 RPi.GPIO
```

### 3. Clone and Set Up This Project
```bash
git clone https://github.com/TheMrNaab/op25-headunit
sudo mv op25-vehicle-scanner /opt/op25-project
```

### 4. Configure OP25
Place the following required files inside the OP25 installation directory:
- `_trunk.tsv`
- `_whitelist.tsv`
- `_tgroups.csv`
- `_blist.tsv`

These files must be located in:
```bash
/home/(user)/op25/op25/gr-op25_repeater/apps/
```

See [op25-config.md](https://github.com/TheMrNaab/op25-headunit/blob/main/help/op25-config.md) for additional information on this step.

### 5. Configure Your System
Edit `system.json` in this installation directory of this script. See  [system-config.md](https://github.com/TheMrNaab/op25-headunit/blob/main/help/system-config.md) for additional information on this step.

### 6. Configure Auto-Start
- Enable automatic login and configure `main.py` to start with the GUI.
- Manually edit `system.json` to configure your channels.

### 7. Run the Scanner UI
```bash
cd /opt/op25-project
python3 main.py
```

## File Structure
```
/opt/op25-project/
├── main.py             # GUI Application
├── logger.py           # Logging Utility
├── fileobject.py       # JSON Data Handling
├── tts.py              # Text-to-Speech Engine
├── ir.py               # IR Remote Handler (WIP)
├── control.py          # OP25 Process Controller
├── customWidgets.py    # Custom GUI Widgets
├── styles.css          # UI Styling (if applicable)
├── system.json         # Zone and Talkgroup Configuration
└── logs/               # Logs Directory
└── templates/          # Template files for OP25 installation
```

## Troubleshooting
### OP25 Not Connecting
- Ensure OP25 is properly installed and running.
- Try running OP25 manually:
  ```bash
  python3 /home/(user)/op25/op25/gr-op25_repeater/apps/rx.py -T /home/(user)/op25/op25/gr-op25_repeater/apps/_trunk.tsv
  ```

### IR Remote Not Working
- Ensure `RPi.GPIO` is installed.
- Check if the correct GPIO pin is used in `ir.py`.
See the [ir.md](https://github.com/TheMrNaab/op25-headunit/blob/main/help/ir.md) for additional information on this step.

## Future Plans
- Implement full IR remote control.
- Improve UI responsiveness.
- Add more customization options.

## License
This project is licensed under the MIT License.

## Credits
Developed by David Naab.

