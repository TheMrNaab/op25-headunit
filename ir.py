import RPi.GPIO as GPIO
import time

class IRRemoteHandler:
    def __init__(self, receiver_pin):
        """Initialize IR remote handler and setup GPIO."""
        self.receiver_pin = receiver_pin
        self.setup_gpio()

    def setup_gpio(self):
        """Set up GPIO for the IR receiver."""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.receiver_pin, GPIO.IN)

    def listen(self):
        """Continuously listens for IR signals and prints the key pressed."""
        print("Listening for IR remote inputs...")
        try:
            while True:
                if GPIO.input(self.receiver_pin) == GPIO.LOW:
                    code = self.decode_signal()
                    if code:
                        print(f"Key Pressed: {code}")  # Print the key name
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nExiting...")
            self.cleanup()

    def decode_signal(self):
        """Placeholder for IR decoding logic. Simulates button presses."""
        # In actual implementation, replace this with IR decoding logic.
        # For now, return a simulated button name.
        return "KEY_UP"  # Simulated key press

    def cleanup(self):
        """Cleanup GPIO on exit."""
        GPIO.cleanup()
        print("GPIO cleaned up.")

# Run the script directly
# if __name__ == "__main__":
#     receiver_pin = 18  # Change to the correct GPIO pin
#     remote = IRRemoteHandler(receiver_pin)
#     remote.listen()