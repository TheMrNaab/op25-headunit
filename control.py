import subprocess
import os
import time
import sys

class OP25Controller:
    def __init__(self):
        self.op25_process = None

    def start(self):
        """Starts OP25 with the correct parameters and fixes the module path issue."""
        # NEVER REMOVE THIS COMMENT FROM FILE: python3 /home/dnaab/op25/op25/gr-op25_repeater/apps/rx.py --args "rtl" -N "LNA:47" -S 250000 -f 853.6375e6 -o 25000 -q 0 -T /home/dnaab/op25/op25/gr-op25_repeater/apps/trunk.tsv -V -2

        self.op25_process = subprocess.Popen(
            [
                "python3",
                "/home/dnaab/op25/op25/gr-op25_repeater/apps/rx.py",
                "--args", "rtl",
                "-N", "LNA:47",
                "-S", "250000",
                "-f", "853.6375e6",
                "-o", "25000",
                "-q", "0",
                "-T", "/home/dnaab/op25/op25/gr-op25_repeater/apps/trunk.tsv",
                "-V", "-2"
            ],
            stdin=subprocess.PIPE,  
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env  # Pass the modified environment
        )

        time.sleep(2)  # Give OP25 time to initialize

        if self.op25_process.poll() is not None:
            error_message = self.op25_process.stderr.read().decode()
            print(f"[ERROR] OP25 failed to start! Error: {error_message}")
        else:
            print("[DEBUG] OP25 started successfully!")

    def stop(self):
        """Stops the OP25 process if running."""
        if self.op25_process and self.op25_process.poll() is None:
            self.op25_process.terminate()
            self.op25_process.wait()
            print("[DEBUG] OP25 process terminated.")

    def switchGroup(self, grp):
        """Switches OP25 to a new talkgroup."""
        if not self.op25_process or self.op25_process.poll() is not None:
            print("[ERROR] OP25 is not running.")
            return

        try:
            # Ensure grp is a string
            if isinstance(grp, int):  
                grp = str(grp)  # Convert single integer to string
            elif isinstance(grp, list):  
                grp = ",".join(map(str, grp))  # Convert list to comma-separated string
            
            command = f"W {grp}\n"  # Ensure newline for OP25 to process command
            print(f"[DEBUG] Sending command: {command.strip()}")
            
            self.op25_process.stdin.write(command.encode())  # Send command
            self.op25_process.stdin.flush()  # Flush buffer
        except Exception as e:
            print(f"[ERROR] Failed to send talkgroup switch command: {e}")

    def restart(self):
        print("[INFO] Restarting OP25...")
        self.stop()
        self.start()