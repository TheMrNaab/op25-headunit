
# OP25 Head Unit Setup Wizard

This project adds a touchscreen-friendly graphical interface to OP25, a software-defined radio (SDR) scanner built for the Raspberry Pi. Designed for in-vehicle use, it simplifies talkgroup monitoring with a low-cost, low-power setup. The system serves the user interface from the `/html` directory and uses `api.py` to manage communication between the interface and OP25. It is optimized for minimal resource use and adapts to various screen sizes.

---

## Step 1: Install OP25

1. **Download Raspberry Pi Imager**
   [Download](https://www.raspberrypi.com/software/) Raspberry Pi Imager and use it to flash Ubuntu Server onto a new MicroSD card. During setup, configure your WiFi settings as needed.
   
3. **Compile and Install BoatBod's OP25** 
   This command clones the OP25 project and runs its install script:
   *You may need to recomplile numerous times to solve dependancy issues* 
   ```bash
   cd ~
   git clone https://github.com/boatbod/op25.git
   cd op25
   ./install.sh
   ```

4. **Replace Modified OP25 Files**  
   Changes had to be made to `terminal.py` and `rx.py` for this to work.
   ```bash
   cp /opt/op25-project/templates/terminal.py /home/$(whoami)/op25/op25/gr-op25_repeater/apps/
   cp /opt/op25-project/templates/rx.py /home/$(whoami)/op25/op25/gr-op25_repeater/apps/

---

## Step 2: Install Required Python Packages

Install the Python libraries used by the user interface and backend API:

```bash
pip install PySide6 watchdog Flask flask-cors
```

---

## Step 3: Clone the Headunit Project

This project contains the HTML interface, API, and configuration utilities:

```bash
git clone https://github.com/TheMrNaab/op25-headunit
sudo mv op25-vehicle-scanner /opt/op25-project
```

---

## Step 4: Configure the Trunking System

Use the `/html/utilities/trunk_system_editor.html` utility to generate your trunking system definition file.

- Currently, only one system is supported, but you can define additional ones for future updates.
- More details about this file can be found in the [OP25 config guide](https://github.com/TheMrNaab/op25-headunit/blob/main/help/op25-config.md).

Place the generated file in:

```bash
cd /home/$(whoami)/op25/op25/gr-op25_repeater/apps/
```

---

## Step 5: Configure Talkgroup Files

1. Place the remaining configuration files in the same directory as the trunking file. Templates are available in the `/templates/` directory.  
2. Reference the [OP25 config guide](https://github.com/TheMrNaab/op25-headunit/blob/main/help/op25-config.md).

Files:

- `_whitelist.tsv` *(always overwritten, do not modify)*
- `_tgroups.csv` *(optional, can contain names of each talkgroup)*
- `_blist.tsv` *(always overwritten, do not modify)*

---

## Step 6: Create `system2.json`

1. This file defines the zones and channels shown in the web interface. Generate it using the `/html/utilities/system-editor.html` utility.

2. Place the file here:

```bash
cd /opt/op25-project/system-2.json
```

---

## Step 7: Choose Startup Mode

Would you like OP25 to start manually or automatically when your Pi boots?

### Manual Start Instructions

Run these commands manually whenever you want to launch the system:

```bash
openbox-session
python3 /opt/op25-project/api.py &
firefox-esr --kiosk http://localhost:8000/
```

---

### Auto Start Configuration

Configure your Pi to start the API and browser automatically on boot:

1. **Edit `~/.bash_profile`:**
   ```bash
   [[ -z $DISPLAY && $XDG_VTNR -eq 1 ]] && startx
   ```

2. **Edit `~/.xinitrc`:**
   ```bash
   exec openbox-session
   ```

3. **Configure OpenBox autostart:**
   ```bash
   python3 /opt/op25-project/api.py &
   sleep 3
   firefox-esr --kiosk http://localhost:8000/ &
   ```
   

