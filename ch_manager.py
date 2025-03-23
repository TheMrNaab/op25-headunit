import json
import os
import configparser
import sys

class ChannelManager:
    def __init__(self, file_path):
        """Initialize with the path to the JSON file."""
        self.file_path = file_path
        self.data = self._load_file()
    def _load_file(self):
        """Loads the JSON file and returns data."""
        try:
            with open(self.file_path, "r") as file:
                data = json.load(file)
                
            if "zones" not in data:
                return {"zones": []}
            return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {"zones": []}

    def _get_sorted_channels(self, inZone, number):
        """
        Returns a sorted list of channels, either within the same zone or across all zones.
        Each channel in the returned list includes the 'zone' (zone name) and 'zone_index'.
        """
        data = self._load_file()
        if not data or "zones" not in data:
            return []
        all_channels = []
        target_zone = None
        for i, zone in enumerate(data["zones"]):
            for channel in zone.get("channels", []):
                # Create a copy so as not to mutate the original JSON data
                channel_with_zone = channel.copy()
                channel_with_zone["zone"] = zone["name"]
                channel_with_zone["zone_index"] = i
                all_channels.append(channel_with_zone)
                if channel["channel_number"] == number:
                    target_zone = zone["name"]
        all_channels.sort(key=lambda x: x["channel_number"])
        if inZone and target_zone:
            return [ch for ch in all_channels if ch["zone"] == target_zone]
        return all_channels

    def nextChannel(self, zone_number, channel_number):
        """
        Finds the next channel within the specified zone relative to the provided channel number.
        If the given channel is the last in the zone, returns the first channel in that zone.
        The returned channel includes 'zone' and 'zone_index'.
        """
        data = self._load_file()
        if "zones" not in data or zone_number < 0 or zone_number >= len(data["zones"]):
            return None

        zone = data["zones"][zone_number]
        channels = zone.get("channels", [])
        if not channels:
            return None

        # Sort channels by channel_number within the zone
        channels = sorted(channels, key=lambda ch: ch["channel_number"])

        # Recursively find the index of the channel with the given channel_number
        def find_index(idx):
            if idx >= len(channels):
                return None
            if channels[idx]["channel_number"] == channel_number:
                return idx
            return find_index(idx + 1)

        index = find_index(0)
        if index is None:
            # If the channel is not found, default to the first channel in the zone.
            result = channels[0].copy()
        else:
            next_index = index + 1
            if next_index >= len(channels):
                next_index = 0  # Wrap-around to the first channel
            result = channels[next_index].copy()

        # Add zone information to the returned channel
        result["zone"] = zone["name"]
        result["zone_index"] = zone_number
        return result

    def previousChannel(self, zone_number, channel_number):
        """
        Finds the previous channel within the specified zone relative to the provided channel number.
        If the given channel is the first in the zone, returns the last channel in that zone.
        The returned channel includes 'zone' and 'zone_index'.
        """
        data = self._load_file()
        if "zones" not in data or zone_number < 0 or zone_number >= len(data["zones"]):
            return None

        zone = data["zones"][zone_number]
        channels = zone.get("channels", [])
        if not channels:
            return None

        # Sort channels by channel_number within the zone
        channels = sorted(channels, key=lambda ch: ch["channel_number"])

        # Recursively find the index of the channel with the given channel_number
        def find_index(idx):
            if idx >= len(channels):
                return None
            if channels[idx]["channel_number"] == channel_number:
                return idx
            return find_index(idx + 1)

        index = find_index(0)
        if index is None:
            # If not found, default to the last channel in the zone.
            result = channels[-1].copy()
        else:
            previous_index = index - 1
            if previous_index < 0:
                previous_index = len(channels) - 1  # Wrap-around to the last channel
            result = channels[previous_index].copy()

        # Add zone information to the returned channel
        result["zone"] = zone["name"]
        result["zone_index"] = zone_number
        return result

    def getChannelByNumber(self, channel_number):
        """
        Finds and returns a channel by its number.
        The returned channel JSON includes the 'zone' and 'zone_index'.
        """
        channels = self._get_sorted_channels(False, channel_number)
        for channel in channels:
            if channel["channel_number"] == channel_number:
                return channel
        return None

    def getChannelByName(self, name):
        """
        Finds and returns a channel by its name (case-insensitive).
        The returned channel JSON includes the 'zone' and 'zone_index'.
        """
        channels = self._get_sorted_channels(False, None)
        for channel in channels:
            if channel["name"].lower() == name.lower():
                return channel
        return None

    def getZoneByIndex(self, index):
        """
        Returns the zone at the specified index.
        The returned zone JSON includes the 'zone_index'.
        """
        data = self._load_file()
        if not data or "zones" not in data or index >= len(data["zones"]):
            return None
        zone = data["zones"][index].copy()
        zone["zone_index"] = index
        return zone

    def getZoneByName(self, name):
        """
        Finds and returns a zone by its name (case-insensitive).
        The returned zone JSON includes the 'zone_index'.
        """
        data = self._load_file()
        if not data or "zones" not in data:
            return None
        for i, zone in enumerate(data["zones"]):
            if zone["name"].lower() == name.lower():
                zone_with_index = zone.copy()
                zone_with_index["zone_index"] = i
                return zone_with_index
        return None

    # Get a channel by its number within a specific zone
    def getChannel(self, zone_number, channel_number):
        """
        Get a channel by its number within a specific zone.
        The returned channel JSON includes the 'zone' and 'zone_index'.
        Returns None if the zone or channel is not found.
        """
        data = self._load_file()
        zone = self.getZoneByIndex(zone_number)
        if not data or "zones" not in data or zone_number < 0 or zone_number >= len(data["zones"]):
            return None
        
        for channel in zone.get("channels", []):
            if channel["channel_number"] == channel_number:
                channel_with_zone = channel.copy()
                channel_with_zone["zone"] = zone["name"]
                channel_with_zone["zone_index"] = zone_number
                return channel_with_zone


    def nextZone(self, index):
        """
        Returns the next zone relative to the specified index.
        Loops back to the first zone if the index is at the last zone.
        The returned zone JSON includes the 'zone_index'.
        """
        data = self._load_file()
        if not data or "zones" not in data:
            return None
        return self.getZoneByIndex((index + 1) % len(data["zones"]))

    def previousZone(self, index):
        """
        Returns the previous zone relative to the specified index.
        Loops back to the last zone if the index is at the first zone.
        The returned zone JSON includes the 'zone_index'.
        """
        data = self._load_file()
        if not data or "zones" not in data:
            return None
        return self.getZoneByIndex((index - 1) % len(data["zones"]))

    def getAllZones(self):
        """
        Returns all zones in the JSON file.
        Each zone JSON includes the 'zone_index'.
        """
        _zones = self._load_file()
        if not _zones or "zones" not in _zones:
            return {"zones": []}
        return _zones

    def firstZone(self):
        """
        Returns the first available zone along with its 'zone_index'.
        """
        return self.getZoneByIndex(0)

    def firstZoneChannel(self, zone_index):
        """
        Returns the first channel in the specified zone.
        The returned channel JSON includes 'zone' and 'zone_index'.
        If the zone has no channels, returns None.
        """
        zone = self.getZoneByIndex(zone_index)
        if not zone or "channels" not in zone or not zone["channels"]:
            return None
        first_channel = zone["channels"][0].copy()
        first_channel["zone"] = zone["name"]
        first_channel["zone_index"] = zone_index
        return first_channel
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