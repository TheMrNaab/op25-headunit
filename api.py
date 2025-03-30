# api.py
from __future__ import annotations
from queue import Queue, Empty
import subprocess
import os
import signal
from configobj import ConfigObj
from flask import Flask, Response, request, jsonify, send_file
from flask_cors import CORS
from modules.linuxSystem.sound import soundSys # Ensure this path matches your project
from modules.linuxSystem.linuxUtils import LinuxUtilities
from modules.logMonitor import LogFileWatcher, logMonitorOP25
from modules.sessionTypes import session
from modules.sessionHandler import sessionHandler 
from modules.OP25_Controller import OP25Controller
import time
import threading
from queue import Queue
import json
import logging

from modules.zoneHandler import ZoneData, Zone, Channel
from modules.myConfiguration import MyConfig
from modules.talkGroupsHandler import TalkgroupsHandler

# class errorHandler:
#     def __init__(self, api):
#         self.configManager = MyConfig()
#         self.API = api
#         LOG_FILE = self.configManager.get("paths", "app_log")
#         print("paths -> app_log", LOG_FILE)

#         # Get the root logger and configure it
#         logger = logging.getLogger()
#         logger.setLevel(logging.DEBUG)
#         for h in logger.handlers[:]:
#             logger.removeHandler(h)
#         handler = logging.FileHandler(LOG_FILE, mode="w")
#         formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
#         handler.setFormatter(formatter)
#         logger.addHandler(handler)

#         # Silence noisy libraries
#         for lib in ("watchdog", "urllib3", "urllib3.connectionpool", "requests", "root"):
#             logging.getLogger(lib).setLevel(logging.WARNING)

#     def logError(self, msg, *args, **kwargs):
#         logging.error(msg, *args, **kwargs)

#     def logInfo(self, msg, *args, **kwargs):
#         logging.info(msg, *args, **kwargs)
        
