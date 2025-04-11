import subprocess
import qrcode
import io
import psutil
import re
import json
from flask import jsonify
import socket
import time
import os

class LinuxUtilities:

    @staticmethod
    def get_active_audio_device_old():
        try:
            # Run the pw-dump with jq filtering command
            cmd = 'pw-dump | jq -r \'.[] | select(.type == "PipeWire:Interface:Node") | select(.info.props."media.class" == "Audio/Sink") | .info.props\''
            result = subprocess.check_output(cmd, shell=True, text=True)
            
            # Parse the result to a Python dictionary
            props = json.loads(result)
            return props
        except subprocess.CalledProcessError as e:
            return {"error": f"Command failed: {e}"}
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON output"}

    @staticmethod
    def get_audio_sink_properties():
        try:
            cmd = (
                'pw-dump | jq -c \'.[] | '
                'select(.type == "PipeWire:Interface:Node") | '
                'select(.info.props["media.class"] == "Audio/Sink") | '
                '.info.props\''
            )
            result = subprocess.check_output(cmd, shell=True, text=True)
            lines = result.strip().splitlines()
            if not lines:
                return {"error": "No audio sink found"}

            return json.loads(lines[0])  # Return full props dictionary

        except subprocess.CalledProcessError as e:
            return {"error": f"Command failed: {e}"}
        except json.JSONDecodeError as e:
            return {"error": f"JSON parse error: {e}"}

    @staticmethod
    def get_volume_percent():
        try:
            result = subprocess.run(["amixer", "get", "PCM"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            match = re.search(r"\[(\d+)%\]", result.stdout)
            return match.group(1) if match else "unknown"
        except subprocess.CalledProcessError as e:
            return f"error: {e.stderr.strip()}"

    @staticmethod
    def generate_qrcode_image(content):
        qr_img = qrcode.make(content)
        img_io = io.BytesIO()
        qr_img.save(img_io, 'PNG')
        img_io.seek(0)
        return img_io

    @staticmethod
    def set_display_timeout(display_id, timeout_minutes):
        seconds = timeout_minutes * 60
        subprocess.run(["xset", "-display", f":{display_id}", "dpms", str(seconds), str(seconds), str(seconds)], check=True)

    @staticmethod
    def get_display_timeout(display_id):
        output = subprocess.check_output(["xset", "-display", f":{display_id}", "q"]).decode()
        for line in output.splitlines():
            if "Standby:" in line:
                parts = line.strip().split()
                return int(parts[1]) // 60
        raise ValueError("Could not parse display timeout")

    @staticmethod
    def set_device_sleep_timeout(timeout_minutes):
        seconds = timeout_minutes * 60
        subprocess.run(["loginctl", "set-idle-delay", str(seconds)], check=True)

    @staticmethod
    def get_device_sleep_timeout():
        output = subprocess.check_output([
            "loginctl", "show-session", "self",
            "-p", "IdleHint", "-p", "IdleSinceHint",
            "-p", "IdleSinceHintMonotonic", "-p", "IdleDelay"
        ]).decode()
        for line in output.splitlines():
            if line.startswith("IdleDelay="):
                return int(line.split("=")[1]) // 60
        raise ValueError("Could not parse device sleep timeout")


    @staticmethod
    def list_displays():
        displays = []
        output = subprocess.check_output(["who"]).decode()
        display_ids = re.findall(r'\((:\d+)\)', output)
        seen = set(display_ids)
        for disp in seen:
            displays.append({"id": disp, "name": f"Display {disp}", "in_use": True})
        for i in range(0, 3):
            disp = f":{i}"
            if disp not in seen:
                displays.append({"id": disp, "name": f"Display {disp}", "in_use": False})
        return displays

    @staticmethod
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Dummy external IP, no traffic sent
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "N/A"

    @staticmethod
    def get_network_status():
        status = {
            "connection_type": "Disconnected",
            "wifi_name": "N/A",
            "status": "Disconnected",
            "mem_available": "N/A",
            "cpu_temp": "N/A",
            "audio_output": "N/A",
            "host_name": "N/A",
            "host_ip": "N/A",
            "host_port": "N/A"
        }
        try:
            for iface, stats in psutil.net_if_stats().items():
                if stats.isup and iface != "lo":
                    status["connection_type"] = "Wired" if "eth" in iface else "Wifi"
                    status["wifi_name"] = iface
                    status["status"] = "Connected"
                    status["host_name"] = socket.gethostname()
                    status["host_ip"] = LinuxUtilities.get_local_ip()
                    status["host_port"] = "8000"
                    break
        except: pass
        try:
            mem = psutil.virtual_memory()
            status["mem_available"] = f"{mem.available // (1024 * 1024)} MB"
        except: pass
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                status["cpu_temp"] = f"{int(f.read()) / 1000:.1f} °C"
        except: pass
        try:
            status["audio_output"] = subprocess.check_output(["pactl", "get-default-sink"]).decode().strip()
        except: pass
        return status    
    
    
    @staticmethod
    def list_bluetooth_speakers():
        try:
            print("DBUS:", os.environ.get("DBUS_SESSION_BUS_ADDRESS"))
            proc = subprocess.Popen(
                ['bluetoothctl'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1
            )

            # Set up agent and scan
            proc.stdin.write("agent on\n")
            proc.stdin.write("default-agent\n")
            proc.stdin.write("scan on\n")
            proc.stdin.flush()

            found_lines = []

            start_time = time.time()
            timeout = 10 # seconds

            # Read stdout in real-time
            while time.time() - start_time < timeout:
                line = proc.stdout.readline()
                if not line:
                    break
                if "Device" in line:
                    found_lines.append(line.strip())

            # Stop scan and get final device list
            proc.stdin.write("scan off\n")
            proc.stdin.write("devices\n")
            proc.stdin.flush()
            time.sleep(1)  # allow output to flush

            # Read remaining lines after devices command
            proc.stdin.close()
            additional_output = proc.stdout.read()
            proc.terminate()

            all_lines = found_lines + additional_output.strip().splitlines()

            # Parse devices
            devices = []
            for line in all_lines:
                match = re.match(r"Device ([0-9A-F:]+) (.+)", line)
                if match:
                    mac, name = match.groups()
                    if name.replace("-", ":") == mac:
                        name = "Unknown Device"
                    devices.append({"address": mac, "name": name})  # no filter
            return devices

        except Exception as e:
            print(f"Error listing bluetooth devices: {e}")
            return []
        
    @staticmethod
    def connect_and_route_bluetooth_audio(mac_address):
        def run_bluetoothctl_commands(commands):
            try:
                proc = subprocess.Popen(
                    ['bluetoothctl'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True
                )
                for cmd in commands:
                    proc.stdin.write(cmd + "\n")
                proc.stdin.flush()
                output, _ = proc.communicate(timeout=15)
                return output.lower()
            except Exception as e:
                return f"Error: {e}"

        # Step 1: Trust, pair, and connect
        print(f"[INFO] Connecting to {mac_address}...")
        output = run_bluetoothctl_commands([
            f"trust {mac_address}",
            f"pair {mac_address}",
            f"connect {mac_address}",
            "exit"
        ])

        if "failed" in output or "not available" in output:
            return {
                "success": False,
                "message": "Bluetooth pairing or connection failed.",
                "output": output
            }

        # Step 2: Wait briefly for Pulse to register the device
        time.sleep(3)

        # Step 3: Set audio sink to Bluetooth speaker
        try:
            sinks = subprocess.check_output(['pactl', 'list', 'short', 'sinks'], text=True)
            normalized_mac = mac_address.replace(":", "_").lower()

            for line in sinks.strip().splitlines():
                if normalized_mac in line.lower():
                    sink_name = line.split()[1]
                    subprocess.run(['pactl', 'set-default-sink', sink_name], check=True)
                    return {
                        "success": True,
                        "message": f"Connected and routed audio to {sink_name}",
                        "sink": sink_name,
                        "mac": mac_address
                    }

            return {
                "success": False,
                "message": "Bluetooth device connected but audio sink was not found.",
                "sinks_available": sinks
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "message": "Error setting default audio sink.",
                "error": str(e)
            }