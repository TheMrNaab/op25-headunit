#_session.py

from modules._zoneManager import channelMember, zoneMember  # Updated import for channelMember
from modules._systemsManager import systemsMember
from typing import List, TYPE_CHECKING
from modules._talkgroupSet import TalkgroupSet

if TYPE_CHECKING:
    from modules._sessionManager import SessionManager

class SessionMember:
    def __init__(self, session_mgr: "SessionManager", system_index: int, zone_index: int, channel_index: int):
        """
        Initializes a SessionMember instance.

        Args:
            session_mgr (SessionManager): The session manager instance managing this session.
            system_index (int): The index of the system to associate with this session.
            zone_index (int): The index of the zone to associate with this session.
            channel_index (int): The index of the channel to associate with this session.

        Attributes:
            _session_manager (SessionManager): Reference to the session manager.
            _activeTGIDList (list): List of active TGIDs for the specified system index.
            _activeChannelNumber (int): The active channel number.
            _activeZoneIndex (int): The active zone index.
            _activeSysIndex (int): The active system index.
            _activeSystem: The active system object retrieved based on the system index.
            _activeZone: The active zone object retrieved based on the zone index.
            _active_channel: The active channel object retrieved based on the zone and channel indices.
        """
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

    def _get_active_zone_channel(self, channel_number: int) -> channelMember:
        """Retrieve the active channel object."""
        return self.sessionManager.zoneManager.getChannel(self._activeZoneIndex, channel_number)
    
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
        """
        Update the session state with the provided channel, zone, and system information,
        and trigger necessary changes based on the updated state.

        Args:
            channel (channelMember): The channel object containing the channel number and related information.
            zone (zoneMember): The zone object containing the zone index and related information.
            system (systemsMember): The system object containing the system index and related information.

        Behavior:
            - Logs debug information about the update process.
            - Updates the active session state with the provided channel, zone, and system.
            - Determines if the system has changed by comparing the current system index with the previous one.
            - Updates the active talkgroup ID list based on the new system index.
            - Triggers a talkgroup or system change if necessary.
        """
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
        """
        Handles the change of a talkgroup or system.

        This method determines whether a system change or a talkgroup change
        has occurred and invokes the appropriate method on the op25Manager
        to handle the change.

        Args:
            did_system_change (bool): A flag indicating whether the system
                                      has changed. If True, a system change
                                      is handled; otherwise, a talkgroup
                                      change is handled.
        """
        """Handle talkgroup or system change."""
        
        self.sessionManager.op25Manager.switchSystem(self)

    def nextChannel(self):
        """
        Switch to the next channel in the current zone.

        This method retrieves the next channel in the current zone using the session manager's
        zone manager. If a next channel is found, it updates the session with the new channel,
        zone, and system information, and returns a formatted session response. If no next
        channel is found, it returns an error response.

        Returns:
            dict: A dictionary containing the session response or an error message.
            int: HTTP status code (200 for success, 404 if no next channel is found).
        """
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
        """
        Switch to the previous channel in the current zone.

        This method retrieves the previous channel data from the session manager's
        zone manager based on the current active zone index and channel number.
        If no previous channel is found, it returns an error response.

        Returns:
            dict: A dictionary containing the session response data if the previous
                  channel is successfully retrieved and updated.
            tuple: A tuple containing an error message and HTTP status code (404)
                   if no previous channel is found.
        """
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
        """
        Switch to the next zone in the session.

        This method retrieves the next zone data using the session manager's zone manager.
        If no next zone is found, it returns an error response with a 404 status code.
        Otherwise, it initializes a new zone member, retrieves the associated system,
        updates the session with the new channel, zone, and system, and formats the session
        response.

        Returns:
            dict: A dictionary containing the session response data or an error message.
            int: HTTP status code (404 if no next zone is found).
        """
        """Switch to the next zone."""
        next_zone_data = self.sessionManager.zoneManager.getNextZone(self._activeZoneIndex)
        if not next_zone_data:
            return {"error": "No next zone found"}, 404

        zone = zoneMember(next_zone_data, next_zone_data.get("zone_index"))
        channel = zone.channels[0]
        system = self._get_system(channel.sysid) # Remember, sysid is the system index. 

        self.update_session(channel, zone, system)
        return self._format_session_response(channel, zone, system)

    def goChannel(self, channel_number: int):
        """
        Switch to a specific channel in the current zone.

        Args:
            channel_number (int): The number of the channel to switch to.

        Returns:
            tuple: A dictionary containing an error message and an HTTP status code (404) 
                   if the channel is not found, or the formatted session response if the 
                   channel is successfully switched.

        Raises:
            None
        """
        """Switch to a specific channel in the current zone."""
        channel_data = self.sessionManager.zoneManager.getChannel(self._activeZoneIndex, channel_number)
        if not channel_data:
            return {"error": "Channel not found"}, 404

        zone = self._get_zone(self._activeZoneIndex)
        channel = channelMember(channel_data, zone.index)
        system = self._get_system(channel.sysid) # Remember, sysid is the system index. 
        self.update_session(channel, zone, system)
        return self._format_session_response(channel, zone, system)

    def previousZone(self):
        """
        Switch to the previous zone.

        This method retrieves the data for the previous zone using the session manager's
        zone manager. If no previous zone is found, it returns an error response with a
        404 status code. Otherwise, it initializes the zone and its first channel, retrieves
        the associated system, updates the session with the new zone, channel, and system,
        and returns a formatted session response.

        Returns:
            dict: A dictionary containing the formatted session response if a previous zone
                  is found, or an error message if no previous zone exists.
            int: The HTTP status code (200 for success, 404 for no previous zone).
        """
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
        """
        Formats the session response for functions that set talkgroups.

        Args:
            channel (channelMember): The channel member object containing channel details.
            zone (zoneMember): The zone member object containing zone details.
            system (systemsMember): The system member object containing system details.

        Returns:
            dict: A dictionary containing the formatted session response with the following keys:
                - "zone_index" (int): The index of the zone.
                - "channel_number" (int): The number of the channel.
                - "channel_name" (str): The name of the channel.
                - "sysid" (int): The system ID associated with the channel.
        """
        """Format the session response that can be returned for functions that set talkgroups."""
        return {
            "zone_index": zone.index,
            "channel_number": channel.channel_number,
            "channel_name": channel.name,
            "sysid": channel.sysid
        }

    def _log_debug(self, message: str):
        """
        Logs a debug message to a file.

        Args:
            message (str): The debug message to be logged.

        Writes the debug message to a file located at 
        '/opt/op25-project/logs/app_log.txt' in append mode, 
        prefixed with 'DEBUG:'.
        """
        """Log debug messages to a file."""
        with open("/opt/op25-project/logs/app_log.txt", 'a') as file:
            file.write(f"DEBUG: {message}\n")
