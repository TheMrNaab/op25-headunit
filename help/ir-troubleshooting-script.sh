# Unload the IR receiver kernel module (resets the IR hardware)
sudo rmmod gpio-ir-recv

# Reload the IR receiver kernel module (re-initializes IR signal handling)
sudo modprobe gpio-ir-recv

# List available IR receiver devices (should show rc0 or rc1 if detected)
ls /sys/class/rc/

# Test if the IR receiver is capturing signals (press remote buttons)
sudo ir-keytable -t

# Clear the current IR keytable configuration (resets mapping)
sudo ir-keytable -c

# Enable the NEC protocol (most common IR remote standard)
sudo ir-keytable -p nec

# Test again to confirm that IR signals are now being detected
sudo ir-keytable -t