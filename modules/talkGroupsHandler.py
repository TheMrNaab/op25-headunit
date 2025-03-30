import json
import os
import csv
import tempfile
import re



class Talkgroup:
    def __init__(self, tg_data):
        self._data = tg_data

    @property
    def tgid(self):
        return self._data.get("tgid")

    @property
    def name(self):
        return self._data.get("name")

    @property
    def priority(self):
        return self._data.get("priority", 0)

    def to_dict(self):
        return self._data

    def toJSON(self):
        return json.dumps(self._data, indent=4)

class TalkgroupSet:
    def __init__(self, sysid, tg_data):
        self.sysid = str(sysid)
        self._talkgroups = tg_data
        self._talkgroupCSVFilePath = ""


    def toTalkgroupsCSV(self) -> str | None:
        """Writes the talkgroups to a CSV file with headers 'Decimal' and 'Alpha Tag'.
        Returns File Path on success, None on failure.
        """
        try:
            file_path = self.talkgroupCSVFilePath
            with open(file_path, "w", newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Decimal", "Alpha Tag"])
                for tg in self.talkgroups:
                    writer.writerow([tg.tgid, tg.name or ""])  # Fallback to empty if name is missing
            return file_path
        except Exception as e:
            import logging
            logging.error(f"Failed to write talkgroup CSV for sysid {self.sysid}: {e}")
            return None
    
    @property
    def talkgroupCSVFilePath(self) -> str:
        if not self._talkgroupCSVFilePath:
            self._talkgroupCSVFilePath = os.path.join(tempfile.gettempdir(), f"{self.sysid}_talkgroups.csv")
        return self._talkgroupCSVFilePath
    
    @property
    def talkgroups(self):
        return [Talkgroup(tg) for tg in self._talkgroups.values()]

    def getTalkgroup(self, tgid) -> Talkgroup | None:
        try:
            return Talkgroup(self._talkgroups[str(tgid)])
        except (KeyError, TypeError):
            return None
    
    def to_dict(self):
        return self._talkgroups

    def toJSON(self):
        return json.dumps(self._talkgroups, indent=4)

class TalkgroupsHandler:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self._read_file()

    def _read_file(self):
        if not os.path.exists(self.file_path):
            return {}
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def update(self, new_data):
        self.data = new_data
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=4)

    @property
    def talkgroup_sets(self):
        return [TalkgroupSet(sysid, tg_data) for sysid, tg_data in self.data.items()]

    def getTalkgroupSetById(self, sysid) -> TalkgroupSet | None:
        if str(sysid) in self.data:
            return TalkgroupSet(sysid, self.data[str(sysid)])
        return None

    def getTalkgroup(self, sysIndex, tgid) -> Talkgroup | None:
        try:
            sysid = list(self.data.keys())[sysIndex]
            return TalkgroupSet(sysid, self.data[sysid]).getTalkgroup(tgid)
        except (IndexError, KeyError):
            return None

    def getTalkgroupName(self, sysIndex, tgid) -> str:
        tg = self.getTalkgroup(sysIndex, tgid)
        if tg:
            return tg.name
        return f"Undefined ({tgid})"

    def toJSON(self):
        return json.dumps(self.data, indent=4)