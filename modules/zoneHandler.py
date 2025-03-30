import json
import os
import tempfile
from typing import List
import re

class ZoneFileHandler:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self._read_file()

    def _read_file(self):
        if not os.path.exists(self.file_path):
            return {"zones": []}
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def update(self, new_data):
        self.data = new_data
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=4)

    @property
    def zones(self):
        return [Zone(z, idx) for idx, z in enumerate(self.data.get("zones", []))]

    def toJSON(self):
        return json.dumps(self.data, indent=4)

class Channel:
    def __init__(self, channel_data, zone_index=None):
        self._data = channel_data
        self._whitelistFilePath = ""
        self._blacklistTGIDs = []
        self._blacklistFilePath = ""
        if zone_index is not None:
            self._data["zone_index"] = zone_index


    def toWhitelistTSV(self) -> str:
        """Writes the channel's TGIDs to a TSV whitelist file with no header.

        Returns:
            str: The file path of the whitelist TSV file, or None on error.
        """
        # If _whitelistFilePath doesn't exist, create it.
        

        try:
            with open(self.whitelistFilePath, "w", newline='') as tsvfile:
                for tgid in self.tgid:
                    tsvfile.write(f"{tgid}\n")
            return self.whitelistFilePath
        
        except Exception as e:
            print(f"Error writing TSV: {e}")
            return None
    
    @property
    def blacklistFilePath(self) -> str:
        """Returns the file path of the blacklist TGIDs. If it is unset, one is created and returned."""
        if not self._blacklistFilePath:
            safe_name = re.sub(r'\W+', '_', self.name)  # Replace non-alphanumeric characters with underscores
            self._blacklistFilePath = os.path.join(tempfile.gettempdir(), f"_blacklist_{safe_name}.tsv")
        return self._blacklistFilePath
    
    @property
    def blacklistTGIDs(self) -> list[int]:
        return self._blacklistTGIDs
    
    def addToBlacklist(self, tgid: int) -> bool:
        """Adds a TGID to the blacklist if it's not already present."""
        if tgid not in self._blacklistTGIDs:
            self._blacklistTGIDs.append(tgid)
            return True
        return False

    def removeFromBlacklist(self, tgid: int) -> bool:
        """Removes a TGID from the blacklist if it exists."""
        if tgid in self._blacklistTGIDs:
            self._blacklistTGIDs.remove(tgid)
            return True
        return False


    def toBlacklistTSV(self) -> str:
        """The blacklist is a list of TGIDS that OP25 uses to 'lock out' (block) from listening. """
        """This list is cleared when api.py is unloaded, but persists throughout the API system (but cleared when switching channels). """
        """Returns the blacklist file path of those TGIDs. if there is an exception."""
        
    
        try:
            with open(self.blacklistFilePath, "w", newline='') as tsvfile:
                for tgid in self.blacklistTGIDs:
                    tsvfile.write(f"{tgid}\n")
                    
                if(len(self.blacklistTGIDs)) == 0:
                    tsvfile.write(f"0\n")
            return self.blacklistFilePath
        
        except Exception as e:
            print(f"Error writing TSV: {e}")
            return None # Return nothing for now

    @property
    def whitelistFilePath(self) -> str:
        """Returns the sanitized temporary path used to create the whitelist file."""
        if not self._whitelistFilePath:
            safe_name = re.sub(r'\W+', '_', self.name)  # Replace non-alphanumeric characters with underscores
            self._whitelistFilePath = os.path.join(tempfile.gettempdir(), f"_whitelist_{safe_name}.tsv")
        return self._whitelistFilePath
    
    @property
    def channel_number(self)->int:
        return int(self._data.get("channel_number"))

    @property
    def name(self)->str:
        """Returns the name of the channel."""
        return self._data.get("name")

    @property
    def type(self)->str:
        """Returns the type of channel (either Scan or Talkgroup), which indicates multiple talkgroups or singular."""
        return self._data.get("type")

    @property
    def zone_index(self)->int:
        """Returns the index of the zone in the dictionary"""
        return int(self._data.get("zone_index"))

    @property
    def tgid(self) -> List[int]:
        """Returns an array of TGID numbers (e.g. [1234, 5678])"""
        return self._data.get("tgid", [])

    @property
    def sysid(self)->str:
        """Returns the sys id of the radio system (e.g. X026)"""
        return self._data.get("sysid")

    def to_dict(self):
        """Returns the channel as a dictionary."""
        return self._data

    def toJSON(self)->str:
        """Returns the channel as s JSON dump"""
        return json.dumps(self._data, indent=4)

class Zone:
    def __init__(self, zone_data, index):
        self._data = zone_data
        self._data["zone_index"] = index
        self.index = index

    @property
    def name(self):
        return self._data.get("name")

    @property
    def channels(self):
        return [Channel(ch, self.index) for ch in self._data.get("channels", [])]

    def nextChannel(self, current_number):
        ch_list = self.channels
        for i, ch in enumerate(ch_list):
            if ch.channel_number == current_number:
                return ch_list[(i + 1) % len(ch_list)]
        return ch_list[0] if ch_list else None

    def previousChannel(self, current_number):
        ch_list = self.channels
        for i, ch in enumerate(ch_list):
            if ch.channel_number == current_number:
                return ch_list[(i - 1) % len(ch_list)]
        return ch_list[-1] if ch_list else None

    def to_dict(self):
        return self._data

    def toJSON(self):
        return json.dumps(self._data, indent=4)

class ZoneData(ZoneFileHandler):
    def getZoneByIndex(self, index):
        try:
            return self.zones[index]
        except IndexError:
            return None

    def getZoneChannelsByIndex(self, index):
        zone = self.getZoneByIndex(index)
        if zone:
            return zone.channels
        return []

    def getChannelsBySysId(self, sysid):
        matched_channels = []
        for zone in self.zones:
            for ch in zone.channels:
                if ch.sysid == sysid:
                    matched_channels.append(ch)
        return matched_channels

    def getChannel(self, zone_index, channel_number) -> Channel:
        zone = self.getZoneByIndex(zone_index)
        if zone:
            for ch in zone.channels:
                if ch.channel_number == channel_number:
                    return ch
        return {}

    def nextZone(self, current_index) -> dict | None:
        zones = self.zones
        if not zones:
            return None  # Clear signal that nothing is available
        next_index = (current_index + 1) % len(zones)
        return zones[next_index].to_dict()

    def previousZone(self, current_index):
        zones = self.zones
        if not zones:
            return {}
        previous_index = (current_index - 1) % len(zones)
        return zones[previous_index].to_dict()

    def getNextChannel(self, zone_index, channel_number):
        zone = self.getZoneByIndex(zone_index)
        if not zone:
            return {}
        next_ch = zone.nextChannel(channel_number)
        return next_ch.to_dict() if next_ch else {}

    def getPreviousChannel(self, zone_index, channel_number):
        zone = self.getZoneByIndex(zone_index)
        if not zone:
            return {}
        prev_ch = zone.previousChannel(channel_number)
        return prev_ch.to_dict() if prev_ch else {}

    def toJSON(self):
        return json.dumps(self.data, indent=4)
