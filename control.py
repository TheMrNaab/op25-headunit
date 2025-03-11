import subprocess
import os
import time

class OP25Controller:
    def __init__(self):
        self.op25_process = None

    def start(self):
        """Starts OP25 with the correct parameters."""
        self.op25_process = subprocess.Popen(
            [
                "python3",
                "/opt/op25-project/rx.py",
                "--args", "rtl",
                "-N", "LNA:47",
                "-S", "250000",
                "-f", "853.6375e6",
                "-o", "25000",
                "-q", "0",
                "-T", "/opt/op25-project/trunk.tsv",
                "-V", "-2"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        time.sleep(2)  # Give OP25 time to initialize

        if self.op25_process.poll() is not None:  # Process failed
            print("[ERROR] OP25 failed to start!")

        if self.op25_process:
            print("[DEBUG] OP25 started successfully!")

    def stop(self):
        """Stops the OP25 process if running."""
        if self.op25_process and self.op25_process.poll() is None:
            self.op25_process.terminate()
            self.op25_process.wait()
            print("[DEBUG] OP25 process terminated.")

    def switchGroup(self, grp):
        """ Switches OP25 to a new talkgroup. """
        if self.op25_process.poll() is not None:
            print("[ERROR] OP25 is not running.")
            return
        try:
            grp = int(grp)  # Ensure numeric input
            command = f"W {grp}\n"  # OP25 uses 'W' to change talkgroup
            print(f"[DEBUG] Sending command: {command.strip()}")
            self.op25_process.stdin.write(command.encode())
            self.op25_process.stdin.flush()
        except ValueError:
            print("[ERROR] Invalid input. Enter a numeric talkgroup.")

    def restart(self):
        print("[INFO] Restarting OP25...")
        self.stop()
        self.start()