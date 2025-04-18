import json
import os
import configparser
import sys
class FileObject:
    def __init__(self, file_path=None):
        sys.stdout = open("/opt/op25-project/logs/stdout_main.txt", "a")
        sys.stderr = open("/opt/op25-project/logs/stderr_main.txt", "a")
        if file_path is None:
            self.file_path = self.beta_file_path()
        else:
            self.file_path = file_path

        self.data = self.load_file()

        # Store zone and talkgroup state
        self.current_zone_index = 0
        self.current_tg_index = 0

        # Extract zone names after loading data
        self.zone_names = list(self.data["zones"].keys()) if "zones" in self.data else []
            
    def beta_file_path(self):
        """Returns the path for the beta JSON file."""

        script_dir = os.path.dirname(os.path.abspath(__file__))  # Get main.py's directory
        file_path = os.path.join(script_dir, "system.json")  # Ensure correct path

        return file_path

    def load_file(self):
        """Loads the JSON file."""
        print(f"Loading JSON from: {self.file_path}")
        try:
            with open(self.file_path, "r") as file:
                data = json.load(file)
            
            print(self.file_path)

            # Convert JSON into zone-based structure
            zones = {}
            for entry in data:
                zone_name = entry["zone"]
                if zone_name not in zones:
                    zones[zone_name] = {"channels": []}
                zones[zone_name]["channels"].append(entry)

            return {"zones": zones}  # Store zones properly
        except FileNotFoundError:
            return {"zones": {}}  # Ensure empty zones structure

    def save_json(self):
        """Saves the current JSON data to the file."""
        with open(self.filename, "w") as f:
            json.dump(self.data, f, indent=4)

    def get_channel_by_number(self, channel_number):
        """Finds a channel by its number."""
        for zone_name, zone_data in self.data["zones"].items():
            for channel in zone_data["channels"]:
                if channel["channel_number"] == channel_number:
                    return channel
        return None

    def get_channels_by_zone(self, zone_name):
        """Returns all channels within a given zone."""
        return self.data["zones"].get(zone_name, {}).get("channels", [])

    def get_channel_type(self, channel_number):
        """Returns the type ('talkgroup' or 'scan') of a given channel number."""
        channel = self.get_channel_by_number(channel_number)
        return channel.get("type", "unknown") if channel else None

    def get_next_channel_number(self):
        """Finds the next available channel number across all zones."""
        max_number = 0
        for zone_data in self.data["zones"].values():
            for channel in zone_data["channels"]:
                max_number = max(max_number, channel["channel_number"])
        return max_number + 1

    def get_channel_by_tgid(self, tgid):
        """Finds a channel by its Talkgroup ID (TGID)."""
        for zone_name, zone_data in self.data["zones"].items():
            for channel in zone_data["channels"]:
                if channel["type"] == "talkgroup" and channel["tgid"] == tgid:
                    return {"zone": zone_name, "channel": channel["name"]}
                elif channel["type"] == "scan" and tgid in channel["tgids"]:
                    return {"zone": zone_name, "channel": channel["name"]}
        return None

    def get_previous_channel(self, current_channel_number):
        """Finds the previous channel based on the channel number."""
        previous_channel = None
        for zone_data in self.data["zones"].values():
            for channel in zone_data["channels"]:
                if channel["channel_number"] < current_channel_number:
                    if previous_channel is None or channel["channel_number"] > previous_channel["channel_number"]:
                        previous_channel = channel
        return previous_channel

    def add_channel(self, zone_name, name, channel_type, tgids):
        """Adds a new channel to a zone, creating the zone if it doesn't exist."""
        new_channel = {
            "channel_number": self.get_next_channel_number(),
            "name": name,
            "type": channel_type
        }
        if channel_type == "talkgroup":
            new_channel["tgid"] = tgids
        elif channel_type == "scan":
            new_channel["tgids"] = tgids

        if zone_name in self.data["zones"]:
            self.data["zones"][zone_name]["channels"].append(new_channel)
        else:
            self.data["zones"][zone_name] = {"channels": [new_channel]}

        self.save_json()
        return new_channel

    def remove_channel(self, channel_number):
        """Removes a channel by its number."""
        for zone_name, zone_data in self.data["zones"].items():
            for channel in zone_data["channels"]:
                if channel["channel_number"] == channel_number:
                    zone_data["channels"].remove(channel)
                    self.save_json()
                    return True
        return False
    
    def get_zone(self, index):
        """Finds the zone by index"""
        if not self.zone_names:
            return None  # No zones exist
        return self.zone_names[(index) % len(self.zone_names)]
    
    def get_next_zone(self, current_zone_index):
        """Finds the next zone, looping back if at the last one."""
        print(f"Current_Zone_Index: {current_zone_index}")
        if not self.zone_names:
            return None  # No zones exist
        return self.zone_names[(current_zone_index + 1) % len(self.zone_names)]

    def get_previous_zone(self, current_zone_index):
        """Finds the previous zone, looping to the last one if at the first."""
        if not self.zone_names:
            return None  # No zones exist
        return self.zone_names[(current_zone_index - 1) % len(self.zone_names)]
    
    def get_first_channel_in_zone(self, zone_index):
        if not self.zone_names:
            return None
        zone_name = self.zone_names[zone_index % len(self.zone_names)]
        channels = self.get_channels_by_zone(zone_name)
        return channels[0] if channels else None
    
class MyConfig:
    def __init__(self, config_file="config.ini"):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

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