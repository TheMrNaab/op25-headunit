import json
import os
import csv
import tempfile
from typing import TYPE_CHECKING, Union  # Add TYPE_CHECKING for conditional imports

if TYPE_CHECKING:
    from modules._sessionManager import sessionManager  # Import only for type hints

class TalkgroupMember:
    def __init__(self, tg_data: dict, parent_set: "TalkgroupSet", index: str):
        self._data = tg_data
        self._parent_set = parent_set
        self._index = index  # Store the physical index

    @property
    def tgid(self) -> int:
        return self._data.get("tgid")

    @property
    def name(self) -> str:
        return self._data.get("name", "")

    @property
    def priority(self) -> int:
        return self._data.get("priority", 0)

    @property
    def index(self) -> str:
        """Return the physical index of the talkgroup."""
        return self._index

    def to_dict(self) -> dict:
        return {"index": self._index, **self._data}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=4)

    @property
    def parent(self) -> "TalkgroupSet":
        return self._parent_set


class TalkgroupSet:
    def __init__(self, *, index, sysid, tg_data, parent_manager):
        self._index = index
        self._sysid = sysid
        self._tg_data = tg_data
        self._parent_manager = parent_manager
        self._talkgroups = [
            TalkgroupMember(tg, self, index) for index, tg in tg_data.items()
        ]
        self._talkgroup_csv_file_path = ""

    @property
    def talkgroups(self) -> list[TalkgroupMember]:
        return self._talkgroups
    
    @property
    def sysIndex(self) -> int:
        return self._index

    @property
    def sysid(self) -> str:
        return self._sysid

    def getTalkgroup(self, tgid: int) -> Union["TalkgroupMember", None]:
        for tg in self._talkgroups:
            if tg.tgid == tgid:
                return tg
        return None

    def toTalkgroupsCSV(self) -> Union[str, None]:
        """Writes the talkgroups to a CSV file with headers 'Index', 'Decimal', and 'Alpha Tag'.
        Returns File Path on success, None on failure.
        """
        try:
            file_path = self.talkgroup_csv_file_path
            with open(file_path, "w", newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Decimal", "Alpha Tag"])
                for tg in self._talkgroups:
                    writer.writerow([tg.tgid, tg.name])  # Include the index
            return file_path
        except Exception as e:
            import logging
            logging.error(f"Failed to write talkgroup CSV for sysindex {self.sysIndex}: {e}")
            return None

    @property
    def talkgroup_csv_file_path(self) -> str:
        """Returns the file path for the talkgroup CSV. Generates it if not already set."""
        if not self._talkgroup_csv_file_path:
            filename = f"{str(self.sysid)}_talkgroups.csv"
            self._talkgroup_csv_file_path = os.path.join(tempfile.gettempdir(), filename)
        return self._talkgroup_csv_file_path

class TalkgroupManager:
    def __init__(self, file_path: str):
        from modules._sessionManager import SessionManager  # Lazy import to avoid circular dependency
        self.file_path = file_path
        self._data = self._read_file()
        self._sets = self._initialize_sets()

    def _read_file(self) -> dict:
        if not os.path.exists(self.file_path):
            return {}
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def _initialize_sets(self) -> list[TalkgroupSet]:
        return [
            TalkgroupSet(
                index = index, 
                sysid = sysid, 
                tg_data = tg_data, 
                parent_manager = self)
            for index, (sysid, tg_data) in enumerate(self._data.items())
        ]

    def logIT(self, line, file_path = "/opt/op25-project/logs/app_log.txt"):
        with open(file_path, 'a') as file:
            file.write(line + '\n')

    def getTalkgroupSetBySysIndex(self, system_index: str) -> Union["TalkgroupSet", None]:
        """Finds a TalkgroupSet by its system index."""
        self.logIT(f"Searching for TalkgroupSet with system index: {system_index}")
        for tg_set in self._sets:
            self.logIT(f" + Checking TalkgroupSet with sysIndex: {tg_set.sysIndex}")
            if tg_set.sysIndex == system_index:
                self.logIT(f" - Found TalkgroupSet: {tg_set.sysIndex}")
                return tg_set
            else:
                self.logIT(f" - Not a match: {tg_set.sysIndex} != {system_index}")
        self.logIT(f"TalkgroupSet with system index {system_index} not found.")
        return None
    
    def getTalkgroupName(self, sysIndex: str, tgid: int) -> str:
        """Finds the talkgroup by system index and tgid, and returns its name."""
        tg_set = self.getTalkgroupSetBySysIndex(sysIndex)
        if tg_set:
            tg_member = tg_set.getTalkgroup(tgid)
            if tg_member:
                return tg_member.name
        return f"Undefined ({tgid})"

    @property
    def sets(self) -> list[TalkgroupSet]:
        return self._sets

    def get_set_by_sysid(self, sysid: str) -> Union["TalkgroupSet", None]:
        for tg_set in self._sets:
            if tg_set.sysid == sysid:
                return tg_set
        return None

    def get_member(self, sysid: str, tgid: int) -> Union["TalkgroupMember", None]:
        tg_set = self.get_set_by_sysid(sysid)
        if tg_set:
            return tg_set.getTalkgroup(tgid)
        return None

    def get_member_name(self, sysid: str, tgid: int) -> str:
        member = self.get_member(sysid, tgid)
        return member.name if member else f"Undefined ({tgid})"

    def update(self, new_data: dict):
        self._data = new_data
        self._sets = self._initialize_sets()
        with open(self.file_path, 'w') as f:
            json.dump(self._data, f, indent=4)

    def to_json(self) -> str:
        return json.dumps(self._data, indent=4)