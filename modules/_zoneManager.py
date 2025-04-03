# _zoneManager.py
import json
import os
import tempfile
from typing import List, Optional
import re
import shutil

from typing import List, Optional

class zoneManager:
    """
    Manages zones and their associated channels by reading and writing to a JSON file.
    Provides methods to access, update, and navigate zones and channels.
    """
    def __init__(self, file_path: str):
        print("Init...")
        self.file_path = file_path
        self._zones = self._load_zones()
        
    def reload(self):
        self.append_line_to_file("zoneManager.reload()")
        self._zones = self._load_zones()
        self.append_line_to_file("zoneManager.reload() -> Done")
        
    def _load_zones(self) -> List["zoneMember"]:
        print("Load Zones...")
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Zone file not found: {self.file_path}")
            return []
        with open(self.file_path, 'r') as f:
            self._data = json.load(f)
            print(self._data)
        return [zoneMember(zone_data, idx) for idx, zone_data in enumerate(self._data.get("zones", {}).values())]

    def save(self):
        with open(self.file_path, 'w') as f:
            json.dump({"zones": [zone.to_dict() for zone in self._zones]}, f, indent=4)

    def update(self, data):
        # Create a backup if the file exists
        if os.path.exists(self.file_path):
            backup_path = self.file_path + '.bak'
            shutil.copy2(self.file_path, backup_path)

        # Write the updated data as-is
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=4)
            
        self._zones = self._load_zones()  # ✅ FIXED
    

    @property
    def zones(self) -> List["zoneMember"]:
        return self._zones

    def getZoneByIndex(self, index: int) -> Optional["zoneMember"]:
        return self._zones[index] if 0 <= index < len(self._zones) else None

    def getZoneByName(self, name: str) -> Optional["zoneMember"]:
        for zone in self._zones:
            if zone.name == name:
                return zone
        return None

    def getZoneChannelsByIndex(self, index: int) -> List["channelMember"]:
        zone = self.getZoneByIndex(index)
        return zone.channels if zone else []

    def getChannelsBySysId(self, sysid: str) -> List["channelMember"]:
        matched_channels = []
        for zone in self._zones:
            for ch in zone.channels:
                if ch.sysid == sysid:
                    matched_channels.append(ch)
        return matched_channels

    def getChannel(self, zone_index: int, channel_number: int) -> Optional["channelMember"]:
        zone = self.getZoneByIndex(zone_index)
        self.append_line_to_file(f"\n\nGetting Channel -> {channel_number}")
        self.append_line_to_file(f"Zone Index -> {zone_index}")
        self.append_line_to_file(f"Channel Number -> {channel_number}")
        self.append_line_to_file(f"Zone -> {zone}")
        if zone:
            channels = zone.channels
            if 0 <= channel_number < len(channels):
                self.append_line_to_file(f"Channel -> {channels[channel_number]}")
                return channels[channel_number]
        return None

    def getNextChannel(self, zone_index: int, channel_number: int) -> dict:
        self.append_line_to_file("zoneManager.get_next_channel()")
        self.append_line_to_file(f"Getting Next Channel -> {channel_number}")
        self.append_line_to_file(f"Zone Index -> {zone_index}")
        self.append_line_to_file("===")
        zone = self.getZoneByIndex(zone_index)
        if not zone:
            return {}
        next_ch = zone.next_channel(channel_number)
        return next_ch.to_dict() if next_ch else {}

    def getPreviousChannel(self, zone_index: int, channel_number: int) -> dict:
        zone = self.getZoneByIndex(zone_index)
        if not zone:
            return {}
        prev_ch = zone.previous_channel(channel_number)
        return prev_ch.to_dict() if prev_ch else {}

    def getNextZone(self, current_index: int) -> dict:
        if not self._zones:
            return {}
        next_index = (current_index + 1) % len(self._zones)
        return self._zones[next_index].to_dict()

    def getPreviousZone(self, current_index: int) -> dict:
        if not self._zones:
            return {}
        previous_index = (current_index - 1) % len(self._zones)
        return self._zones[previous_index].to_dict()

    def to_json(self) -> str:
        return json.dumps({"zones": [z.to_dict() for z in self._zones]}, indent=4)

    def append_line_to_file(self, line: str):
        with open("/opt/op25-project/logs/app_log.txt", 'a') as file:
            file.write(line + '\n')
