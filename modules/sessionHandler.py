#sessionHandler.py
from __future__ import annotations
from modules.myConfiguration import MyConfig
from modules.OP25_Controller import OP25Controller
from modules.systemsHandler import OP25FilesPackage, OP25SystemManager, OP25System
from modules.sessionTypes import session
from modules.talkGroupsHandler import TalkgroupSet, TalkgroupsHandler
from modules.zoneHandler import Channel, Zone, ZoneData
from typing import List

class sessionHandler(object):
    def __init__(self, opManager: OP25Controller, 
                 defaultSystemIndex:int,
                 defaultChannelIndex:int, 
                 defaultZoneIndex:int):
        from modules.OP25_Controller import OP25Controller
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

    # def op25ConfigFiles(self) -> OP25FilesPackage:
    #     """Returns a dictionary of all the configuration files (trunk, whitelist, blacklist)"""
    #     return OP25FilesPackage(
    #         Blacklist = self.thisSession.activeChannel.toBlacklistTSV(),
    #         Whitelist = self.thisSession.activeChannel.toWhitelistTSV(), 
    #         Trunk     = self.thisSession.activeSystem.toTrunkTSV(),  # <-- FIXED: removed ()
    #         TGIDFile  = self.thisSession.activeTGIDList.toTalkgroupsCSV()
    #     )