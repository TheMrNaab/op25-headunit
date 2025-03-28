import logging
import requests
import re
import time
import threading
import queue
from watchdog.observers import Observer  # type: ignore
from watchdog.events import FileSystemEventHandler  # type: ignore

VOICE_REGEX = re.compile(
    r'(?P<Date>\d{2}/\d{2}/\d{2})\s+'
    r'(?P<Time>\d{2}:\d{2}:\d{2}\.\d+)\s+'
    r'(?P<Action>voice update):\s+'
    r'tg\((?P<Talkgroup>\d+)\),\s+'
    r'freq\((?P<Frequency>\d+)\),\s+'
    r'slot\([^)]+\),\s+'
    r'prio\((?P<Priority>\d+)\)'
)

TG_REGEX = re.compile(
    r'(?P<Date>\d{2}/\d{2}/\d{2})\s+'
    r'(?P<Time>\d{2}:\d{2}:\d{2}\.\d+)\s+'
    r'(?P<Action>added talkgroup)\s+'
    r'(?P<Talkgroup>\d+)\s+from\s+(?P<Source>\S+)'
    # ADD HERE
)

class LogFileHandler(FileSystemEventHandler):
    def __init__(self, logMonitor):
        self.logMonitor = logMonitor

    def on_modified(self, event):
        if event.src_path == self.logMonitor.source:
            old_lines = self.logMonitor.lines
            self.logMonitor.read()
            new_lines = self.logMonitor.lines[len(old_lines):]
            self.logMonitor.append_new_entries(new_lines)

class LogFileWatcher:
    def __init__(self, logMonitor):
        self.logMonitor = logMonitor
        self.observer = Observer()
        self.observer.schedule(LogFileHandler(logMonitor), path=self.logMonitor.source, recursive=False)

    def start_in_thread(self):
        thread = threading.Thread(target=self.observer.start)
        thread.daemon = True
        thread.start()

class logMonitorOP25:
    def __init__(self, API, file="/opt/op25-project/logs/stderr_op25.log", endpoint=None):
        self.source = file
        self.endpoint = endpoint
        self.lines = []
        self.entries = []
        self.queue = queue.Queue()
        self.sender_thread = threading.Thread(target=self._sender_worker, daemon=True)
        self.sender_thread.start()
        self.api = API
        try:
            with open(self.source) as f:
                self.lines = f.readlines()
        except Exception as e:
            raise IOError(f"Unable to read log file: {e}")
        self.append_new_entries(self.lines)

    def read(self):
        with open(self.source) as f:
            self.lines = f.readlines()

    def append_new_entries(self, new_lines):
        for line in new_lines:
            entry = self.interpretLine(line)
            if entry:
                self.entries.append(entry)
                self.queue.put(entry)

    def _sender_worker(self):
        while True:
            entry = self.queue.get()
            if not self.endpoint:
                self.queue.task_done()
                continue
            try:
                response = requests.post(self.endpoint, json=entry, timeout=5)
                response.raise_for_status()
            except Exception as e:
                logging.error(f"POST failed, re-queueing entry: {e}")
                time.sleep(5)
                self.queue.put(entry)
            finally:
                self.queue.task_done()

    def interpretLine(self, line):
        m = VOICE_REGEX.match(line)
        if m:
            entry = m.groupdict()
            entry["Talkgroup Name"] = self.api.file_obj.get_alpha_tag(int(entry["Talkgroup"]))
            return entry

        m = TG_REGEX.match(line)
        if m:
            entry = m.groupdict()
            entry["Talkgroup Name"] = self.api.file_obj.get_alpha_tag(int(entry["Talkgroup"]))
            return entry

        return None