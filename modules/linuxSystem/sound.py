import subprocess
from flask import jsonify, send_file
import subprocess
import re
import io
import qrcode
import psutil

class SoundSys:
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
            return SoundSys.parse_volume(result)
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
    
