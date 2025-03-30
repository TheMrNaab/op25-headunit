#sessionHandler.py
from __future__ import annotations
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from api import API
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
                 defaultZoneIndex:int,
                 api: "API"):
        from modules.OP25_Controller import OP25Controller
        # TODO: USE DEFAULT SETTINGS FOR PATHS IN THE FUTURE 
        # NOTE: TO MYSELF
        self._zoneManager = ZoneData("/opt/op25-project/zones.json")
        self._talkgroupsManager = TalkgroupsHandler("/opt/op25-project/talkgroups.json")
        self._systemsManager = OP25SystemManager("/opt/op25-project/systems.json")
        self._op25Manager: OP25Controller = opManager
        self._apiManager = api
        # Pass self into session to resolve the circular reference
        self._thisSession = session(self, defaultSystemIndex, defaultZoneIndex, defaultChannelIndex)
    
    @property 
    def apiManager(self) -> "API":
        return self._apiManager
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