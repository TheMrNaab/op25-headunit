import json
import os

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
        return [Zone(z) for z in self.data.get("zones", [])]

    def toJSON(self):
        return json.dumps(self.data, indent=4)

class Channel:
    def __init__(self, channel_data):
        self._data = channel_data

    @property
    def channel_number(self):
        return self._data.get("channel_number")

    @property
    def name(self):
        return self._data.get("name")

    @property
    def type(self):
        return self._data.get("type")
    
    @property
    def zone_id(self):
        return self._data.get("zone_id")

    @property
    def tgid(self):
        return self._data.get("tgid", [])

    @property
    def sysid(self):
        return self._data.get("sysid")

    def to_dict(self):
        return self._data

    def toJSON(self):
        return json.dumps(self._data, indent=4)

class Zone:
    def __init__(self, zone_data):
        self._data = zone_data

    @property
    def name(self):
        return self._data.get("name")

    @property
    def channels(self):
        return [Channel(ch) for ch in self._data.get("channels", [])]

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

    def getZoneChannelsByIndex(self, index):                      # APPENDS ZONE_INDEX
        zone:Zone = self.getZoneByIndex(index)
        
        for channel in zone.channels:
            self.appendZoneIndex(channel, index)
        
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

    def getChannel(self, zone_index, channel_number):
        zone = self.getZoneByIndex(zone_index)
        if zone:
            for ch in zone.channels:
                if ch.channel_number == channel_number:            # APPENDS ZONE_INDEX
                    self.appendZoneIndex(ch, zone_index)
                    return ch.to_dict()
        return {}

    def nextZone(self, current_index):                             
        zones = self.zones
        if not zones:
            return {}
        next_index = (current_index + 1) % len(zones)
        return zones[next_index].to_dict()

    def previousZone(self, current_index):
        zones = self.zones
        if not zones:
            return {}
        previous_index = (current_index - 1) % len(zones)
        return zones[previous_index].to_dict()

    def getNextChannel(self, zone_index, channel_number):          # APPENDS ZONE_INDEX
        zone = self.getZoneByIndex(zone_index)
        if not zone:
            return {}
        next_ch = zone.nextChannel(channel_number)
        self.appendZoneIndex(next_ch, zone_index)
        return next_ch.to_dict() if next_ch else {}
    
    def getPreviousChannel(self, zone_index, channel_number):      # APPENDS ZONE_INDEX
        zone = self.getZoneByIndex(zone_index)
        if not zone:
            return {}
        prev_ch = zone.previousChannel(channel_number)
        self.appendZoneIndex(prev_ch, zone_index)
        return prev_ch.to_dict() if prev_ch else {}

    def appendZoneIndex(self, channel, zone_index):
        if channel and not hasattr(channel, "zone_id"):
            channel.zone_id = zone_index
    
    def toJSON(self):
        return json.dumps(self.data, indent=4)
    