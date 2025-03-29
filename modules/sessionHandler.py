from modules.myConfiguration import MyConfig
from modules.OP25_Controller import OP25Controller
from modules.systemsHandler import OP25FilesPackage, OP25SystemManager, OP25System
from modules.sessionHandler import session, sessionHandler
from modules.talkGroupsHandler import TalkgroupSet, TalkgroupsHandler

from modules.zoneHandler import Channel, Zone, ZoneData
from modules.talkGroupsHandler import TalkgroupsHandler, TalkgroupSet
from typing import List
from __future__ import annotations


class sessionHandler(object):
    def __init__(self, opManager: OP25Controller, 
                 defaultSystemIndex:int,
                 defaultChannelIndex:int, 
                 defaultZoneIndex:int):
        # TODO: USE DEFAULT SETTINGS FOR PATHS IN THE FUTURE 
        # NOTE: TO MYSELF
        self._zoneManager = ZoneData("/opt/op25-project/zones.json")
        self._talkgroupsManager = TalkgroupsHandler("/opt/op25-project/talkgroups.json")
        self._systemsManager = OP25SystemManager("/opt/op25-project/systems.json")
        self._op25Manager: OP25Controller = opManager


        # Pass self into session to resolve the circular reference
        self._thisSession = session(self, defaultSystemIndex, defaultZoneIndex, defaultChannelIndex)
    
    @property
    def zoneManager(self) -> ZoneData:
        return self._zoneManager

    @property
    def systemsManager(self) -> OP25SystemManager:
        return self._systemsManager

    @property
    def talkgroupsManager(self) -> TalkgroupsHandler:
        return self._talkgroupsManager

    @property
    def op25Manager(self) -> OP25Controller:
        return self._op25Manager

    @property
    def thisSession(self) -> session:
        return self._thisSession

    def op25ConfigFiles(self) -> OP25FilesPackage:
        """Returns a dictionary of all the configuration files (trunk, whitelist, blacklist)"""
        return OP25FilesPackage(Blacklist = self.thisSession.activeChannel.toBlacklistTSV,
                               Whitelist = self.thisSession.activeChannel.toWhitelistTSV, 
                               Trunk = self.thisSession.activeSystem.toTrunkTSV(),
                               TGIDFile= self.thisSession.activeTGIDList.toTalkgroupsCSV())
