import os
import subprocess
import time
class OP25Controller:
    def __init__(self):  # Fixed method name
        # Define OP25 executable path
        rx_script = os.path.expanduser("~/op25/op25/gr-op25_repeater/apps/rx.py")

        # Start OP25 in the background
        try:
            self.op25_process = subprocess.Popen(
                [
                    "python3", rx_script, "--args", "rtl=0", "-N", "LNA:35",
                    "-S", "2500000", "-q", "0", "-T", "trunk.tsv", "-V", "-2", "-U"
                ],
                cwd=os.path.dirname(rx_script),  # Ensure the script runs in the correct directory
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,  # Suppress stdout to avoid triggering gnuplot
                stderr=subprocess.DEVNULL,  # Suppress errors to prevent gnuplot launch
                text=True
            )

            time.sleep(5)  # Give OP25 time to initialize

        except Exception as e:
            print(f"Failed to start OP25: {e}")
            exit(1)

    def switchGroup(self, grp):
        """ Switches OP25 to a new talkgroup. """
        if self.op25_process.poll() is not None:
            print("Error: OP25 is not running.")
            return
        try:
            grp = int(grp)  # Ensure numeric input
            command = f"W {grp}\n"  # OP25 uses 'w' to change talkgroup
            print(command)
            self.op25_process.stdin.write(command)
            self.op25_process.stdin.flush()
        except ValueError:
            print("Invalid input. Enter a numeric talkgroup.")

    def start(self):
        # Check if the process is still running
        if self.op25_process.poll() is None:
            print("OP25 started successfully!")
        else:
            print("OP25 failed to start.")
            error_message = self.op25_process.stderr.read()
            print("Error Output:\n", error_message)
            self.op25_process.terminate()  # Ensure the process does not hang
            exit(1)

    def stop(self):
        if self.op25_process and self.op25_process.poll() is None:
            print("Stopping OP25...")
            self.op25_process.terminate()
            self.op25_process.wait()
            print("OP25 stopped successfully.")
        else:
            print("OP25 is not running.")

    def restart(self):
        print("Restarting OP25...")
        self.stop()
        self.start()


