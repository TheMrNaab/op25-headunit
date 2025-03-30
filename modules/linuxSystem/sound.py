import subprocess
from flask import jsonify, send_file
import subprocess
import re
import io
import qrcode
import psutil

class soundSys:
    @staticmethod
    def get_volume_percent():
        command = ["amixer", "get", "PCM"]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            match = re.search(r"\[(\d+)%\]", result.stdout)
            if match:
                return match.group(1)
            else:
                return "unknown", 500
        except subprocess.CalledProcessError as e:
            return f"error: {e.stderr.strip()}", 500

    @staticmethod
    def set_volume(level):
        command = ["amixer", "set", "PCM", f"{level}%"]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return soundSys.parse_volume(result)
        except subprocess.CalledProcessError as e:
            return jsonify({"error": e.stderr.strip()}), 500

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
