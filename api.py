import subprocess
import os
import signal
import logging
import re
from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from control import OP25Controller
from ch_manager import ChannelManager, MyConfig
from logMonitor import LogFileHandler, LogFileWatcher, logMonitorOP25
import time
import threading
from queue import Queue
import json
import logging
logging.getLogger('watchdog').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

class errrorHandler:
    def __init__(self, api):
        self.config = MyConfig()
        self.API = api
        LOG_FILE = self.config.get_path("paths", "app_log")

        logging.basicConfig(
            filename=LOG_FILE,
            filemode="a",
            level=logging.ERROR,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s"
        )

        # Silence noisy libraries
        for lib in ("watchdog", "urllib3", "urllib3.connectionpool", "requests", "root"):
            logging.getLogger(lib).setLevel(logging.WARNING)
            
class API:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
        self.free_port(8000)
        self.free_port(5001)
        self.kill_named_scripts(["rx.py", "terminal.py"])
        logging.basicConfig(level=logging.DEBUG)

        self.errHandler = errrorHandler(self)
        # External controllers
        self.op25 = OP25Controller()
        self.file_obj = ChannelManager('/opt/op25-project/systems-2.json')

        end_point = f"{self.file_obj.config.get('hosts','api_host')}/logging/update"
        monitor = logMonitorOP25(self, file=self.file_obj.config.get("paths","stderr_file"), endpoint = end_point)
        watcher = LogFileWatcher(monitor)
        watcher.start_in_thread()
        # Register routes
        self.register_routes()


    def register_routes(self):

        # 1 === PROGRESS & SYNC LOCK ====
        # + TODO: MODIFY RX.PY TO STREAM STATUS UPDATE IN {}
        progress = 0
        lock = threading.Lock()

        # 2 === PROGRESS ENDPOINT ====      
        @self.app.route('/update/<int:percent>', methods=['POST'])
        def update_progress(percent): # In practice, your talk group update code would update the progress value.
            global progress
            data = request.get_json()
            with lock:
                progress = data.get("progress", progress)
            return jsonify(success=True)
        
        # 3 === SSE EVENT GENERATOR (UPDATE EVERY SECOND) ====   
        def event_stream():
            global progress
            while True:
                with lock:
                    current = progress
                yield f"data: {current}\n\n"
                time.sleep(1)

        # 4 === SSE ENDPOINT ===
        @self.app.route('/progress', methods=['POST'])
        def progress_stream():
            return Response(event_stream(), mimetype="text/event-stream")

        @self.app.route('/volume/simple', methods=['GET'])
        def get_volume():
            command = ["amixer", "get", "PCM"]
            try:
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
                match = re.search(r"\[(\d+)%\]", result.stdout)
                if match:
                    return match.group(1)  # plain text, just "97"
                else:
                    return "unknown", 500
            except subprocess.CalledProcessError as e:
                return f"error: {e.stderr.strip()}", 500
        
        # + SET VOLUME
        @self.app.route('/volume/<int:level>', methods=['POST'])
        def set_volume(level):
            # EXAMPLE OUTPUT: { "output": "Simple mixer control 'PCM',0\nCapabilities: pvolume pvolume-joined pswitch pswitch-joined\nPlayback channels: Mono\nLimits: Playback -10239 - 400\nMono: Playback -9175 [10%] [-91.75dB] [on]" }
            command = ["amixer", "set", "PCM", f"{level}%"]
            try:
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            except subprocess.CalledProcessError as e:
                # Return error information if the command fails
                return jsonify({"error": e.stderr.strip()}), 500

            # Return all raw information as a JSON string
            return parse_volume(result)

        def parse_volume(result):
  
            # Process and parse amixer output into structured JSON
            lines = result.stdout.strip().splitlines()
            parsed = {}

            # Line 1: Output name
            if lines:
                match = re.match(r"Simple mixer control '(\w+)',(\d+)", lines[0])
                if match:
                    parsed["output"] = lines[0].strip()
                    parsed["pcm"] = int(match.group(2))

            # Line 2: Capabilities
            for line in lines:
                if "Capabilities:" in line:
                    parsed["capabilities"] = line.split(":", 1)[1].strip().split()

            # Line 3: Playback channels
            for line in lines:
                if "Playback channels:" in line:
                    parsed["playback_channels"] = line.split(":", 1)[1].strip()

            # Line 4: Limits
            for line in lines:
                if "Limits:" in line:
                    parts = re.findall(r"-?\d+", line)
                    if len(parts) == 2:
                        parsed["limits"] = {
                            "playback_min": int(parts[0]),
                            "playback_max": int(parts[1])
                        }

            # Line 5: Mono playback line
            for line in lines:
                if "Mono:" in line and "Playback" in line:
                    # Example: Mono: Playback 33 [97%] [0.33dB] [on]
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

        @self.app.route('/channel/<int:channel_number>/zone', methods=['GET'])
        def channel_zone(channel_number):
            data = self.file_obj.getZoneByChannelNumber(channel_number)
            return jsonify(data), 200

        @self.app.route('/zone/<int:zone_number>/channel/<int:channel_number>/', methods=['GET'])
        def channel(zone_number, channel_number):
            data = self.file_obj.getChannel(zone_number, channel_number)
            return jsonify(data), 200

        @self.app.route('/zone/<int:zone_number>/channel/<int:channel_number>/next', methods=['GET'])
        def channel_next(zone_number, channel_number):
            return jsonify(self.file_obj.nextChannel(zone_number, channel_number)), 200

        @self.app.route('/zone/<int:zone_number>/channel/<int:channel_number>/previous', methods=['GET'])
        def channel_previous(zone_number, channel_number):
            return jsonify(self.file_obj.previousChannel(zone_number, channel_number)), 200

        @self.app.route('/zones', methods=['GET'])
        def zones():
            data = self.file_obj.getAllZones()
            if not data or "zones" not in data:
                return jsonify({"error": "No zones found"}), 404
            return jsonify(data), 200

        @self.app.route('/zone/<int:zone_number>', methods=['GET'])
        def get_zone(zone_number):
            return jsonify(self.file_obj.getZoneByIndex(zone_number)), 200

        @self.app.route('/zone/<int:zone_number>/previous', methods=['GET'])
        def zone_previous(zone_number):
            return jsonify(self.file_obj.previousZone(zone_number)), 200

        @self.app.route('/zone/<int:zone_number>/next', methods=['GET'])
        def zone_next(zone_number):
            return jsonify(self.file_obj.nextZone(zone_number)), 200

        @self.app.route('/whitelist', methods=['POST'])
        def whitelist():
            payload = request.get_json() or {}
            tgids = payload.get("tgid", [])
            if not tgids:
                return jsonify({"error": "No TGIDs provided", "payload": payload}), 400
            self.op25.switchGroup(tgids)
            return jsonify({"message": "TGIDs added to whitelist", "payload": payload}), 200

        @self.app.route('/restart', methods=['POST'])
        def restart():
            self.op25.restart()
            self.re
            return jsonify({"message": "OP25 restarted"}), 200

        log_queue = Queue()

        @self.app.route('/logging/update', methods=['POST'])
        def receive_log_update():
            data = request.get_json() or {}
            log_queue.put(data)
            return jsonify(success=True), 200

        def log_event_stream():
            while True:
                data = log_queue.get()
                yield f"data: {json.dumps(data)}\n\n"

        @self.app.route('/logging/stream', methods=['GET'])
        def logging_stream():
            return Response(log_event_stream(), mimetype='text/event-stream')

    def run(self):
        self.op25.start()
        # Launch static frontend server
        http_proc = subprocess.Popen([
            "python3", "-m", "http.server", "8000",
            "--directory", "/opt/op25-project/html"
        ])
        try:
            self.app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
        finally:
            http_proc.terminate()
            http_proc.wait()

    @staticmethod
    def free_port(port):
        try:
            result = subprocess.run(
                ["lsof", "-ti", f"TCP:{port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                if pid:
                    print(f"Killing process on port {port}, PID: {pid}")
                    os.kill(int(pid), signal.SIGKILL)
        except Exception as e:
            print(f"Error freeing port {port}: {e}")
    
    @staticmethod
    def kill_named_scripts(scripts):
        """Kill any running processes with names in the given list."""
        for name in scripts:
            try:
                result = subprocess.run(
                    ["pgrep", "-f", name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True
                )
                pids = result.stdout.strip().split("\n")
                for pid in pids:
                    if pid:
                        print(f"Killing process {name}, PID: {pid}")
                        os.kill(int(pid), signal.SIGKILL)
            except Exception as e:
                print(f"Error killing {name}: {e}")

class sound(object):

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


# ======== Launch from here ========
if __name__ == '__main__':
    api_server = API()
    #api_server.run(debug=True, host="0.0.0.0", port=5001) # Debug mode - be sure to turn off
    api_server.run() 