class session(object):

    def __init__(self, sessionMgr:sessionHandler, 
                 systemIndex:int,
                 zoneIndex:int,
                 channelIndex:int):
        
        self.sessionManager:sessionHandler = sessionMgr
        self._activeChannelNumber = channelIndex
        self._activeZoneIndex = zoneIndex
        self._activeChannel = self.sessionManager.zoneManager.getChannel(zone_index=zoneIndex, channel_number=channelIndex)
        self._activeZone = self.sessionManager.zoneManager.getZoneByIndex(index=self.activeChannel.zone_index)
        self._zones = self.sessionManager.zoneManager.zones 
        self._activeSystem = self.sessionManager.systemsManager.getSystemByIndex(systemIndex)
        #NOTE: CAN I DELETE? NEED TO CHECK
        self._activeSysIndex = systemIndex
        self._activeTGIDList =  self.sessionManager.talkgroupsManager.getTalkgroupSetById(sysid=self.activeSysIndex)
        



    @property
    def activeTGIDList(self) -> TalkgroupSet:
        return self._activeTGIDList

    @property
    def activeChannelNumber(self) -> int:
        """Returns the channel number of the talkgroup TGID whitelist being played in OP25."""
        return self._activeChannelNumber

    @property
    def activeZoneIndex(self) -> int:
        """Returns the zone index of the talkgroup TGID whitelist being played in OP25."""
        return self._activeZoneIndex

    @property
    def activeChannel(self) -> Channel:
        """Returns the active channel object being played in OP25."""
        return self._activeChannel

    @property
    def activeZone(self) -> Zone:
        """Returns the active zone of the channel being played in OP25 """
        return self._activeZone

    @property
    def activeSystem(self) -> OP25System:
        """Returns the active system of the channel being played in OP25."""
        return self._activeSystem

    @property
    def zones(self) -> List[Zone]:
        """Returns the zones preloaded into zones.json. """
        return self._zones

    @property
    def activeSysIndex(self) -> int:
        """Returns the P25 system index preloaded from systems.json."""
        return self._activeSysIndex


    def changeTalkgroup(self, didSystemChange: bool):
        """Changes the talkgroup currently active in OP25.

        Args:
            didSystemChange (bool): Indicates whether the system changed,
            which determines how the talkgroup switch is handled.
        """
        if not didSystemChange:
               self.sessionManager.op25Manager.switchTG(self.activeChannel.tgid, self.activeChannel.blacklistTGIDs)   
        else:
               self.sessionManager.op25Manager.switchSystem(self.sessionManager.thisSession)
               


    def updateSession(self, ch:Channel, zn:Zone, sys:OP25System):
        didSystemChange = False
        # IF THE NEW SYSTEM INDEX DIFFERS FROM THE PREVIOUS ONE
        # AND IS NOT THE DEFAULT (-1), THE SYSTEM HAS CHANGED
        if sys.index != self.activeSysIndex and sys.index != -1:
            didSystemChange = True

        # UPDATE TO NEW VALUES
        self._activeChannelNumber = ch.channel_number
        self._activeChannel = ch
        self._activeZoneIndex = zn.index
        self._activeZone = zn
        self._activeSysIndex = sys.index
        self._activeSys = sys
        self._activeTGIDList = self.sessionManager.talkgroupsManager.getTalkgroupSetById(sys.index)
        
        self.changeTalkgroup(didSystemChange) # ONLY SHOULD BE CALLED FROM HERE!

        return True

    def nextChannel(self):
        # Get current zone index and channel number from session
        current_zone_index = self.activeZoneIndex
        current_channel_number = self.activeChannelNumber

        # Get the next channel from the zone manager
        next_ch_data = self.sessionManager.zoneManager.getNextChannel(current_zone_index, current_channel_number)
        if not next_ch_data:
            return {"error": "No next channel found"}, 404

        # Get Zone and Channel objects
        zone = self.sessionManager.zoneManager.getZoneByIndex(current_zone_index)
        channel = Channel(next_ch_data, zone.index)

        # Find system by sysid
        sys = self.sessionManager.systemsManager.getSystemByIndex(channel.sysid)
        if not sys:
            return {"error": f"System with sysid {channel.sysid} not found"}, 404

        # Update session
        self.updateSession(channel, zone, sys)

        # Return updated session info
        return {
            "zone_index": zone.index,
            "channel_number": channel.channel_number,
            "channel_name": channel.name,
            "sysid": channel.sysid
        }

    def previousChannel(self):
        # Get current zone index and channel number from session
        current_zone_index = self.activeZoneIndex
        current_channel_number = self.activeChannelNumber

        # Get the previous channel from the zone manager
        prev_ch_data = self.sessionManager.zoneManager.getPreviousChannel(current_zone_index, current_channel_number)
        if not prev_ch_data:
            return {"error": "No previous channel found"}, 404

        # Get Zone and Channel objects
        zone = self.sessionManager.zoneManager.getZoneByIndex(current_zone_index)
        channel = Channel(prev_ch_data, zone.index)

        # Find system by sysid
        sys = self.sessionManager.systemsManager.getSystemByIndex(channel.sysid)
        if not sys:
            return {"error": f"System with sysid {channel.sysid} not found"}, 404

        # Update session
        self.updateSession(channel, zone, sys)

        # Return updated session info
        return {
            "zone_index": zone.index,
            "channel_number": channel.channel_number,
            "channel_name": channel.name,
            "sysid": channel.sysid
        }
    
    def nextZone(self):
        current_zone_index = self.activeZoneIndex

        # Get the next zone from the zone manager
        next_zone_data = self.sessionManager.zoneManager.nextZone(current_zone_index)
        if not next_zone_data:
            return {"error": "No next zone found"}, 404

        # Get zone and first channel
        zone = Zone(next_zone_data, next_zone_data.get("zone_index"))
        channels = zone.channels
        if not channels:
            return {"error": "Zone has no channels"}, 404
        channel = channels[0]

        # Get system
        sys = self.sessionManager.systemsManager.getSystemByIndex(channel.sysid)
        if not sys:
            return {"error": f"System with sysid {channel.sysid} not found"}, 404

        # Update session
        self.updateSession(channel, zone, sys)



        return {
            "zone_index": zone.index,
            "channel_number": channel.channel_number,
            "channel_name": channel.name,
            "sysid": channel.sysid
        }
    
    def previousZone(self):
        current_zone_index = self.activeZoneIndex

        # Get the previous zone from the zone manager
        prev_zone_data = self.sessionManager.zoneManager.previousZone(current_zone_index)
        if not prev_zone_data:
            return {"error": "No previous zone found"}, 404

        # Get zone and first channel
        zone = Zone(prev_zone_data, prev_zone_data.get("zone_index"))
        channels = zone.channels
        if not channels:
            return {"error": "Zone has no channels"}, 404
        channel = channels[0]

        # Get system
        sys = self.sessionManager.systemsManager.getSystemByIndex(channel.sysid)
        if not sys:
            return {"error": f"System with sysid {channel.sysid} not found"}, 404

        # Update session
        self.updateSession(channel, zone, sys)

        return {
            "zone_index": zone.index,
            "channel_number": channel.channel_number,
            "channel_name": channel.name,
            "sysid": channel.sysid
        }