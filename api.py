# api.py
from __future__ import annotations
from queue import Queue, Empty
import subprocess
import os
import signal
from flask import Flask, Response, request, jsonify, send_file
from flask_cors import CORS, cross_origin
from modules.linuxSystem.sound import soundSys # Ensure this path matches your project
from modules.linuxSystem.linuxUtils import LinuxUtilities
from modules.logMonitor import LogFileWatcher, logMonitorOP25
from modules._session import SessionMember
from modules._sessionManager import SessionManager
from modules._op25Manager import op25Manager
from modules.myConfiguration import MyConfig
import time
import threading
from queue import Queue
import json
from modules._zoneManager import zoneMember, channelMember
from modules._talkgroupSet import TalkgroupManager

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)  # or logging.CRITICAL to suppress even more
  
class API:
    def __init__(self):
        # SET THE CROSS-ORIIGINS IP ADDRESS TO THE ROUTER-ASSIGNED IP
        # THIS PROCESS IS REDUNDANT TO THE DYNAMIC CROSS-ORIGIN FUNCTION
        # BUT IT IS HERE FOR LEGACY REASONS

        # FLASK SETUP
        self.app = Flask(__name__)
        CORS(
            self.app,
            supports_credentials=True,
            resources={r"/*": {
                "origins": [
                    f"http://{LinuxUtilities.get_local_ip()}:8000",
                    "http://localhost:8000"
                ]
            }}
        )

        # INITIALIZE CONFIGURATION & ERROR HANDLER
        self._configManager = MyConfig()
        

        # CLEANUP PORTS AND PROCESSES
        self.killAndFree()

        # STEP 1: INIT DUMMY SESSION (placeholder)
        self._session = None
        
         # STEP 2: INIT OP25 CONTROLLER WITH TEMP SESSION
        self._op25Manager = op25Manager(configMgr=self.configManager)


        # STEP 3: INIT SESSION HANDLER NOW THAT CONTROLLER EXISTS
        self._sessionManager = SessionManager(self.op25Manager,
                                             defaultSystemIndex=0,
                                             defaultZoneIndex=0,
                                             defaultChannelIndex=0,
                                             api=self)
        
       


        # LOGGER STREAM FOR OP25
        self._monitor = None
        self.startLoggerStream()

        # STEP 4: SET SESSION ON CONTROLLER
        if self._sessionManager is None:
            raise Exception("SessionManager is not initialized")
        
        if self.sessionManager.thisSession is None:
            raise Exception("Session is not initialized")

        self._session = self.sessionManager.thisSession # MUST BE GROUPED TOGETHER
        self.op25Manager.set_session(self._session) # MUST BE GROUPED TOGETHER
        self.op25Manager.start(self._session) # MUST BE ONE OF THE LAST CALLS IN INIT()
        
        self.progress = 0
        self.lock = threading.Lock()

        # REGISTER API ROUTES
        self.register_routes()
     
    @property
    def logMonitor(self) -> logMonitorOP25:
        return self._monitor

    def set_session(self, session: SessionMember):
        self._activeSession = session
        self.session = session

    def init_from_session(self):
        #files = self.session.sessionManager.op25ConfigFiles()
        #self.session.activeSys.toTrunkTSV(files)
        pass
    
    def killAndFree(self):
        """Kill any processes running on the specified ports and free them."""
        self.free_port(8000)
        self.free_port(5001)
        self.kill_named_scripts(["rx.py", "terminal.py"])

    def startLoggerStream(self):
        """Starts the logger stream for OP25. This process is responsible for reading the 
        OP25 log file and sending updates to the API server. Without it running, the UI
        cannot receive updates.
        """
        self._end_point = f"http://127.0.0.0:5001/controller/logging/update"
        self._monitor = logMonitorOP25(self, file=self.configManager.get("paths", "stderr_file"), endpoint=self._end_point)
        self._watcher = LogFileWatcher(self._monitor)
        self._watcher.start_in_thread()
        self._log_queue = Queue()
        
    @property
    def logQueue(self) -> Queue:
        """Returns the log queue."""
        return self._log_queue

    @property
    def configManager(self) -> MyConfig:
        """Returns the configuration manager."""
        return self._configManager

    @property
    def op25Manager(self) -> op25Manager:
        """Returns the OP25 manager."""
        return self._op25Manager
    
    @property
    def sessionManager(self) -> sessionManager:
        """Returns the session manager."""
        return self._sessionManager 

    @property
    def activeSession(self) -> SessionMember:
        """Returns the active session from the session manager."""
        return self.sessionManager.thisSession
    
    @property
    def zoneManager(self) -> zoneMember:
        """Returns the zone manager from the session manager."""
        return self.sessionManager.zoneManager
    
    def dynamic_cross_origin(self):
        """Dynamically set CORS headers based on the request origin."""
        
        ip = f"http://{LinuxUtilities.get_local_ip()}:8000"
        allowed_origins = ALLOWED_ORIGINS = [
            ip,
            "http://localhost:8000"
        ]
        return cross_origin(origins=allowed_origins, supports_credentials=True)

    def register_routes(self):

        # ====== SYSTEM CONTROL ======
        # 1: [GET] Get system volume level (0–100)
        @self.app.route('/volume/simple', methods=['GET'])
        def get_volume():
            return soundSys.get_volume_percent()

        # 2: [POST] Set system volume level
        @self.app.route('/volume/<int:level>', methods=['PUT'])
        def set_volume(level):
            return soundSys.set_volume(level)
        
        # [GET] Returns the active sound device address
        @self.app.route('/device/audio/properties', methods=['GET'])
        def get_audio_properties():
            return LinuxUtilities.get_audio_sink_properties()
        
        # [GET] Returns a specific property from the active sound device
        @self.app.route('/device/audio/properties/<property>', methods=['GET'])
        def get_audio_property(property):
            props = LinuxUtilities.get_audio_sink_properties()
            if "error" in props:
                return jsonify(props), 500

            if property in props:
                return jsonify({property: props[property]})
            else:
                return jsonify({"error": f"Property '{property}' not found"}), 404
        
        # ====== SYSTEM UTILITIES & CONTROL ======
        @self.app.route('/utilities/qrcode/<path:content>', methods=['GET'])
        def generate_qr(content):
            img_io = LinuxUtilities.generate_qrcode_image(content)
            return send_file(img_io, mimetype='image/png')


        # ====== DISPLAY SLEEP SETTINGS ======
        @self.app.route('/config/openbox/display/<int:id>/sleep/set/<int:timeout>', methods=['PUT'])
        @self.dynamic_cross_origin()
        def set_display_timeout(id, timeout):
            try:
                LinuxUtilities.set_display_timeout(id, timeout)
                return jsonify({"display_id": id, "sleep_timeout_minutes": timeout})
            except subprocess.CalledProcessError:
                return jsonify({"error": "Failed to set display timeout"}), 500

        @self.app.route('/config/openbox/display/<int:id>/sleep', methods=['GET'])
        @self.dynamic_cross_origin()
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
        @self.dynamic_cross_origin()
        def get_active_channel_object():
            if not self.activeSession.activeChannel:
                return {"error": "No active channel in session"}, 400
            return jsonify(self.activeSession.activeChannel.to_dict())
        
        # 7: [PUT] Go to the channel of the current zone
        @self.app.route('/session/channel/go/<int:channel_number>', methods=['PUT'])
        @self.dynamic_cross_origin()
        def go_session_channel(channel_number):
            return jsonify(self.activeSession.goChannel(channel_number)), 200


        # 8: [GET] Get the full active zone object
        @self.app.route('/session/zone', methods=['GET'])
        @self.dynamic_cross_origin()
        def get_active_zone_object():
            if not self.activeSession.activeChannel:
                return {"error": "No active zone in session"}, 400
            return jsonify(self.activeSession.activeZone.to_dict())

        # 9: [GET] Get name of TGID from active system
        @self.app.route('/session/talkgroups/<tgid>/name/plaintext', methods=['GET'])
        @self.dynamic_cross_origin()
        def get_active_tgid_name(tgid):
            tg = self.sessionManager.talkgroupsManager.getTalkgroupName(self.activeSession.activeSysIndex, tgid);
            if not tg:
                return jsonify({"error": f"Talkgroup {tgid} not found in system {self.activeSession.activeSysIndex}."}), 404
            return jsonify({"name": f"{tg}"}), 200

        # 10: [GET] Get all TGIDs from active system
        @self.app.route('/session/talkgroups', methods=['GET'])
        def get_active_tgid_object():
            if not self.activeSession.activeTGIDList:
                return {"error": "No active TGID list in session"}, 400
            return jsonify(self.activeSession.activeTGIDList.to_dict())

        # ====== SESSION MODIFIERS ======

        # 11: [PUT] Set active channel by ID
        @self.app.route('/session/channel/<int:id>', methods=['PUT'])
        @self.dynamic_cross_origin()
        def set_active_channel(id):
            zone_index = self.activeSession.activeZoneIndex
            channel = self.sessionManager.zoneManager.getChannel(zone_index, id) # MODIFIED FOR ERROR CHECKING
            if not channel:
                return {"error": f"Channel {id} not found in zone {zone_index}"}, 404
            zone = self.sessionManager.zoneManager.getZoneByIndex(zone_index)
             
            sys = self.sessionManager.systemsManager.getSystemByIndex(channel.sysid)
            if not sys:
                return {"error": f"System with sysid {channel.sysid} not found"}, 404
            self.activeSession.update_session(channel, zone, sys)
            return {
                "message": "Channel updated successfully",
                "SysIndex": self.sessionManager.thisSession.activeSysIndex
            }
        
        @self.app.route('/session/zone/<int:zn>/channel/<int:ch>', methods=['PUT'])
        @self.dynamic_cross_origin()
        def set_active_zone_channel(zn,ch):
            channel = self.sessionManager.zoneManager.getChannel(zn, ch) # MODIFIED FOR ERROR CHECKING
            if not channel:
                return {"error": f"Channel {ch} not found in zone {zn}"}, 404
            zone = self.sessionManager.zoneManager.getZoneByIndex(zn)
            sys = self.sessionManager.systemsManager.getSystemByIndex(channel.sysid)
            if not sys:
                return {"error": f"System with sysid {channel.sysid} not found"}, 404
            self.activeSession.update_session(channel, zone, sys)
            return {
                "message": "Channel updated successfully",
                "SysIndex": self.sessionManager.thisSession.activeSysIndex
            }

        # 12: [PUT] Move to next channel
        @self.app.route('/session/channel/next', methods=['PUT'])
        @self.dynamic_cross_origin()
        def next_channel():
            return self.activeSession.nextChannel()


        # 13: [PUT] Move to previous channel
        @self.app.route('/session/channel/previous', methods=['PUT'])
        @self.dynamic_cross_origin()
        def previous_channel():
            return self.activeSession.previousChannel()

        # 14: [PUT] Set zone by index (loads first channel)
        @self.app.route('/session/zone/<int:id>', methods=['PUT'])
        @self.dynamic_cross_origin()
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
            return jsonify(self.zoneManager._data)

        # 18: [GET] Zone by index
        @self.app.route('/zone/<int:zone_number>', methods=['GET'])
        def get_zone(zone_number):
            zone = self.zoneManager.getZoneByIndex(zone_number)
            if not zone:
                return jsonify({"error": "Zone not found"}), 404
            return jsonify(zone.to_dict()), 200

        # 19: [GET] Previous zone
        @self.app.route('/zone/<int:zone_number>/previous', methods=['GET'])
        @self.dynamic_cross_origin()
        def zone_previous(zone_number):
            return jsonify(self.zoneManager.previousZone(zone_number)), 200

        # 20: [GET] Next zone
        @self.app.route('/zone/<int:zone_number>/next', methods=['GET'])
        @self.dynamic_cross_origin()
        def zone_next(zone_number):
            return jsonify(self.zoneManager.nextZone(zone_number)), 200
       
        # ======    OP25 RADIO CONTROLS      =======
        
        # 21: TODO: WHITELIST TGIDS (SWITCH TGIDS)
        @self.app.route('/session/controller/whitelist', methods=['POST'])
        @self.dynamic_cross_origin()
        def whitelist():
            payload = request.get_json() or {}
            tgids = payload.get("tgid", [])
            channel = channelMember(payload)

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
        
        # ADMIN PORTAL #
        
        # 29: [GET] GET THE ENTIRE SYSTEMS FILE
        @self.app.route('/admin/systems/', methods=['GET'])
        def admin_systems_get():
            return jsonify(self.sessionManager.systemsManager.data), 200
        
        # 30:[POST] UPDATE THE ENTIRE SYSTEMS FILE
        @self.app.route('/admin/systems/update', methods=['POST'])
        @self.dynamic_cross_origin()
        def admin_systems_post():
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data received"}), 400
            try:
                self.sessionManager.systemsManager.update(data)  # your existing update logic
                return jsonify({"status": "ok"}), 200  # ✅ must return something
            except Exception as e:
                return jsonify({"error": str(e)}), 500  # ✅ handles errors gracefully
                data = request.get_json()
                
        # 31: [GET] Get all TGIDs
        @self.app.route('/admin/talkgroups/all', methods=['GET'])
        def get_all_tgid_objects():
            return jsonify(self.sessionManager.talkgroupsManager._data)

        # 30:[POST] UPDATE THE ENTIRE ZONES FILE
        @self.app.route('/admin/zones/update', methods=['POST'])
        @self.dynamic_cross_origin()
        def admin_update_zones_post():
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data received"}), 400
            try:
                self.sessionManager.zoneManager.update(data)  # Call your updated method
                return jsonify({"status": "ok"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    
        # 31: [GET] GET CONFIG FILE
        @self.app.route('/admin/config/get', methods=['GET'])
        @self.dynamic_cross_origin()
        def get_config_file():
            config = self.configManager.toJson()
            return jsonify(config), 200
        
        # 31: [GET] GET CONFIG FILE
        @self.app.route('/admin/config/set', methods=['POST'])
        @self.dynamic_cross_origin()
        def update_config_file():
            config = self.configManager.update(request.get_json())
            return jsonify(config), 200
        
        # 32: [GET] GET SPECIFIC DEVICE SETTING
        @self.app.route('/admin/config/device/<property>', methods=['GET'])
        @self.dynamic_cross_origin()
        def get_device_config(property):
            config = {
                "timeout": LinuxUtilities.get_display_timeout("0")
            }
            if property == "sleep":
                return jsonify(config), 200
        
        @self.app.route("/config/op25/get", methods=["GET"])
        @self.dynamic_cross_origin()
        def get_op25_config():
            settings = self._configManager.fetchOP25Settings()
            return settings, 200

        @self.app.route("/config/op25/post", methods=["POST"])
        @self.dynamic_cross_origin()
        def post_op25_config():
            try:
                settings_update = request.get_json(force=True)
                if not isinstance(settings_update, dict):
                    return {"error": "Invalid JSON format"}, 400

                self._configManager.updateOP25Settings(settings_update)
                return {"status": "success"}, 200

            except Exception as e:
                return {"error": str(e)}, 500
            
        @self.app.route("/config/reload", methods=["GET"])
        @self.dynamic_cross_origin()     
        def reload_config_file():
            try:
                self.configManager.reload()
                return {"success": "reload command sent."}, 200
            except Exception as e:
                return {"error": str(e)}, 500
            
        @self.app.route("/config/talkgroups/post", methods=["POST"])
        @self.dynamic_cross_origin()     
        def post_talkgroups_file():
            try:
                tgupdate = request.get_json(force=True)
                self.sessionManager.talkgroupsManager.update(tgupdate)
                return {"success": "reload command sent."}, 200
            except Exception as e:
                return {"error": str(e)}, 500
            
        @self.app.route("/config/audio-devices", methods=["GET"])
        @self.dynamic_cross_origin()  
        def list_audio_devices():
            devices = soundSys.parse_hw_devices()
            return jsonify(devices)

        
    def run(self):
        self.free_port(8000)
        self.free_port(5001)
        #self.kill_named_scripts(["rx.py", "terminal.py"])

        # Launch static frontend server
        http_proc = subprocess.Popen([
            "python3", "-m", "http.server", "8000",
            "--directory", "/opt/op25-project/html"
        ])
        try:
            self.app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
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
                    print(f"[INFO] Killing process on port {port}, PID: {pid}")
                    os.kill(int(pid), signal.SIGKILL)
        except Exception as e:
            print(f"[ERROR] freeing port {port}: {e}")
    
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
                        print(f"[INFO] Killing process {name}, PID: {pid}")
                        os.kill(int(pid), signal.SIGKILL)
            except Exception as e:
                print(f"[INFO] Error killing {name}: {e}")



# ======== Launch from here ========
if __name__ == '__main__':
    # Initialize the API server
    api_server = API()
    #TODO: Delete temporary files on exit, but how?
    api_server.run()