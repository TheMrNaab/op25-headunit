#logMonitor.py
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from api import API  # Replace with actual class name if different
import logging
import requests
import re
import time
import threading
import queue
from watchdog.observers import Observer  # type: ignore
from watchdog.events import FileSystemEventHandler  # type: ignore
import os

# Regex to parse "voice update" log entries
VOICE_REGEX = re.compile(
    r'(?P<Date>\d{2}/\d{2}/\d{2})\s+'
    r'(?P<Time>\d{2}:\d{2}:\d{2}\.\d+)\s+'
    r'(?P<Action>voice update):\s+'
    r'tg\((?P<Talkgroup>\d+)\),\s+'
    r'freq\((?P<Frequency>\d+)\),\s+'
    r'slot\([^)]+\),\s+'
    r'prio\((?P<Priority>\d+)\)'
)

# Regex to parse "added talkgroup" log entries
TG_REGEX = re.compile(
    r'(?P<Date>\d{2}/\d{2}/\d{2})\s+'
    r'(?P<Time>\d{2}:\d{2}:\d{2}\.\d+)\s+'
    r'(?P<Action>added talkgroup)\s+'
    r'(?P<Talkgroup>\d+)\s+from\s+(?P<Source>\S+)'
    # ADD HERE
)

class LogFileHandler(FileSystemEventHandler):
    """
    Handles file system events for the log file.
    Specifically, it processes new log entries when the file is modified.
    """
    def __init__(self, logMonitor):
        self.logMonitor = logMonitor

    def on_modified(self, event):
        """
        Triggered when the log file is modified.
        Reads new lines and appends them as entries.
        """
        if event.src_path == self.logMonitor.source:
            old_lines = self.logMonitor.lines
            self.logMonitor.read()
            new_lines = self.logMonitor.lines[len(old_lines):]
            self.logMonitor.append_new_entries(new_lines)

class LogFileWatcher:
    """
    Watches the log file for changes using the watchdog library.
    """
    def __init__(self, logMonitor):
        self.logMonitor = logMonitor
        self.observer = Observer()
        self.observer.schedule(LogFileHandler(logMonitor), path=self.logMonitor.source, recursive=False)

    def start_in_thread(self):
        """
        Starts the file watcher in a separate thread to avoid blocking the main thread.
        """
        thread = threading.Thread(target=self.observer.start)
        thread.daemon = True
        thread.start()

class logMonitorOP25:
    """
    Monitors the OP25 log file for specific patterns and sends parsed entries to an API endpoint.
    """
    def __init__(self, API: "API", file="/opt/op25-project/logs/stderr_op25.log", endpoint=None):
        self.source = "/opt/op25-project/logs/stderr_op25.log"  # Path to the log file
        self.endpoint = endpoint  # API endpoint to send parsed entries
        self.lines = []  # Stores all lines read from the log file
        self.entries = []  # Stores parsed log entries
        self.queue = queue.Queue()  # Queue for sending entries to the API
        self.sender_thread = threading.Thread(target=self._sender_worker, daemon=True)
        self.sender_thread.start()
        self._api = API
        self.initFile()

    @property
    def api(self) -> "API":
        """
        Returns the API instance.
        """
        return self._api

    def initFile(self):
        """
        Initializes the log file by ensuring it exists and reading its contents.
        """
        if not os.path.exists(self.source):
            # Create the file if it doesn't exist
            open(self.source, 'w').close()

        try:
            with open(self.source, 'r') as f:
                self.lines = f.readlines()
        except Exception as e:
            raise IOError(f"Unable to read log file: {e}")

        # Process existing lines in the log file
        self.append_new_entries(self.lines)

    def read(self):
        """
        Reads the entire log file into memory.
        """
        with open(self.source) as f:
            self.lines = f.readlines()

    def append_new_entries(self, new_lines):
        """
        Parses and appends new log entries from the provided lines.
        """
        for line in new_lines:
            entry = self.interpretLine(line)
            if entry:
                self.entries.append(entry)
                self.queue.put(entry)

    def _sender_worker(self):
        """
        Worker thread that sends log entries to the API endpoint.
        Retries failed requests with exponential backoff.
        """
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
                time.sleep(5)  # Retry after a delay
                self.queue.put(entry)
            finally:
                self.queue.task_done()

    def interpretLine(self, line):
        """
        Interprets a single line from the log file.
        Tries to match the line against predefined regex patterns.
        """
        # Step 1: Check VOICE_REGEX
        m = VOICE_REGEX.match(line)
        if m:
            entry = m.groupdict()
            # Add talkgroup name using the API
            entry["Talkgroup Name"] = self.api.sessionManager.talkgroupsManager.getTalkgroupName(
                self.api.sessionManager.thisSession.activeSystem.index, m
            )
            return entry

        # Step 2: Check TG_REGEX
        m = TG_REGEX.match(line)
        if m:
            entry = m.groupdict()
            # Add talkgroup name using the API
            entry["Talkgroup Name"] = self.api.sessionManager.talkgroupsManager.getTalkgroupName(
                self.api.sessionManager.thisSession.activeChannelNumber, m
            )
            return entry

        # Step 3: Return None if no patterns match
        return None