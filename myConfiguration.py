import os
import configparser
import sys

class MyConfig:
    def __init__(self, config_file="config.ini"):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    @property
    def defaultZonesFile(self):
        """Retrieve the default value for zones.json configuration."""
        return self.get("paths", "default_zones_file")

    def get(self, section, key, fallback=None):
        """Retrieve a value from the config file."""
        if self.config.has_section(section) and self.config.has_option(section, key):
            return self.config.get(section, key)
        return fallback  # Return fallback if section or key doesn't exist
    
    def get_path(self, section, key, expanded=True, fallback=None):
        return os.path.dirname(self.config.get(section, key, fallback=fallback)) if expanded else self.config.get(section, key, fallback=fallback)

    def get(self, section, key, fallback=None):
        """Retrieve a string value from the config file."""
        return self.config.get(section, key, fallback=fallback)

    def getint(self, section, key, fallback=0):
        """Retrieve an integer value from the config file."""
        return self.config.getint(section, key, fallback=fallback)

    def getboolean(self, section, key, fallback=False):
        """Retrieve a boolean value from the config file."""
        return self.config.getboolean(section, key, fallback=fallback)
    
    def build_command(self):
        """Construct the OP25 command based on the config.ini settings."""
        rx_script = self.get("paths", "rx_script")
        command = [
            rx_script,
            "--nocrypt" if self.getboolean("op25", "nocrypt") else "",
            "--args", self.get("op25", "args", "rtl"),
            "--gains", self.get("op25", "gains", "lna:40"),
            "-S", str(self.getint("op25", "sample_rate", 960000)),
            "-q", str(self.getint("op25", "frequency_correction", 0)),
            "-v", str(self.getint("op25", "verbosity", 1)),
            "-2" if self.getboolean("op25", "two_tuner_mode") else "",
            "-V" if self.getboolean("op25", "voice_logging") else "",
            "-U" if self.getboolean("op25", "udp_output") else "",
            "-T", f"{self.get("paths","rx_script")}",
            "-U",
            "-l", str(self.config.getint("op25", "udp_output_port", 5000))
        ]

        return command