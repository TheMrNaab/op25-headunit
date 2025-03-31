from __future__ import annotations  # You already have this
import json
import os
import tempfile
from typing import TYPE_CHECKING

from modules._talkgroupSet import TalkgroupManager
if TYPE_CHECKING:
    from modules._session import session


class systemsFilesPackage:
    def __init__(self, Blacklist: str, Whitelist: str, Trunk: str, TGIDFile:str):
        self._Blacklist = Blacklist
        self._Whitelist = Whitelist
        self._Trunk = Trunk
        self._tgid = TGIDFile

    @property
    def Blacklist(self) -> str:
        return self._Blacklist

    @property
    def Whitelist(self) -> str:
        return self._Whitelist

    @property
    def Trunk(self) -> str:
        return self._Trunk
    
    @property 
    def TGID(self) -> str:
        return self._tgid
    
class systemsMember:
    """Represents a single system member."""
    def __init__(self, system_data, parent: systemsManager, index=None):
        self._data = system_data
        self._parent = parent
        self._index = index
        self._blacklistFilePath = ""
        self._systemTSVFilePath = ""

    @property
    def parent(self) -> systemsManager:
        return self._parent

    @property
    def systemTSVFilePath(self) -> str:
        if not self._systemTSVFilePath:
            self._systemTSVFilePath = os.path.join(tempfile.gettempdir(), f"_trunk_{self.sysname}.tsv")
        return self._systemTSVFilePath

    @property
    def index(self):
        return self._index

    @property
    def sysname(self):
        return self._data.get("sysname")

    @property
    def control_channels(self):
        return self._data.get("control_channels", [])

    @property
    def offset(self):
        return self._data.get("offset")

    @property
    def nac(self):
        return self._data.get("nac")

    @property
    def modulation(self):
        return self._data.get("modulation")

    @property
    def tgid_tags_file(self):
        return self._data.get("tgid_tags_file")

    @property
    def whitelist(self):
        raise Exception("General Exception. Whitelist should never be referenced. Use channel.toWhitelistTSV() instead.")
        return self._data.get("whitelist")

    @property
    def blacklist(self):
        """Returns the blacklist specified in systems.json. Must always be none."""
        raise Exception("General Exception. Blacklist should never be referenced. Reference blacklistFilePath in your code instead.")
        return self._data.get("blacklist")

    @property
    def center_frequency(self):
        return self._data.get("center_frequency")

    def to_dict(self):
        """Returns this single system member as a dictionary."""
        return self._data

    def toJSON(self):
        """Returns this single system member as a JSON dump."""
        return json.dumps(self._data, indent=4)

    @property
    def trunkFilePath(self) -> str:
        if not hasattr(self, "_trunkFilePath") or not self._trunkFilePath:
            safe_name = self.sysname.replace(" ", "_")  # Replace spaces with underscores
            self._trunkFilePath = os.path.join(tempfile.gettempdir(), f"{safe_name}_trunk.tsv")
        return self._trunkFilePath


    def toTrunkTSV(self, _session: session.SessionMember):
        """
        Writes the trunk.tsv file for OP25 using the provided session object.
        """
      
        headers = [
            "Sysname",
            "Control Channel List",
            "Offset",
            "NAC",
            "Modulation",
            "TGID Tags File",
            "Whitelist",
            "Blacklist",
            "Center Frequency"
        ]

        if _session.activeTGIDList is None:
            raise Exception("General Exception. activeTGIDList is None. This should never happen.")
        
        values = [
            self.sysname or "",
            ",".join(map(str, self.control_channels)) if self.control_channels else "",
            str(self.offset or ""),
            self.nac or "",
            self.modulation or "",
            _session.activeTGIDList.toTalkgroupsCSV() or "",
            _session.activeChannel.toWhitelistTSV(),                    # changed from files.whitelist
            _session.activeChannel.toBlacklistTSV(),                    # changed from files.blacklist
            str(self.center_frequency or "")
        ]


        with open(self.trunkFilePath, "w") as f:
            f.write("\t".join(headers) + "\n")
            f.write("\t".join(values) + "\n")

        return self.trunkFilePath

class systemsManager:
    """Represents an entire group of systems."""
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self._read_file()
        self.members = self._initialize_members()

    def _read_file(self):
        if not os.path.exists(self.file_path):
            return {}
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def _initialize_members(self):
        return [systemsMember(self.data[key], parent=self, index=int(key)) for key in sorted(self.data.keys(), key=int)]

    def update(self, new_data):
        self.data = new_data
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=4)

    @property
    def systems(self):
        return self.members

    def getSystemByIndex(self, index) -> systemsMember:
        try:
            return systemsMember(self.data[str(index)], parent=self, index=index)
        except KeyError:
            return None

    def getSystemByName(self, sysname) -> systemsMember:
        for key, entry in self.data.items():
            if entry.get("sysname") == sysname:
                return systemsMember(entry, parent=self, index=int(key))
        return None

    def getSystemByNAC(self, nac) -> systemsMember:
        for key, entry in self.data.items():
            if entry.get("nac") == nac:
                return systemsMember(entry, parent=self, index=int(key))
        return None

    def getAllSystemNames(self) -> list[str]:
        return [entry.get("sysname") for entry in self.data.values() if entry.get("sysname")]

    def nextSystem(self, current_index) -> systemsMember | None:
        keys = sorted(self.data.keys(), key=int)
        if not keys:
            return None
        current_pos = keys.index(str(current_index)) if str(current_index) in keys else -1
        next_index = (current_pos + 1) % len(keys)
        return systemsMember(self.data[keys[next_index]], parent=self, index=next_index)

    def previousSystem(self, current_index) -> systemsMember:
        keys = sorted(self.data.keys(), key=int)
        if not keys:
            return {}
        current_pos = keys.index(str(current_index)) if str(current_index) in keys else 0
        previous_index = (current_pos - 1) % len(keys)
        return systemsMember(self.data[keys[previous_index]], parent=self, index=previous_index)
    

    def toJSON(self) -> str:
        return json.dumps(self.data, indent=4)