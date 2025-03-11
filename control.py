import subprocess
import os
import time

class OP25Controller:
    def __init__(self):
        self.op25_process = None
        self.OP25_Path = "/home/dnaab/op25/op25/gr-op25_repeater/apps/rx.py"
        print("OP25Controller - Version 1.3")

    def kill_rx_processes(self):
        """Kills all existing rx.py processes."""
        try:
            subprocess.run(["pkill", "-f", "rx.py"], check=True)
            print("[DEBUG] Killed all existing rx.py processes.")
        except subprocess.CalledProcessError:
            print("[DEBUG] No existing rx.py processes found.")

    def start_op25(self):
        """Starts OP25 process."""
        self.op25_process = subprocess.Popen(
            [
                "python3",
                self.OP25_Path,
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
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE  # Added for command input handling
        )

    def start(self):
        """Starts OP25 and handles failures by killing rx.py if necessary."""
        self.kill_rx_processes()  # Ensure no existing instances are running

        self.start_op25()
        time.sleep(2)  # Give OP25 time to initialize

        if self.op25_process.poll() is not None:  # Process failed immediately
            print("[ERROR] OP25 failed to start on the first attempt!")

            self.kill_rx_processes()  # Kill any partially started processes

            print("[INFO] Retrying OP25 startup...")
            self.start_op25()
            time.sleep(2)

            if self.op25_process.poll() is not None:
                print("[CRITICAL] OP25 failed to start after retry. Check logs!")
                self.op25_process = None
                return

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
            grp = int(grp)  # Ensure numeric input
            command = f"W {grp}\n"  # OP25 uses 'W' to change talkgroup
            print(f"[DEBUG] Sending command: {command.strip()}")
            self.op25_process.stdin.write(command.encode())
            self.op25_process.stdin.flush()
        except ValueError:
            print("[ERROR] Invalid input. Enter a numeric talkgroup.")

    def restart(self):
        """Restarts OP25."""
        print("[INFO] Restarting OP25...")
        self.stop()
        self.start()