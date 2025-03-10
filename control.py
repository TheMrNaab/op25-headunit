import subprocess
import os
import time

class OP25Controller:
    def __init__(self):
        # Define OP25 executable path
        self.rx_script = os.path.expanduser("~/op25/op25/gr-op25_repeater/apps/rx.py")
        self.op25_process = None  # Initialize the process variable
        print("[DEBUG] OP25Controller initialized")

    def start(self):
        if self.op25_process and self.op25_process.poll() is None:
            print("[DEBUG] OP25 is already running.")
            return

        try:
            print("[DEBUG] Starting OP25 process")
            self.op25_process = subprocess.Popen(
                [
                    "python3", self.rx_script, "--args", "rtl=0", "-N", "LNA:35",
                    "-S", "2500000", "-q", "0", "-T", "trunk.tsv", "-2", "-U"
                ],
                cwd=os.path.dirname(self.rx_script),  # Ensure the script runs in the correct directory
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,  # Ignore stdout to avoid blocking audio
                stderr=subprocess.DEVNULL,  # Capture errors
                text=True
            )

            time.sleep(5)  # Give OP25 time to initialize
            print("[DEBUG] OP25 started successfully!")

        except Exception as e:
            print(f"[ERROR] Failed to start OP25: {e}")
            exit(1)

    def switchGroup(self, grp):
        """ Switches OP25 to a new talkgroup. """
        if not self.op25_process or self.op25_process.poll() is not None:
            print("[ERROR] OP25 is not running.")
            return
        try:
            grp = int(grp)  # Ensure numeric input
            command = f"w {grp}\n"  # OP25 uses 'w' to change talkgroup
            self.op25_process.stdin.write(command)
            self.op25_process.stdin.flush()
            print(f"[DEBUG] Switched to talkgroup {grp}")
        except ValueError:
            print("[ERROR] Invalid input. Enter a numeric talkgroup.")

    def stop(self):
        if self.op25_process and self.op25_process.poll() is None:
            print("[DEBUG] Stopping OP25...")
            self.op25_process.terminate()
            self.op25_process.wait()
            print("[DEBUG] OP25 stopped successfully.")
        else:
            print("[DEBUG] OP25 is not running.")

    def restart(self):
        print("[DEBUG] Restarting OP25...")
        self.stop()
        self.start()

# TEST CODE
# op = OP25Controller()
# op.start()
# op.switchGroup(46800)
# op.stop()