class API:
    def __init__(self):
        # self._errorHandler = errorHandler(self)
        
        # FLASK SETUP
        self.app = Flask(__name__)
        CORS(
            self.app,
            supports_credentials=True,
            resources={r"/*": {"origins": "http://192.168.1.46:8000"}}
        )
     
        # INITIALIZE CONFIGURATION & ERROR HANDLER
        self._configManager = MyConfig()
        

        # CLEANUP PORTS AND PROCESSES
        self.killAndFree()

        # STEP 1: INIT DUMMY SESSION (placeholder)
        self._session = None

        # STEP 2: INIT OP25 CONTROLLER WITH TEMP SESSION
        self._op25Manager = OP25Controller(configMgr=self.configManager)

        # STEP 3: INIT SESSION HANDLER NOW THAT CONTROLLER EXISTS
        self._sessionManager = sessionHandler(self.op25Manager, 0, 0, 0, self)

        # LOGGER STREAM FOR OP25
        self._monitor = None
        self.startLoggerStream()

        # STEP 4: SET SESSION ON CONTROLLER
        self._session = self.sessionManager.thisSession
        self.op25Manager.set_session(self._session)
        self.op25Manager.start()

        self.progress = 0
        self.lock = threading.Lock()

        # REGISTER API ROUTES
        self.register_routes()
     
    @property
    def logMonitor(self) -> logMonitorOP25:
        return self._monitor

    def set_session(self, session: session):
        self._activeSession = session
        self.session = session

    def init_from_session(self):
        files = self.session.sessionManager.op25ConfigFiles()
        self.session.activeSys.toTrunkTSV(files)

    def killAndFree(self):
        self.free_port(8000)
        self.free_port(5001)
        self.kill_named_scripts(["rx.py", "terminal.py"])

    def startLoggerStream(self):
        self._end_point = f"{self.configManager.get('hosts', 'api_host')}/controller/logging/update"
        self._monitor = logMonitorOP25(self, file=self.configManager.get("paths", "stderr_file"), endpoint=self._end_point)
        self._watcher = LogFileWatcher(self._monitor)
        self._watcher.start_in_thread()
        self._log_queue = Queue()
        
    @property
    def logQueue(self) -> Queue:
        return self._log_queue

    @property
    def configManager(self) -> ConfigObj:
        return self._configManager

    @property
    def op25Manager(self) -> OP25Controller:
        return self._op25Manager
    
    @property
    def sessionManager(self) -> sessionHandler:
        return self._sessionManager 

    @property
    def activeSession(self) -> session:
        return self.sessionManager.thisSession
    
    @property
    def zoneManager(self) -> ZoneData:
        return self.sessionManager.zoneManager

    def register_routes(self):

        # ====== SYSTEM CONTROL ======

        # 1: [GET] Get system volume level (0–100)
        @self.app.route('/volume/simple', methods=['GET'])
        def get_volume():
            return soundSys.get_volume_percent()

        # 2: [POST] Set system volume level
        @self.app.route('/volume/<int:level>', methods=['POST'])
        def set_volume(level):
            return soundSys.set_volume(level)
        
        # ====== SYSTEM UTILITIES & CONTROL ======

        @self.app.route('/utilities/qrcode/<path:content>', methods=['GET'])
        def generate_qr(content):
            img_io = LinuxUtilities.generate_qrcode_image(content)
            return send_file(img_io, mimetype='image/png')


        # ====== DISPLAY SLEEP SETTINGS ======

        @self.app.route('/config/openbox/display/<int:id>/sleep/set/<int:timeout>', methods=['POST'])
        def set_display_timeout(id, timeout):
            try:
                LinuxUtilities.set_display_timeout(id, timeout)
                return jsonify({"display_id": id, "sleep_timeout_minutes": timeout})
            except subprocess.CalledProcessError:
                return jsonify({"error": "Failed to set display timeout"}), 500

        @self.app.route('/config/openbox/display/<int:id>/sleep', methods=['GET'])
        def get_display_timeout(id):
            try:
                timeout = LinuxUtilities.get_display_timeout(id)
                return jsonify({"sleep_timeout_minutes": timeout})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        

        # ====== DEVICE SLEEP SETTINGS ======

        @self.app.route('/config/openbox/device/sleep/set/<int:timeout>', methods=['POST'])
        def set_device_sleep_timeout(timeout):
            try:
                LinuxUtilities.set_device_sleep_timeout(timeout)
                return jsonify({"sleep_timeout_minutes": timeout})
            except subprocess.CalledProcessError:
                return jsonify({"error": "Failed to set device sleep timeout"}), 500

        @self.app.route('/config/openbox/device/sleep', methods=['GET'])
        def get_device_sleep_timeout():
            try:
                timeout = LinuxUtilities.get_device_sleep_timeout()
                return jsonify({"sleep_timeout_minutes": timeout})
            except Exception as e:
                return jsonify({"error": str(e)}), 500


        # ====== DISPLAY LISTING ======

        @self.app.route('/config/openbox/device/displays', methods=['GET'])
        def list_displays():
            try:
                return jsonify(LinuxUtilities.list_displays())
            except Exception as e:
                return jsonify({"error": str(e)}), 500


        # ====== SYSTEM NETWORK STATUS ======

        #1: [GET] NETWORK STATUS
        @self.app.route('/config/network', methods=['GET'])
        def get_network_status():
            return jsonify(LinuxUtilities.get_network_status())

        # ====== CHANNEL DATA BY ZONE ======

        # 3: [GET] Get channel by zone and channel number
        @self.app.route('/zone/<int:zone_number>/channel/<int:channel_number>', methods=['GET'])
        def channel(zone_number, channel_number):
            return jsonify(self.zoneManager.getChannel(zone_number, channel_number)), 200

        # 4: [GET] Get next channel in the zone
        @self.app.route('/zone/<int:zone_number>/channel/<int:channel_number>/next', methods=['GET'])
        def channel_next(zone_number, channel_number):
            return jsonify(self.zoneManager.getNextChannel(zone_number, channel_number)), 200

        # 5: [GET] Get previous channel in the zone
        @self.app.route('/zone/<int:zone_number>/channel/<int:channel_number>/previous', methods=['GET'])
        def channel_previous(zone_number, channel_number):
            return jsonify(self.zoneManager.getPreviousChannel(zone_number, channel_number)), 200

        # ====== ACTIVE SESSION STATE ======

        # 6: [GET] Return one field from the active channel
        @self.app.route('/session/channel/field/<field_name>', methods=['GET'])
        def get_active_channel_property(field_name):
            if not self.activeSession.activeChannel:
                return {"error": "No active channel in session"}, 400
            channel_dict = self.activeSession.activeChannel.to_dict()
            if field_name in channel_dict:
                return jsonify({field_name: channel_dict[field_name]})
            return {"error": f"Field '{field_name}' not found in active channel"}, 404

        # 7: [GET] Get the full active channel object
        @self.app.route('/session/channel', methods=['GET'])
        def get_active_channel_object():
            if not self.activeSession.activeChannel:
                return {"error": "No active channel in session"}, 400
            return jsonify(self.activeSession.activeChannel.to_dict())

        # 8: [GET] Get the full active zone object
        @self.app.route('/session/zone', methods=['GET'])
        def get_active_zone_object():
            if not self.activeSession.activeChannel:
                return {"error": "No active zone in session"}, 400
            return jsonify(self.activeSession.activeZone.to_dict())

        # 9: [GET] Get name of TGID from active system
        @self.app.route('/session/talkgroups/<tgid>/name/plaintext', methods=['GET'])
        def get_active_tgid_name(tgid):
            if not self.activeSession.activeTGIDList:
                return {"error": "No active TGID list in session"}, 400
            return self.activeSession.activeTGIDList.getTalkgroup(tgid)

        # 10: [GET] Get all TGIDs from active system
        @self.app.route('/session/talkgroups', methods=['GET'])
        def get_active_tgid_object():
            if not self.activeSession.activeTGIDList:
                return {"error": "No active TGID list in session"}, 400
            return jsonify(self.activeSession.activeTGIDList.to_dict())

        # ====== SESSION MODIFIERS ======

        # 11: [PUT] Set active channel by ID
        @self.app.route('/session/channel/<int:id>', methods=['PUT'])
        def set_active_channel(id):
            zone_index = self.activeSession.activeZoneIndex
            ch_data = self.sessionManager.zoneManager.getChannel(zone_index, id)
            if not ch_data:
                return {"error": f"Channel {id} not found in zone {zone_index}"}, 404
            zone = self.sessionManager.zoneManager.getZoneByIndex(zone_index)
            channel = Channel(ch_data, zone_index)
            sys = self.sessionManager.systemsManager.getSystemByIndex(channel.sysid)
            if not sys:
                return {"error": f"System with sysid {channel.sysid} not found"}, 404
            self.activeSession.updateSession(channel, zone, sys)
            return {"message": "Channel updated successfully"}

        # 12: [PUT] Move to next channel
        @self.app.route('/session/channel/next', methods=['PUT'])
        def next_channel():
            return self.activeSession.nextChannel()

        # 13: [PUT] Move to previous channel
        @self.app.route('/session/channel/previous', methods=['PUT'])
        def previous_channel():
            return self.activeSession.previousChannel()

        # 14: [PUT] Set zone by index (loads first channel)
        @self.app.route('/session/zone/<int:id>', methods=['PUT'])
        def set_active_zone(id):
            zone = self.sessionManager.zoneManager.getZoneByIndex(id)
            if not zone:
                return {"error": f"Zone {id} not found"}, 404
            channels = zone.channels
            if not channels:
                return {"error": "Zone has no channels"}, 404
            channel = channels[0]
            sys = self.sessionManager.systemsManager.getSystemByIndex(channel.sysid)
            if not sys:
                return {"error": f"System with sysid {channel.sysid} not found"}, 404
            self.activeSession.updateSession(channel, zone, sys)
            return {"message": "Zone updated successfully"}

        # 15: [PUT] Move to next zone (loads first channel)
        @self.app.route('/session/zone/next', methods=['PUT'])
        def next_zone():
            return self.activeSession.nextZone()

        # 16: [PUT] Move to previous zone (loads first channel)
        @self.app.route('/session/zone/previous', methods=['PUT'])
        def previous_zone():
            return self.activeSession.previousZone()

        # ====== ZONE DATA ======

        # 17: [GET] All zones from zones.json
        @self.app.route('/zones', methods=['GET'])
        def getAllZones():
            return jsonify(self.zoneManager.data)

        # 18: [GET] Zone by index
        @self.app.route('/zone/<int:zone_number>', methods=['GET'])
        def get_zone(zone_number):
            zone = self.zoneManager.getZoneByIndex(zone_number)
            if not zone:
                return jsonify({"error": "Zone not found"}), 404
            return jsonify(zone.to_dict()), 200

        # 19: [GET] Previous zone
        @self.app.route('/zone/<int:zone_number>/previous', methods=['GET'])
        def zone_previous(zone_number):
            return jsonify(self.zoneManager.previousZone(zone_number)), 200

        # 20: [GET] Next zone
        @self.app.route('/zone/<int:zone_number>/next', methods=['GET'])
        def zone_next(zone_number):
            return jsonify(self.zoneManager.nextZone(zone_number)), 200
       
        # ======    OP25 RADIO CONTROLS      =======
        
        # 21: TODO: WHITELIST TGIDS (SWITCH TGIDS)
        @self.app.route('/session/controller/whitelist', methods=['POST'])
        def whitelist():
            payload = request.get_json() or {}
            tgids = payload.get("tgid", [])
            channel = Channel(payload)

            if not tgids:
                return jsonify({"error": "No TGIDs provided", "payload": payload}), 400
            
            # SEND ARRAY OF WHITELISTED TALKGROUPS TO CONTROLLER
            self.op25Manager.switchGroup(tgids)

            return jsonify({"message": "TGIDs added to whitelist", "payload": payload}), 200
        
        # 22: BLACKLIST TGID (LOCKOUT COMMAND IN CONTROLLER)
        @self.app.route('/session/controller/lockout/<int:tgid>', methods=['PUT'])
        def put_lockout(tgid):
            # NOTE: CONSTRUCT LATER
            # NOTE: ENSURE WE TRACK THE LOCK OUT AND CLEAR IT BEFORE CHANGING CHANNELS (UPDATE COMMAND)
            # NOTE: I DO NOT THINK WE NEED TO REWRITE FILES FOR THIS
            return jsonify({"Error":"Function requires implementation"})
        
        # 23: LOCK ONTO TGID (LOCK COMMAND IN CONTROLLER)
        @self.app.route('/session/controller/hold/<int:tgid>', methods=['PUT'])
        def put_hold(tgid):
            # NOTE: CONSTRUCT LATER
            # NOTE: ENSURE WE TRACK THE HOLD AND CLEAR IT BEFORE CHANGING CHANNELS (UPDATE COMMAND)
            # NOTE: AND REWRITE THE BLACKLIST FILE CONTENTS
            return jsonify({"Error":"Hold function requires implementation"})

        # 24: [PUT] RESTART OP25 
        @self.app.route('/controller/restart', methods=['PUT'])
        def restart():
            self.op25Manager.restart()
            return jsonify({"message": "OP25 restarted"}), 200

        # ======    STREAMING & LOGGING      =======

        # 25: [POST] Receive log data for SSE broadcast
        @self.app.route('/controller/logging/update', methods=['POST'])
        def receive_log_update():
            data = request.get_json() or {}
            self.logQueue.put(data)
            return jsonify(success=True), 200

        # 26: [GET] Stream log data as Server-Sent Events (SSE)
        @self.app.route('/controller/logging/stream', methods=['GET'])
        def logging_stream():
            
            def log_event_stream():
                while True:
                    try:
                        data = self.logQueue.get(timeout=5)
                        yield f"data: {json.dumps(data)}\n\n"
                    except Empty:
                        # Prevent client timeout
                        yield f": keep-alive\n\n"
            return Response(log_event_stream(), mimetype='text/event-stream')

        # 27: [GET] Stream OP25 TGID update progress (0–100) as SSE
        @self.app.route('/controller/progress', methods=['GET'])
        def get_stream_progress():
            """Streams the current TGID update progress as plain text using SSE."""
            def progress_streamer():
                while True:
                    with self.lock:
                        current = self.progress
                    yield f"data: {current}\n\n"
                    time.sleep(1)
            return Response(progress_streamer(), mimetype="text/event-stream")

        # 28: [POST] Update TGID progress value (0–100)
        @self.app.route('/controller/progress/update/<int:percent>', methods=['POST'])
        def update_progress(percent):
            """Updates the current progress value. JSON input can override the URL value."""
            data = request.get_json()
            with self.lock:
                self.progress = data.get("progress", percent)
            return jsonify(success=True)

    def run(self):

        # This is the reloader child — run normal startup
        # self.op25Manager.start(self.activeSession)

        self.free_port(8000)
        self.free_port(5001)
        #self.kill_named_scripts(["rx.py", "terminal.py"])

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



# ======== Launch from here ========
if __name__ == '__main__':
    api_server = API()
    #api_server.run(debug=True, host="0.0.0.0", port=5001) # Debug mode - be sure to turn off
    #TODO: Delete temporary files on exit, but how?
    api_server.run() 