import subprocess
import os
import time

class OP25Controller:
    def __init__(self):
        self.op25_process = None

    def kill_rx_processes(self):
        """Kills all existing rx.py processes."""
        try:
            subprocess.run(["pkill", "-f", "rx.py"], check=True)
            print("[DEBUG] Killed all existing rx.py processes.")
        except subprocess.CalledProcessError:
            print("[DEBUG] No existing rx.py processes found.")

    def start(self):
        """Starts OP25 and handles failures by killing rx.py if necessary."""
        self.kill_rx_processes()  # Ensure no existing instances are running

        self.op25_process = subprocess.Popen(
            ["python3", "/opt/op25-project/rx.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        time.sleep(2)  # Give OP25 time to initialize

        if self.op25_process.poll() is not None:  # Process failed immediately
            print("[ERROR] OP25 failed to start on the first attempt!")

            # Kill rx.py again in case it partially started
            self.kill_rx_processes()

            print("[INFO] Retrying OP25 startup...")
            self.op25_process = subprocess.Popen(
                ["python3", "/opt/op25-project/rx.py"], 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            time.sleep(2)  # Wait for second attempt

            if self.op25_process.poll() is not None:
                print("[CRITICAL] OP25 failed to start after retry. Check logs!")
                self.op25_process = None  # Prevent further execution
                return

        if self.op25_process and self.op25_process.poll() is None:
            print("[DEBUG] OP25 started successfully!")
        else:
            print("[ERROR] OP25 is not running. Exiting process.")
            self.op25_process = None  # Ensure it does not get marked as running

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