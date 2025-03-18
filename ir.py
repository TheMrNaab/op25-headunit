import subprocess
import time
import re

class IRRemoteHandler:
    def __init__(self):
        print("[INFO] IR Remote Handler initialized.")

    def listen(self):
        """Continuously listens for IR scancodes and prints them."""
        print("[INFO] Listening for IR remote inputs...")

        try:
            process = subprocess.Popen(
                ["ir-keytable", "-t"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Force line buffering
            )

            while True:
                output, _ = process.communicate(timeout=5)  # Wait for output with timeout
                if output:
                    print(f"[DEBUG] Raw Output: {output.strip()}")  # Print raw output

                    scancode = self.extract_scancode(output)
                    if scancode:
                        print(f"[INFO] IR Scancode Received: {scancode}")
                        self.handle_ir_input(scancode)  # Process scancode

                time.sleep(0.1)  # Prevent CPU overuse

        except subprocess.TimeoutExpired:
            print("[WARNING] No IR signal received within timeout, continuing...")
        except KeyboardInterrupt:
            print("\n[INFO] Exiting...")
            process.terminate()

    def extract_scancode(self, line):
        """Extracts the scancode from ir-keytable output using regex."""
        match = re.search(r"scancode = (0x[0-9a-fA-F]+)", line)
        return match.group(1) if match else None

    def handle_ir_input(self, scancode):
        """Processes the received scancode and maps it dynamically."""
        scancode_map = {
            "0x19": "KEY_POWER",
            "0x45": "KEY_UP",
            "0x46": "KEY_DOWN",
            "0x47": "KEY_LEFT",
            "0x44": "KEY_RIGHT",
            "0x40": "KEY_ENTER",
            "0x43": "KEY_BACK"
        }
        if scancode in scancode_map:
            print(f"[INFO] Mapped Key Pressed: {scancode_map[scancode]}")
        else:
            print(f"[INFO] Unmapped Scancode: {scancode}")

# Run the script
# if __name__ == "__main__":
#     remote = IRRemoteHandler()
#     remote.listen()