#sessionHandler.py
from __future__ import annotations
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from api import API
    from modules._session import sessionMember  # Only imported for type checking
from modules._session import SessionMember
from modules.myConfiguration import MyConfig
from modules._op25Manager import op25Manager
from modules._systemsManager import systemsManager
from modules._talkgroupSet import TalkgroupSet, TalkgroupMember, TalkgroupManager
from modules._zoneManager import channelMember, zoneMember, zoneManager
from typing import List

class SessionManager(object):
    def __init__(self, opManager: op25Manager, 
                 defaultSystemIndex:int,
                 defaultChannelIndex:int, 
                 defaultZoneIndex:int,
                 api: "API"):
        # from modules._op25Manager import op25Manager
        # TODO: USE DEFAULT SETTINGS FOR PATHS IN THE FUTURE 
        # NOTE: TO MYSELF
        self._zoneManager = zoneManager("/opt/op25-project/zones.json")
        self._talkgroupsManager = TalkgroupManager("/opt/op25-project/talkgroups.json")
        self._systemsManager = systemsManager("/opt/op25-project/systems.json")
        self._op25Manager = opManager
        self._apiManager = api
        # Pass self into session to resolve the circular reference
        self._thisSession = SessionMember(self, defaultSystemIndex, defaultZoneIndex, defaultChannelIndex)
    
    def reloadManagers(self) -> bool:
        self._zoneManager._load_zones()
        self._talkgroupsManager.reload() 
        #TODO: RELOAD SYSTEMS MANAGER
        pass
    
    @property 
    def apiManager(self) -> "API":
        return self._apiManager
    @property
    def zoneManager(self) -> zoneManager:
        return self._zoneManager

    @property
    def systemsManager(self) -> systemsManager:
        return self._systemsManager

    @property
    def talkgroupsManager(self) -> TalkgroupManager:
        return self._talkgroupsManager

    @property
    def op25Manager(self) -> op25Manager:
        return self._op25Manager

    @property
    def thisSession(self) -> SessionMember: #TODO: TEMPORARY FIX
        if self._thisSession is None:
            self._thisSession = SessionMember(self, 0, 0, 0)
        return self._thisSession