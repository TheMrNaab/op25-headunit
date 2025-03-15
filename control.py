import subprocess
import os
import time
import socket
import socket
import subprocess
import json
from typing import List
from logger import CustomLogger
from typing import List
#  echo '{"command": "whitelist", "arg1": 47021, "arg2": 0}' | nc -u 127.0.0.1 5000

class OP25Controller:
    def __init__(self):
        # Define OP25 executable path
        self.rx_script = os.path.expanduser("~/op25/op25/gr-op25_repeater/apps/rx.py")
        self.trunk_file = os.path.expanduser("~/op25/op25/gr-op25_repeater/apps/_trunk.tsv")
        self.stderr_file = os.path.expanduser("/opt/op25-project/logs/stderr.2")

        self.defaultWhitelistFile = os.path.expanduser("~/op25/op25/gr-op25_repeater/apps/_whitelist.tsv")
        self.defaultBlacklistFile = os.path.expanduser("~/op25/op25/gr-op25_repeater/apps/_blist.tsv")

        self.whitelist_tgids = self.load_tgid_file(self.defaultWhitelistFile)
        self.blacklist_tgids = self.load_tgid_file(self.defaultBlacklistFile)

        # Define Logger
        self.logFile = os.path.expanduser("/opt/op25-project/logs/app_log.txt")
        self.logger = CustomLogger(self.logFile)

        # Set environment variables correctly
        os.environ["PYTHONPATH"] = os.environ.get("PYTHONPATH", "") + ":/home/dnaab/op25/op25/gr-op25_repeater/apps/tx:/home/dnaab/op25/build"

        # Kill any existing OP25 processes before starting a new one
        subprocess.run(["pkill", "-f", "rx.py"])

        # Define the OP25 command with arguments
        self.op25_command = [
            self.rx_script , "--nocrypt", "--args", "rtl",
            "--gains", "lna:36", "-S", "960000", "-q", "0",
            "-v", "1", "-2", "-V", "-U",
            "-T", self.trunk_file,
            "-U", "-l", "5000"
        ]

        # Start OP25 process and redirect stderr to a file
        self.op25_process = subprocess.Popen(
            self.op25_command,
            stdout=subprocess.PIPE,
            stderr=open(self.stderr_file, "w"),
            text=True
        )

        time.sleep(14)
        if(self.isConnected()):
             self.logger.info("Connection Status", "OP25 Connected")

    def isConnected(self, timeout=30):
        """Continuously check for 'Reconfiguring NAC' in the log file until found or timeout."""
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
                self.logger.info(f"Sent {message}")

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

    # Usage: me.switchGroup(int(tgid))
    def switchGroup(self, grp):
        """Switches OP25 to a new talkgroup."""
        if not self.op25_process or self.op25_process.poll() is not None:
            print("[ERROR] OP25 is not running.")
            return

        try:
            if isinstance(grp, int):
                if grp not in self.whitelist_tgids:
                    self.whitelist([grp])  # Ensure it's whitelisted
                self.command("hold", grp)  # Actually switch the TGID
                print(f"Success! Talkgroup changed to {grp}.")
        except Exception as e:
            print(f"[ERROR] Failed to switch talkgroup: {e}")


    def command(self, cmd, data):
        """Sends a command to OP25. Ensures proper handling for hold, whitelist, and reload."""
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
                print(f"[SUCCESS] Hold command sent for TGID {data}.")
            else:
                print(f"[ERROR] Failed to hold TGID {data}. No response received.")

        elif cmd == "whitelist":
            response = self.send_udp_command(cmd, data)  # Directly send the command
            if response:
                print(f"[SUCCESS] Whitelisted TGID {data}.")
            else:
                print(f"[ERROR] Failed to whitelist TGID {data}. No response received.")

        # 🔹 Step 3: Handle reload command - Fully reload both whitelist & blacklist
        elif cmd == "reload":
            response = self.send_udp_command(cmd, 0)  # Reset OP25 state
            if response:
                print("[SUCCESS] OP25 reload command executed.")
                time.sleep(1)  # Ensure OP25 has time to process reload

                # 🔹 Step 3A: Reload the default whitelist and blacklist files
                self.whitelist_tgids = self.load_tgid_file(self.defaultWhitelistFile)
                self.blacklist_tgids = self.load_tgid_file(self.defaultBlacklistFile)
                print(f"[INFO] Reloaded whitelist ({len(self.whitelist_tgids)} TGIDs) and blacklist ({len(self.blacklist_tgids)} TGIDs).")

                # 🔹 Step 3B: Reapply stored whitelist TGIDs after reset
                if self.whitelist_tgids:
                    self.whitelist(self.whitelist_tgids)
            else:
                print("[ERROR] OP25 reload command failed. No response received.")

        # 🔹 Step 4: Handle all other commands and verify response
        else:
            response = self.send_udp_command(cmd, data)
            if response:
                print(f"[SUCCESS] Command '{cmd}' executed with data: {data}.")
            else:
                print(f"[ERROR] Command '{cmd}' failed. No response received.")

    def whitelist(self, values: list[int]):
        """Resets OP25 and applies a new whitelist of talkgroups."""
        if not values:
            print("[WARNING] No TGIDs provided for whitelisting.")
            return

        removed_from_blacklist = False
        for tgid in values:
            if tgid in self.blacklist_tgids:
                print(f"[INFO] Removing TGID {tgid} from blacklist before whitelisting.")
                self.blacklist_tgids.remove(tgid)
                removed_from_blacklist = True  # Track if we need to clear OP25 blacklist

        if removed_from_blacklist:
            self.command("lockout", 0)  # Clear OP25 blacklist in one call

        # Add TGIDs to the stored whitelist
        self.whitelist_tgids.extend([tgid for tgid in values if tgid not in self.whitelist_tgids])

        # Reset OP25 first to clear whitelist/blacklist
        self.send_udp_command("reload", 0)
        time.sleep(1)

        # Send each TGID to OP25 as a whitelist command
        for tgid in self.whitelist_tgids:
            self.send_udp_command("whitelist", tgid)
            time.sleep(0.2)

        print(f"[INFO] Applied whitelist for {len(self.whitelist_tgids)} TGIDs")

    def update_scan_list(self, new_tgids: List[int]):
        """Moves all whitelisted TGIDs to blacklist, then applies new whitelist. 
        Also ensures blacklisted TGIDs are removed before whitelisting.
        """
        if not new_tgids:
            print("[ERROR] No TGIDs provided for scan list update.")
            return

        # Check if the new scan list is the same as the current whitelist
        if set(new_tgids) == set(self.whitelist_tgids):
            print("[INFO] New scan list is identical to current list. No changes needed.")
            return

        # 🔹 Step 1: Capture the current whitelist and blacklist before modifying
        current_blacklist = set(self.blacklist_tgids)  # Snapshot of blacklisted TGIDs
        current_whitelist = set(self.whitelist_tgids)  # Snapshot of whitelisted TGIDs

        # 🔹 Step 2: Move all currently whitelisted TGIDs to the blacklist
        print(f"[INFO] Moving {len(current_whitelist)} TGIDs from whitelist to blacklist.")
        for tgid in current_whitelist:
            if tgid not in current_blacklist:  # Avoid redundant blacklisting
                self.command("lockout", tgid)  # API request to blacklist
                self.blacklist_tgids.append(tgid)  # Store in updated blacklist

        time.sleep(0.5)  # Allow OP25 time to process blacklist requests

        # 🔹 Step 3: Remove any new TGIDs that were previously blacklisted
        removed_from_blacklist = False
        tgids_to_whitelist = []
        
        for tgid in new_tgids:
            if tgid in current_blacklist:
                print(f"[INFO] Removing TGID {tgid} from blacklist before whitelisting.")
                self.blacklist_tgids.remove(tgid)  # Remove from locally stored blacklist
                removed_from_blacklist = True  # Track if we need to clear OP25 blacklist

            tgids_to_whitelist.append(tgid)  # Add to whitelist queue

        # 🔹 Step 4: Clear OP25's global blacklist if we removed any TGIDs
        if removed_from_blacklist:
            self.command("lockout", 0)  # Clear OP25 blacklist once

        # 🔹 Step 5: Now clear the stored whitelist (AFTER moving TGIDs to blacklist)
        self.whitelist_tgids.clear()

        # 🔹 Step 6: Reset OP25 to clear all internal lists
        response = self.command("reload", 0)  # Verify OP25 reload was successful
        if not response:
            print("[ERROR] OP25 reload command failed. Scan list update aborted.")
            return  # Stop execution if OP25 fails to reload

        time.sleep(1)  # Allow OP25 to reset before adding new TGIDs

        # 🔹 Step 7: Apply new whitelist
        if tgids_to_whitelist:
            print(f"[INFO] Adding {len(tgids_to_whitelist)} new TGIDs to whitelist.")
            self.whitelist(tgids_to_whitelist)  # This function already handles API requests

        # 🔹 Step 8: Store the new whitelist in `self.whitelist_tgids`
        self.whitelist_tgids = tgids_to_whitelist.copy()

        print("[INFO] Scan list update complete.")   

    def load_tgid_file(self, filepath):
        """Loads talkgroup IDs from a file, one per line."""
        tgids = []
        if os.path.exists(filepath):
            with open(filepath, "r") as file:
                for line in file:
                    try:
                        tgids.append(int(line.strip()))  # Convert each line to an integer
                    except ValueError:
                        print(f"[WARNING] Invalid TGID in {filepath}: {line.strip()}")  # Skip invalid lines
        else:
            print(f"[WARNING] Talkgroup file not found: {filepath}")
        return tgids

    def restart(self):
        print("[INFO] Restarting OP25...")
        self.stop()
        self.start()

# me = OP25Controller()
# tgid = input("# Talk Group: ")
# 