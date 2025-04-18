import subprocess
from flask import jsonify, send_file
import subprocess
import re
import io
import qrcode
import psutil

class soundSys:
    @staticmethod
    def get_volume_percent(card=3):
        command = ["amixer", "-c", f"{card}", "get", "PCM"]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            match = re.search(r"\[(\d+)%\]", result.stdout)
            if match:
                return match.group(1)
            else:
                return "unknown", 500
        except subprocess.CalledProcessError as e:
            return f"error: {e.stderr.strip()}", 500

    def set_volume(percent, card=3):
        if isinstance(percent, int):
            percent = f"{percent}%"
        elif isinstance(percent, str) and not percent.endswith('%'):
            percent += '%'

        command = ["amixer", "-c", f"{card}", "set", "PCM", percent]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return "ok"
        except subprocess.CalledProcessError as e:
            return f"error: {e.stderr.strip()}", 500

    @staticmethod
    def parse_volume(result):
        lines = result.stdout.strip().splitlines()
        parsed = {}

        if lines:
            match = re.match(r"Simple mixer control '(\w+)',(\d+)", lines[0])
            if match:
                parsed["output"] = lines[0].strip()
                parsed["pcm"] = int(match.group(2))

        for line in lines:
            if "Capabilities:" in line:
                parsed["capabilities"] = line.split(":", 1)[1].strip().split()
            elif "Playback channels:" in line:
                parsed["playback_channels"] = line.split(":", 1)[1].strip()
            elif "Limits:" in line:
                parts = re.findall(r"-?\d+", line)
                if len(parts) == 2:
                    parsed["limits"] = {
                        "playback_min": int(parts[0]),
                        "playback_max": int(parts[1])
                    }
            elif "Mono:" in line and "Playback" in line:
                values = re.findall(r"Playback (\d+) \[(\d+)%\] \[([-\d.]+)dB\] \[(on|off)\]", line)
                if values:
                    raw, percent, db, status = values[0]
                    parsed["playback"] = {
                        "level_raw": int(raw),
                        "level_percent": int(percent),
                        "level_db": float(db),
                        "status": status
                    }
                    parsed["volume_percent"] = int(percent)
                break

        return jsonify(parsed)


    def parse_hw_devices():
        try:
            # Step 1: Map card names to indexes from aplay -l
            result_l = subprocess.run(["aplay", "-l"], capture_output=True, text=True, check=True)
            card_map = {}  # { "vc4hdmi1": "2", "Headphones": "0" }

            for line in result_l.stdout.splitlines():
                match = re.search(r'card (\d+): (\S+) \[([^\]]+)\]', line)
                if match:
                    card_index = match.group(1)
                    card_id = match.group(2)  # machine-readable
                    card_map[card_id] = card_index

            # Step 2: Filter hw/plughw devices from aplay -L
            result_L = subprocess.run(["aplay", "-L"], capture_output=True, text=True, check=True)
            device_lines = result_L.stdout.splitlines()

            output = [{"label": "Default Device", "value": "default"}]

            for line in device_lines:
                line = line.strip()
                match = re.match(r'^(hw|plughw):CARD=(\w+),DEV=(\d+)', line)
                if match:
                    prefix, card_name, dev_index = match.groups()
                    if card_name in card_map:
                        card_index = card_map[card_name]
                        short_val = f"{prefix}:{card_index},{dev_index}"
                        label = f"{card_name} ({short_val})"
                        output.append({"label": label, "value": short_val})

            return output

        except Exception as e:
            print("Error parsing ALSA devices:", e)
            return [{"label": "default", "value": "default"}]

    @staticmethod
    def list_alsa_devices():
        try:
            result = subprocess.run(["aplay", "-L"], capture_output=True, text=True, check=True)
            lines = result.stdout.splitlines()
            devices = [line.strip() for line in lines if line and not line.startswith(" ")]
            return devices
        except Exception as e:
            print("Error listing ALSA devices:", e)
            return []
    
class sound:
    @staticmethod
    def percent_to_raw(min_val, max_val, percent):
        """
        Convert percent (0–100) to raw ALSA value
        """
        if percent < 0 or percent > 100:
            raise ValueError("Percent must be between 0 and 100")
        range_span = max_val - min_val
        raw = round(min_val + (range_span * (percent / 100)))
        return raw

    @staticmethod
    def raw_to_percent(min_val, max_val, raw):
        """
        Convert raw ALSA value to percent
        """
        if raw < min_val or raw > max_val:
            raise ValueError("Raw value out of range")
        range_span = max_val - min_val
        percent = ((raw - min_val) / range_span) * 100
        return round(percent, 2)

    @staticmethod
    def raw_to_db(raw):
        """
        Convert ALSA raw value to dB (rough estimation)
        ALSA uses 100 steps = 1 dB
        So: -10239 = -102.39 dB, etc.
        """
        return round(raw / 100, 2)
    @staticmethod
    def db_to_raw(db):
        """
        Convert dB to raw ALSA value (if using 100 steps per dB)
        """
        return round(db * 100)
