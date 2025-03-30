import subprocess
import qrcode
import io
import psutil
import re
class LinuxUtilities:

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
    def get_network_status():
        status = {
            "connection_type": "Disconnected",
            "wifi_name": "N/A",
            "status": "Disconnected",
            "mem_available": "N/A",
            "cpu_temp": "N/A",
            "audio_output": "N/A"
        }
        try:
            for iface, stats in psutil.net_if_stats().items():
                if stats.isup and iface != "lo":
                    status["connection_type"] = "Wired" if "eth" in iface else "Wifi"
                    status["wifi_name"] = iface
                    status["status"] = "Connected"
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