class zoneMember:
    """
    Represents a zone containing multiple channels.
    Provides methods to navigate between channels and access channel data.
    """
    def __init__(self, zone_data: dict, index: int):
        self._data = zone_data
        self._data["zone_index"] = index
        self.index = index

    @property
    def name(self) -> str:
        """Returns the name of the zone."""
        return self._data.get("name")

    @property
    def channels(self) -> List["channelMember"]:
        """Returns the list of channels in the zone."""
        return [channelMember(ch, self.index) for ch in self._data.get("channels", [])]

    def next_channel(self, current_number: int) -> Optional["channelMember"]:
        """Gets the next channel in the zone."""
        ch_list = self.channels
        for i, ch in enumerate(ch_list):
            if ch.channel_number == current_number:
                return ch_list[(i + 1) % len(ch_list)]
        return ch_list[0] if ch_list else None

    def previous_channel(self, current_number: int) -> Optional["channelMember"]:
        """Gets the previous channel in the zone."""
        ch_list = self.channels
        for i, ch in enumerate(ch_list):
            if ch.channel_number == current_number:
                return ch_list[(i - 1) % len(ch_list)]
        return ch_list[-1] if ch_list else None

    def to_dict(self) -> dict:
        """Returns the zone as a dictionary."""
        return self._data

    def get_channel_by_index(self, channel_index: int) -> Optional["channelMember"]:
        """Retrieves a channel by its index within the zone."""
        channels = self.channels
        return channels[channel_index] if 0 <= channel_index < len(channels) else None

class channelMember:
    """
    Represents a channel within a zone.
    Manages whitelist and blacklist functionality and provides access to channel properties.
    """
    def __init__(self, channel_data: dict, zone_index: Optional[int] = None):
        self._data = channel_data
        if not isinstance(channel_data, dict):
            raise TypeError("channel_data must be a dict")
        self._whitelistFilePath = ""
        self._blacklistTGIDs = []
        self._blacklistFilePath = ""
        if zone_index is not None:
            self._data["zone_index"] = zone_index
            
    def append_line_to_file(self, line: str):
        with open("/opt/op25-project/logs/app_log.txt", 'a') as file:
            file.write(line + '\n')
    @property
    def channel_number(self) -> int:
        """Returns the channel number."""
        return int(self._data.get("channel_number"))

    @property
    def zoneIndex(self) -> int:
        """Returns the index of the zone this channel belongs to."""
        return self._data.get("zone_index")
    @property
    def name(self) -> str:
        """Returns the name of the channel."""
        return self._data.get("name")

    @property
    def type(self) -> str:
        """Returns the type of the channel (Scan or Talkgroup)."""
        return self._data.get("type")

    @property
    def tgid(self) -> List[int]:
        """Returns the list of TGIDs associated with the channel."""
        return self._data.get("tgid", [])

    @property
    def sysid(self) -> str:
        """Returns the system ID of the channel."""
        return self._data.get("sysid")

    @property
    def whitelistFilePath(self) -> str:
        """Returns the file path for the whitelist."""
        if not self._whitelistFilePath:
            safe_name = re.sub(r'\W+', '_', self.name)
            self._whitelistFilePath = os.path.join(tempfile.gettempdir(), f"_whitelist_{safe_name}.tsv")
        return self._whitelistFilePath

    @property
    def blacklistFilePath(self) -> str:
        """Returns the file path for the blacklist."""
        if not self._blacklistFilePath:
            safe_name = re.sub(r'\W+', '_', self.name)
            self._blacklistFilePath = os.path.join(tempfile.gettempdir(), f"_blacklist_{safe_name}.tsv")
        return self._blacklistFilePath

    def toWhitelistTSV(self) -> str:
        """Writes the TGIDs to a whitelist TSV file."""
        try:
            with open(self.whitelistFilePath, "w", newline='') as tsvfile:
                for tgid in self.tgid:
                    tsvfile.write(f"{tgid}\n")
            return self.whitelistFilePath
        except Exception as e:
            print(f"Error writing whitelist TSV: {e}")
            return None

    def toBlacklistTSV(self) -> str:
        """Writes the TGIDs to a blacklist TSV file."""
        try:
            with open(self.blacklistFilePath, "w", newline='') as tsvfile:
                for tgid in self._blacklistTGIDs:
                    tsvfile.write(f"{tgid}\n")
                if not self._blacklistTGIDs:
                    tsvfile.write("1234\n")  # Placeholder for empty blacklist
            return self.blacklistFilePath
        except Exception as e:
            print(f"Error writing blacklist TSV: {e}")
            return None

    def add_to_blacklist(self, tgid: int) -> bool:
        """Adds a TGID to the blacklist."""
        if tgid not in self._blacklistTGIDs:
            self._blacklistTGIDs.append(tgid)
            return True
        return False

    def remove_from_blacklist(self, tgid: int) -> bool:
        """Removes a TGID from the blacklist."""
        if tgid in self._blacklistTGIDs:
            self._blacklistTGIDs.remove(tgid)
            return True
        return False

    def to_dict(self) -> dict:
        """Returns the channel as a dictionary."""
        return self._data



# Ensure the Channel class is defined or imported correctly
class Channel:
    """Placeholder or actual implementation of the Channel class."""
    def __init__(self, data, zone_index):
        self.data = data
        self.zone_index = zone_index
        # Add necessary initialization logic

    @property
    def channel_number(self):
        # Return the channel number
        return self.data.get("channel_number", 0)

    @property
    def name(self):
        # Return the channel name
        return self.data.get("name", "")

    @property
    def sysid(self):
        # Return the system ID
        return self.data.get("sysid", 0)


# Ensure these classes are available for import
__all__ = ["Channel", "Zone", "ZoneData"]
