# **Installing IR Drivers on Ubuntu Server for Raspberry Pi**

This guide provides step-by-step instructions for installing IR drivers on Ubuntu Server for Raspberry Pi, ensuring proper configuration and troubleshooting methods.

## **Installation Steps**

### **1. Update the System**
Before installing any drivers, update your system:
```bash
sudo apt update && sudo apt upgrade -y
```

### **2. Install Required Packages**
Install the necessary LIRC and GPIO tools:
```bash
sudo apt install lirc ir-keytable gpiod -y
```

### **3. Add User to the GPIO Group**
To allow access to GPIO without `sudo`, add your user to the `gpio` group:
```bash
sudo usermod -aG gpio $USER
```
Log out and back in for changes to take effect.

### **4. Enable IR Support in Boot Configuration**
Edit the boot configuration file:
```bash
sudo nano /boot/firmware/config.txt
```
Add the following line at the end:
```
dtoverlay=gpio-ir,gpio_pin=18
```
(Replace `18` with the GPIO pin where the IR receiver is connected.)

Save and exit (`CTRL+X`, then `Y`, then `ENTER`).

Reboot the system:
```bash
sudo reboot
```

### **5. Load IR Kernel Modules**
After reboot, manually load the IR modules:
```bash
sudo modprobe gpio-ir-recv
sudo modprobe gpio-ir
```
Verify if `/dev/lirc0` exists:
```bash
ls /dev/lirc*
```
If found, proceed to the next step.

### **6. Enable and Start LIRC Service**
Ensure the LIRC service is running:
```bash
sudo systemctl enable lircd
sudo systemctl start lircd
```
Check the service status:
```bash
systemctl status lircd
```

### **7. Test IR Input**
Use the following command to check if IR signals are being received:
```bash
sudo ir-keytable -t
```
Press buttons on the remote and look for output.

---

## **Troubleshooting**

### **1. IR Signals Not Detected**
#### **Check Wiring**
Ensure the IR receiver is properly connected:
| **IR Receiver Pin** | **Raspberry Pi Pin** |
|--------------------|------------------|
| **VCC** (middle)  | **5V (Pin 2 or 4)** |
| **GND** (left)    | **GND (Pin 6, 9, 14, etc.)** |
| **OUT** (right)   | **GPIO 18 (Pin 12)** (or configured GPIO) |

#### **Verify GPIO Input Activity**
Use `gpiomon` to check if signals are detected:
```bash
sudo gpiomon --num-events=10 --rising-edge gpiochip0 18
```
If no output appears when pressing remote buttons, recheck wiring.

### **2. `/dev/lirc0` Not Found**
Try manually loading the IR kernel modules:
```bash
sudo modprobe gpio-ir-recv
sudo modprobe gpio-ir
```
Then check for `/dev/lirc0` again:
```bash
ls /dev/lirc*
```
If still missing, ensure the correct overlay is in `/boot/firmware/config.txt` and reboot.

### **3. LIRC Not Detecting IR Events**
Check available input devices:
```bash
ls /dev/input/
```
Test each event:
```bash
sudo evtest /dev/input/eventX
```
(Replace `eventX` with detected event numbers.)

If `evtest` detects signals, update LIRC to use the correct event:
```bash
sudo nano /etc/lirc/lirc_options.conf
```
Change:
```
driver = devinput
device = /dev/input/eventX
```
Restart LIRC:
```bash
sudo systemctl restart lircd
```

### **4. Permission Errors**
Ensure your user has access to GPIO:
```bash
sudo usermod -aG gpio $USER
```
Then reboot:
```bash
sudo reboot
```

---

## **Conclusion**
Following this guide will set up IR drivers on Ubuntu Server for Raspberry Pi, enabling LIRC to process IR remote signals. If issues persist, verify wiring, check kernel modules, and ensure the correct input event is used in LIRC.

For further assistance, refer to the [LIRC documentation](http://www.lirc.org/) or check Raspberry Pi forums.

