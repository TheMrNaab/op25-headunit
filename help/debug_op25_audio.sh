#!/bin/bash
set -e

LOGFILE="./op25_audio_debug.txt"
echo "===== OP25 Audio Troubleshoot Report =====" > "$LOGFILE"
date >> "$LOGFILE"
echo >> "$LOGFILE"

echo "### System info" >> "$LOGFILE"
uname -a >> "$LOGFILE"
echo >> "$LOGFILE"

echo "### List ALSA playback devices" >> "$LOGFILE"
aplay -l >> "$LOGFILE" 2>&1
echo >> "$LOGFILE"

echo "### ALSA mixer settings (card 0)" >> "$LOGFILE"
amixer -c 0 scontents >> "$LOGFILE" 2>&1
echo >> "$LOGFILE"

echo "### PulseAudio sinks" >> "$LOGFILE"
pactl list short sinks >> "$LOGFILE" 2>&1 || echo "(PulseAudio not running)" >> "$LOGFILE"
echo >> "$LOGFILE"

echo "### Processes using /dev/snd" >> "$LOGFILE"
sudo lsof /dev/snd/* >> "$LOGFILE" 2>&1
echo >> "$LOGFILE"

echo "### OP25 rx.py process and UDP listeners" >> "$LOGFILE"
ps aux | grep rx.py | grep -v grep >> "$LOGFILE"
netstat -ulnp | grep 23456 >> "$LOGFILE" 2>&1
echo >> "$LOGFILE"

echo "### Capture 5 UDP packets from OP25 (port 23456)" >> "$LOGFILE"
sudo timeout 5 tcpdump -n -i lo udp port 23456 -c 5 >> "$LOGFILE" 2>&1 || echo "No UDP packets seen" >> "$LOGFILE"
echo >> "$LOGFILE"

echo "### ALSA playback test (Front Center WAV)" >> "$LOGFILE"
aplay -D plughw:0,0 /usr/share/sounds/alsa/Front_Center.wav >> "$LOGFILE" 2>&1 || echo "APLAY FAILED" >> "$LOGFILE"
echo >> "$LOGFILE"

echo "### OP25 stderr tail (last 20 lines)" >> "$LOGFILE"
tail -n20 stderr.2 >> "$LOGFILE" 2>&1 || echo "stderr.2 not found" >> "$LOGFILE"
echo >> "$LOGFILE"

echo "Report written to $LOGFILE"