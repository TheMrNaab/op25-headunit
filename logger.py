import os
import datetime

class CustomLogger:
    def __init__(self, log_file):
        self.log_file = log_file
        # Create log file if it does not exist
        if not os.path.exists(log_file):
            with open(log_file, "w") as f:
                f.write("=== Log File Created ===\n")

    def log(self, level, message):
        """Write log messages to the log file."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level.upper()}] {message}\n"

        with open(self.log_file, "a") as f:
            f.write(log_message)

        print(log_message.strip())  # Optional: Print logs to console

    def info(self, title, message=""):
        self.log("INFO", f"{title}: {message}")

    def warning(self, message):
        self.log("WARNING", message)

    def error(self, message):
        self.log("ERROR", message)