from __future__ import annotations  # You already have this
import json
import os
import tempfile
import shutil
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
        """
        Generates and returns the file path for the trunk file associated with the system.

        If the file path is not already set or is empty, it constructs a new file path
        using the system name (`sysname`) with spaces replaced by underscores. The file
        is stored in the system's temporary directory with a `.tsv` extension.

        Returns:
            str: The full file path to the trunk file.
        """
        if not hasattr(self, "_trunkFilePath") or not self._trunkFilePath:
            safe_name = "sys"  
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
            '"' + ", ".join([f"{float(x):.4f}" for x in sorted(self.control_channels, key=lambda x: float(x))]) + '"',
            "0",
            self.nac or "0",
            self.modulation or "",
            _session.activeTGIDList.toTalkgroupsCSV() or "",
            _session.activeChannel.toWhitelistTSV(),
            _session.activeChannel.toBlacklistTSV(),
            str(self.center_frequency or "")
        ]

        with open(self.trunkFilePath, "w") as f:
            f.write("\t".join(headers) + "\n")
            f.write("\t".join(values) + "\n")

        #return "/opt/op25-project/templates/_trunk.tsv"
        os.chmod(self.trunkFilePath, 0o644)
        
        
        return self.trunkFilePath

class systemsManager:
    """Represents an entire group of systems."""
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self._read_file()
        self.members = self._initialize_members()

    def _read_file(self):
        """
        Reads and parses a JSON file from the specified file path.

        If the file does not exist, an empty dictionary is returned.

        Returns:
            dict: The contents of the JSON file as a dictionary, or an empty
            dictionary if the file does not exist.
        """
        if not os.path.exists(self.file_path):
            return {}
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def _initialize_members(self):
        """
        Initializes and returns a list of `systemsMember` objects.

        This method iterates over the keys in the `self.data` dictionary, sorts them
        numerically, and creates a `systemsMember` instance for each key. Each instance
        is initialized with the corresponding value from `self.data`, the current object
        as its parent, and the key converted to an integer as its index.

        Returns:
            list: A list of `systemsMember` objects initialized with the data from `self.data`.
        """
        return [systemsMember(self.data[key], parent=self, index=int(key)) for key in sorted(self.data.keys(), key=int)]


    def reload(self):
        """
        Reloads system data from the original JSON file, discarding any current in-memory changes.
        """
        self.data = self._read_file()
        self.members = self._initialize_members()
        
    def update(self, new_data):
        """
        Updates the current system data with new_data and writes it to file.
        Before overwriting the original file, creates a backup with the .bak extension.

        Args:
            new_data (dict): The new system configuration data to save.

        Raises:
            IOError: If file operations fail.
        """
        self.data = new_data

        # Create backup of the original file
        if os.path.exists(self.file_path):
            backup_path = self.file_path + ".bak"
            shutil.copy2(self.file_path, backup_path)

        # Write updated data to file
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=4)
            
        # RELOAD THE FILE WITH NEW DATA
        self.reload()

    @property
    def systems(self):
        return self.members

    def getSystemByIndex(self, index) -> systemsMember:
        """
        Retrieves a systemsMember object by its index.

        Args:
            index (int): The index of the system to retrieve.

        Returns:
            systemsMember: An instance of systemsMember initialized with the data
            corresponding to the given index, or None if the index does not exist.
        """
        try:
            return systemsMember(self.data[str(index)], parent=self, index=index)
        except KeyError:
            return None

    def getSystemByName(self, sysname) -> systemsMember:
        """
        Retrieve a systemsMember object by its system name.

        Args:
            sysname (str): The name of the system to search for.

        Returns:
            systemsMember: An instance of systemsMember corresponding to the 
                           specified system name, or None if no match is found.
        """
        for key, entry in self.data.items():
            if entry.get("sysname") == sysname:
                return systemsMember(entry, parent=self, index=int(key))
        return None

    def getSystemByNAC(self, nac) -> systemsMember:
        """
        Retrieve a system member by its NAC (Network Access Code).

        Args:
            nac (int): The Network Access Code to search for.

        Returns:
            systemsMember: An instance of `systemsMember` corresponding to the 
            provided NAC, or `None` if no matching system is found.
        """
        for key, entry in self.data.items():
            if entry.get("nac") == nac:
                return systemsMember(entry, parent=self, index=int(key))
        return None

    def getAllSystemNames(self) -> list[str]:
        """
        Retrieves a list of all system names from the stored data.

        This method iterates through the values in the `self.data` dictionary,
        extracting the "sysname" field from each entry if it exists.

        Returns:
            list[str]: A list of system names (strings) extracted from the data.
        """
        return [entry.get("sysname") for entry in self.data.values() if entry.get("sysname")]

    def nextSystem(self, current_index) -> systemsMember | None:
        """
        Retrieve the next system in the sequence based on the current index.

        Args:
            current_index (int): The index of the current system.

        Returns:
            systemsMember | None: An instance of `systemsMember` representing the next system 
            in the sequence, or `None` if there are no systems available.
        """
        keys = sorted(self.data.keys(), key=int)
        if not keys:
            return None
        current_pos = keys.index(str(current_index)) if str(current_index) in keys else -1
        next_index = (current_pos + 1) % len(keys)
        return systemsMember(self.data[keys[next_index]], parent=self, index=next_index)

    def previousSystem(self, current_index) -> systemsMember:
        """
        Retrieve the previous system in the sequence based on the current index.

        Args:
            current_index (int): The index of the current system.

        Returns:
            systemsMember: An instance of `systemsMember` representing the previous system
            in the sequence. If the data is empty, an empty dictionary is returned.

        Notes:
            - The systems are sorted by their keys (converted to integers) to determine
              the sequence.
            - If the current index is not found in the keys, the method starts from the
              first system in the sequence.
            - The sequence wraps around, so if the current system is the first one,
              the previous system will be the last one in the sequence.
        """
        keys = sorted(self.data.keys(), key=int)
        if not keys:
            return {}
        current_pos = keys.index(str(current_index)) if str(current_index) in keys else 0
        previous_index = (current_pos - 1) % len(keys)
        return systemsMember(self.data[keys[previous_index]], parent=self, index=previous_index)
    

    def toJSON(self) -> str: # SEE API.PY :: /admin/systems endpoint; might be ok to remove
        """
        Converts the `data` attribute of the instance to a JSON-formatted string.

        Returns:
            str: A JSON string representation of the `data` attribute, formatted with an indentation of 4 spaces.
        """
        return json.dumps(self.data, indent=4)