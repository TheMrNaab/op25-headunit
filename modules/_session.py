#_session.py

from modules._zoneManager import channelMember, zoneMember  # Updated import for channelMember
from modules._systemsManager import systemsMember
from typing import List, TYPE_CHECKING
from modules._talkgroupSet import TalkgroupSet

if TYPE_CHECKING:
    from modules._sessionManager import SessionManager

class SessionMember:
    def __init__(self, session_mgr: "SessionManager", system_index: int, zone_index: int, channel_index: int):
        self._session_manager = session_mgr  # must be first

        self._activeTGIDList = self._get_tgid_list(system_index)
        self.append_line_to_file(f"SessionMember initialized: system_index={system_index}, zone_index={zone_index}, channel_index={channel_index}")

        self._activeChannelNumber = channel_index
        self._activeZoneIndex = zone_index
        self._activeSysIndex = system_index

        self._activeSystem = self._get_system(self.activeSysIndex)
        self._activeZone = self._get_zone(self._activeZoneIndex)
        self._active_channel = self._get_channel(self.activeZoneIndex, self.activeChannelNumber)

    def append_line_to_file(self, line: str):
        with open("/opt/op25-project/logs/app_log.txt", 'a') as file:
            file.write(line + '\n')

    def _get_channel(self, zone_index: int, channel_number: int) -> channelMember:
        """Retrieve a channel object by zone index and channel number."""
        channel = self.sessionManager.zoneManager.getChannel(zone_index, channel_number)
        if not isinstance(channel, channelMember):  # Updated type check
            self._log_debug(f"Invalid Channel object: {type(channel)}")
            raise AttributeError("Invalid Channel object during initialization")
        return channel

    def _get_zone(self, zone_index: int) -> zoneMember:
        """Retrieve a zone object by index."""
        return self.sessionManager.zoneManager.getZoneByIndex(zone_index)

    def _get_system(self, system_index: int) -> systemsMember:
        """Retrieve a system object by index."""
        return self.sessionManager.systemsManager.getSystemByIndex(system_index)

    def _get_tgid_list(self, system_index: int) -> TalkgroupSet:
        """Retrieve a talkgroup set by system index."""
        return self.sessionManager.talkgroupsManager.getTalkgroupSetBySysIndex(system_index)

    @property
    def activeSysIndex(self) -> int:
        return self._activeSysIndex

    @property
    def sessionManager(self) -> "SessionManager":
        return self._session_manager

    @property
    def activeChannelNumber(self) -> int:
        return self._activeChannelNumber

    @property
    def activeZoneIndex(self) -> int:
        return self._activeZoneIndex

    @property
    def activeChannel(self) -> channelMember:  # Updated return type
        return self._active_channel

    @property
    def activeZone(self) -> zoneMember:
        return self._activeZone

    @property
    def activeSystem(self) -> systemsMember:
        return self._activeSystem

    @property
    def activeTGIDList(self) -> TalkgroupSet:
        return self._activeTGIDList

    def update_session(self, channel: channelMember, zone: zoneMember, system: systemsMember):
        """Update session state and trigger necessary changes."""
        did_system_change = system.index != self._activeSysIndex

        # Log debug information
        self._log_debug(f"Updating session: Channel={channel.channel_number}, Zone={zone.index}, System={system.index}")
        self._log_debug(f"Did system change: {did_system_change}")

        # Update session state
        self._activeChannelNumber = channel.channel_number
        self._active_channel = channel
        self._activeZoneIndex = zone.index
        self._activeZone = zone
        self._activeSysIndex = system.index
        self._activeSystem = system
        self._activeTGIDList = self._get_tgid_list(system.index)

        # Trigger talkgroup or system change
        self._change_talkgroup(did_system_change)

    def _change_talkgroup(self, did_system_change: bool):
        """Handle talkgroup or system change."""
        if did_system_change:
            self.sessionManager.op25Manager.switchSystem(self)
        else:
            self.sessionManager.op25Manager.switchTalkgroup(self)

    def nextChannel(self):
        """Switch to the next channel in the current zone."""
        next_channel_data = self.sessionManager.zoneManager.getNextChannel(self._activeZoneIndex, self._activeChannelNumber)
        if not next_channel_data:
            return {"error": "No next channel found"}, 404

        zone = self._get_zone(self._activeZoneIndex)
        channel = channelMember(next_channel_data, zone.index)  # Updated instantiation
        system = self._get_system(channel.sysid)

        self.update_session(channel, zone, system)
        return self._format_session_response(channel, zone, system)

    def previousChannel(self):
        """Switch to the previous channel in the current zone."""
        prev_channel_data = self.sessionManager.zoneManager.getPreviousChannel(self._activeZoneIndex, self._activeChannelNumber)
        if not prev_channel_data:
            return {"error": "No previous channel found"}, 404

        zone = self._get_zone(self._activeZoneIndex)
        channel = channelMember(prev_channel_data, zone.index)  # Updated instantiation
        system = self._get_system(channel.sysid)

        self.update_session(channel, zone, system)
        return self._format_session_response(channel, zone, system)

    def nextZone(self):
        """Switch to the next zone."""
        next_zone_data = self.sessionManager.zoneManager.getNextZone(self._activeZoneIndex)
        if not next_zone_data:
            return {"error": "No next zone found"}, 404

        zone = zoneMember(next_zone_data, next_zone_data.get("zone_index"))
        channel = zone.channels[0]
        system = self._get_system(channel.sysid)

        self.update_session(channel, zone, system)
        return self._format_session_response(channel, zone, system)

    def previousZone(self):
        """Switch to the previous zone."""
        prev_zone_data = self.sessionManager.zoneManager.getPreviousZone(self._activeZoneIndex)
        if not prev_zone_data:
            return {"error": "No previous zone found"}, 404

        zone = zoneMember(prev_zone_data, prev_zone_data.get("zone_index"))
        channel = zone.channels[0]
        system = self._get_system(channel.sysid)

        self.update_session(channel, zone, system)
        return self._format_session_response(channel, zone, system)

    def _format_session_response(self, channel: channelMember, zone: zoneMember, system: systemsMember) -> dict:
        """Format the session response."""
        return {
            "zone_index": zone.index,
            "channel_number": channel.channel_number,
            "channel_name": channel.name,
            "sysid": channel.sysid
        }

    def _log_debug(self, message: str):
        """Log debug messages to a file."""
        with open("/opt/op25-project/logs/app_log.txt", 'a') as file:
            file.write(f"DEBUG: {message}\n")
