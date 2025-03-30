#OP25_Controller.py
import subprocess
import os
import time
import socket
import subprocess
import json
from typing import List
from modules.sessionTypes import session
from modules.myConfiguration import MyConfig
from modules.systemsHandler import OP25FilesPackage
#  echo '{"command": "whitelist", "arg1": 47021, "arg2": 0}' | nc -u 127.0.0.1 5000

class OP25Controller:
    def __init__(self, configMgr:MyConfig):
        
        # SET MANAGERS
        self.configManager = configMgr
        self._activeSession = None

        # SET CUSTOM CONFIGURATIONS
        # TODO: Replace with configuration paths
        self._rx_script = os.path.expanduser("~/op25/op25/gr-op25_repeater/apps/rx.py")
        self._stderr_file = os.path.expanduser("/opt/op25-project/logs/stderr_op25.log")
        self._stdout_file = os.path.expanduser("/opt/op25-project/logs/stdout_op25.log")

        # SET PERSISTENT ENVOIRNMENTAL VARIABLES CORRECTLY
        os.environ["PYTHONPATH"] = os.environ.get("PYTHONPATH", "") + ":" + self.configManager.get("paths", "pythonpath")

        # KILL EXISTING PROCESSES
        subprocess.run(["pkill", "-f", "rx.py"])

        self.session:session = None
        
    def set_session(self, session):
        self._activeSession = session
        self.session = session

    @property
    def rx_script(self):
        return self._rx_script
    
    @property
    def stderr_file(self):
        return self._stderr_file
    
    @property
    def stdout_file(self):
        return self._stdout_file
        
    def start(self, session_obj: session):
        if session_obj:
            self._activeSession = session_obj
            self.session = session_obj

        if not self.session:
            print("[ERROR] No session available. Cannot start OP25.")
            return

        self.op25_command = [
            self.rx_script, "--nocrypt", "--args", "rtl",
            "--gains", "lna:35", "-S", "960000", "-q", "0",
            "-v", "1", "-2", "-V", "-U",
            "-T", self.session.activeSystem.toTrunkTSV(session_obj),
            "-U", "-l", "5000"
        ]
        
        print(self.op25_command)

        # Start subprocess
        self.op25_process = subprocess.Popen(
            self.op25_command,
            stdout=open(self.stdout_file, "w"),
            stderr=open(self.stderr_file, "w"),
            text=True
        )

        time.sleep(3)  # Wait for startup

        if self.isConnected():
            print("Connection Status:", "OP25 Connected")
        else:
            print("[WARNING] OP25 may not have connected successfully.")

    def isConnected(self, timeout=30):
        """Continuously check for 'Reconfiguring NAC' in the log file until found or timeout."""
        print("...", "isConnected()")
        start_time = time.time()

        while time.time() - start_time < timeout:
            if os.path.exists(self.stderr_file):
                with open(self.stderr_file, "r") as file:
                    if "Reconfiguring NAC" in file.read():
                        return True  # Found the phrase, return immediately
            
            time.sleep(1)  # Wait 1 second before checking again

        return False  # Timed out after 30 seconds

    def send_udp_command(self, command, arg2=0):
        try:
            server_address = ('127.0.0.1', 5000)  # Target address and port
            buffer_size = 1024  # Buffer size for receiving response

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                message = json.dumps({"command": command, "arg1": arg2, "arg2": 0})
                sock.sendto(message.encode(), server_address)

                response, _ = sock.recvfrom(buffer_size)
                response_data = json.loads(response.decode())

                return response_data  # Return the received JSON response

        except (socket.error, json.JSONDecodeError) as e:
            print(f"[ERROR] Failed to send command '{command}': {e}")
            return None  # Return None on failure

    def stop(self):
        """Stops the OP25 process if running."""
        if self.op25_process and self.op25_process.poll() is None:
            self.op25_process.terminate()
            self.op25_process.wait()
            print("[DEBUG] OP25 process terminated.")
            subprocess.run(["pkill", "-f", "rx.py"])        #TODO: Send API request to end gracefuuly
                                                            #TODO: PKILL ensures rx.py is closed for now 

    @property
    def activeSession (self):
        return self._activeSession

    def switchTalkgroup(self, thisSession:session):
        """Switches OP25 to a new talkgroup."""
        if not self.op25_process or self.op25_process.poll() is not None:
            print("[ERROR] OP25 is not running.")
            return



        # Command to reload OP25 configuration, assuming self.command is implemented
        self.command("reload", 0)

    def switchSystem(self, thisSession:session):
        """Switches OP25 to a new P25 system with the first zone and channel set automatically."""
        #TODO: Implement multisystem

        # Command to reload OP25 configuration, assuming self.command is implemented
        
        #self.command("reload", 0)
        pass

    def command(self, cmd, data):
        """Sends a command to OP25. Ensures proper handling for hold, whitelist, and reload."""
        time.sleep(1) 
        
        if cmd not in ["hold", "whitelist", "skip", "lockout", "reload"]:
            print(f"[ERROR] Invalid command: {cmd}")
            return

        # 🔹 Step 1: Ensure hold TGIDs are whitelisted before holding
        if cmd == "hold":
            if data not in self.whitelist_tgids:
                print(f"[INFO] TGID {data} not in whitelist. Adding before hold.")
                self.whitelist([data])

            response = self.send_udp_command(cmd, data)
            if response:
                pass
                # print(f"[SUCCESS] Hold command sent for TGID {data}.")
            else:
                print(f"[ERROR] Failed to hold TGID {data}. No response received.")

        elif cmd == "whitelist":
            response = self.send_udp_command(cmd, data)  # Directly send the command
            if response:
                pass
                #print(f"[SUCCESS] Whitelisted TGID {data}.")
            else:
                print(f"[ERROR] Failed to whitelist TGID {data}. No response received.")

        # 🔹 Step 3: Handle reload command - Fully reload both whitelist & blacklist
        elif cmd == "reload":
            response = self.send_udp_command(cmd, 0)  # Reset OP25 state
            if response:
                print("[SUCCESS] OP25 reload command executed.")
                time.sleep(1)  # Ensure OP25 has time to process reload
                # 🔹 Step 3B: Reapply stored whitelist TGIDs after reset
                # if self.whitelist_tgids:
                #     self.whitelist(self.whitelist_tgids)
            else:
                print("[ERROR] OP25 reload command failed. No response received.")

        # 🔹 Step 4: Handle all other commands and verify response
        elif cmd=="lockout":
            response = self.send_udp_command(cmd, data)
            if response:
                pass
                #print(f"[SUCCESS] Command '{cmd}' executed with data: {data}.")
            else:
                print(f"[ERROR] Command '{cmd}' failed. No response received.")

    def update_scan_list(self, new_tgids: List[int]):
        """Updates the scan list by writing TGIDs directly to the whitelist file, then reloads OP25."""
        
        print("[DEBUG] Updating Scan List...")
        
        if not new_tgids:
            print("[ERROR] No TGIDs provided for scan list update.")
            return
        
        total_items = len(new_tgids)
        print(f". . . . . Total TGIDs in new scan list: {total_items}")

        # Step 1: Write TGIDs to the whitelist file
        try:
            with open(self.defaultWhitelistFile, 'w') as wl_file:
                for tgid in new_tgids:
                    wl_file.write(f"{tgid}\n")
                    print(f". . . . . Writing TGID to whitelist file: {tgid}")
        except Exception as e:
            print(f"[ERROR] Failed to write whitelist file: {e}")
            return

        # Step 2: Reload OP25 to apply new whitelist
        print("[INFO] Sending OP25 reload command...")
        response = self.command("reload", 0)
        
        if not response:
            print("[ERROR] OP25 reload command failed. Scan list update aborted.")
            return

        print("[INFO] Scan list update complete.")
    
    def restart(self):
        print("[INFO] Restarting OP25...")
        self.stop()
        self.start()