After installing the imports and device drivers for the IR receiver, we must configure our script to run without the need to sudo.

1. Add your user to the gpio group (Run this once):
`sudo usermod -aG gpio $USER1

2. Enable GPIO access via udev rules (Run this once):
`echo 'SUBSYSTEM=="gpio*", KERNEL=="gpio*", MODE="0660", GROUP="gpio"' | sudo tee /etc/udev/rules.d/99-gpio.rules`

3. Reboot your Raspberry Pi:
`sudo reboot`