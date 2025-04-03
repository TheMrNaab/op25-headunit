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
from datetime import datetime

DEMOD_REGEX = re.compile(
    r'(?P<Action>demodulator):\s+xlator\s+if_rate=(?P<if_rate>\d+),\s+input_rate=(?P<input_rate>\d+),\s+decim=(?P<decim>\d+),\s+if taps=\[(?P<taps>[\d,]+)\],\s+resampled_rate=(?P<resampled_rate>\d+),\s+sps=(?P<sps>\d+)'
)

RECONFIG_REGEX = re.compile(
    r'(?P<Date>\d{2}/\d{2}/\d{2})\s+'
    r'(?P<Time>\d{2}:\d{2}:\d{2}\.\d+)\s+'
    r'(?P<Action>Reconfiguring NAC)\s+from\s+0x(?P<NACFrom>[0-9A-Fa-f]{3})\s+to\s+0x(?P<NACTo>[0-9A-Fa-f]{3})'
)
AUDIO_SOCKET_REGEX = re.compile(
    r'(?P<Action>op25_audio::open_socket\(\)):\s+enabled udp host\((?P<host>[^)]+)\),\s+wireshark\((?P<wireshark>\d+)\),\s+audio\((?P<audio>\d+)\)'
)

FRAME_ASSEMBLER_REGEX = re.compile(
    r'(?P<Action>p25_frame_assembler_impl):\s+do_imbe\[(?P<do_imbe>\d+)\],\s+do_output\[(?P<do_output>\d+)\],\s+do_audio_output\[(?P<do_audio_output>\d+)\],\s+do_phase2_tdma\[(?P<do_phase2_tdma>\d+)\],\s+do_nocrypt\[(?P<do_nocrypt>\d+)\]'
)


GAIN_REGEX = re.compile(
    r'(?P<Action>gain):\s+name:\s+(?P<name>\S+)\s+range:\s+start\s+(?P<start>\d+)\s+stop\s+(?P<stop>\d+)\s+step\s+(?P<step>\d+)'
)


DEVICE_REGEX = re.compile(
    r'(?P<Action>Using device)\s+#(?P<index>\d+)\s+(?P<model>.+?)\s+SN:\s+(?P<serial>\d+)'
)

HOLD_REGEX = re.compile(
    r'(?P<Date>\d{2}/\d{2}/\d{2})\s+'
    r'(?P<Time>\d{2}:\d{2}:\d{2}\.\d+)\s+'
    r'(?P<Action>hold active)\s+tg\((?P<Talkgroup>\d+)\)'
)

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

DUID_REGEX = re.compile(
    r'(?P<Date>\d{2}/\d{2}/\d{2})\s+'
    r'(?P<Time>\d{2}:\d{2}:\d{2}\.\d+)\s+'
    r'(?P<Action>duid\d+),\s+tg\((?P<Talkgroup>\d+)\)'
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

    def _timestamp_now(self):
        now = datetime.now()
        return now.strftime("%m/%d/%y"), now.strftime("%H:%M:%S.%f")[:-3]

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

    def _match_config_patterns(self, line):
        """
        Matches config-related log lines and returns structured data.
        """
        date, time = self._timestamp_now()

        config_patterns = [
            {
                "regex": GAIN_REGEX,
                "action": "gain",
                "fields": ["name", "start", "stop", "step"]
            },
            {
                "regex": DEVICE_REGEX,
                "action": "Using device",
                "fields": ["index", "model", "serial"]
            },
            {
                "regex": DEMOD_REGEX,
                "action": "demodulator",
                "fields": ["if_rate", "input_rate", "decim", "taps", "resampled_rate", "sps"]
            },
            {
                "regex": AUDIO_SOCKET_REGEX,
                "action": "op25_audio::open_socket()",
                "fields": ["host", "wireshark", "audio"]
            },
            {
                "regex": FRAME_ASSEMBLER_REGEX,
                "action": "p25_frame_assembler_impl",
                "fields": ["do_imbe", "do_output", "do_audio_output", "do_phase2_tdma", "do_nocrypt"]
            }
        ]

        for pattern in config_patterns:
            m = pattern["regex"].match(line)
            if m:
                return {
                    "Date": date,
                    "Time": time,
                    "Action": m.group("Action"),
                    "Config": {key: m.group(key) for key in pattern["fields"]}
                }

        return None

    def interpretLine(self, line):
        """
        Interprets a single line from the log file.
        Tries to match the line against predefined regex patterns.
        """
        # Step 1: Check VOICE_REGEX
        m = VOICE_REGEX.search(line)
        if m:
            entry = m.groupdict()
            entry["Talkgroup Name"] = self.api.sessionManager.talkgroupsManager.getTalkgroupName(
                self.api.sessionManager.thisSession.activeSystem.index, m
            )
            return entry

        # Step 2: Check TG_REGEX
        m = TG_REGEX.match(line)
        if m:
            entry = m.groupdict()
            entry["Talkgroup Name"] = self.api.sessionManager.talkgroupsManager.getTalkgroupName(
                self.api.sessionManager.thisSession.activeChannelNumber, m
            )
            return entry

        # Step 3: Check RECONFIG_REGEX
        m = RECONFIG_REGEX.match(line)
        if m:
            return m.groupdict()

        # Step 4: Check HOLD_REGEX
        m = HOLD_REGEX.match(line)
        if m:
            entry = m.groupdict()
            entry["Talkgroup Name"] = self.api.sessionManager.talkgroupsManager.getTalkgroupName(
                self.api.sessionManager.thisSession.activeSystem.index, m
            )
            return entry

        # Step 5: Check DUID_REGEX
        m = DUID_REGEX.match(line)
        if m:
            entry = m.groupdict()
            entry["Talkgroup Name"] = self.api.sessionManager.talkgroupsManager.getTalkgroupName(
                self.api.sessionManager.thisSession.activeSystem.index, m
            )
            return entry

        # Step 6: Check config-related patterns
        entry = self._match_config_patterns(line)
        if entry:
            return entry

        # Step 7: Fallback for uncategorized lines
        # date, time = self._timestamp_now()
        # return {
        #     "Date": date,
        #     "Time": time,
        #     "Action": "Misc",
        #     "Data": line.strip()
        # }
