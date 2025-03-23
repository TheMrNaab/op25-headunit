import logging
from watchdog.observers import Observer  # type: ignore
from watchdog.events import FileSystemEventHandler  # type: ignore
import time
import threading

class LogFileHandler(FileSystemEventHandler):
    def __init__(self, logMonitor):
        self.logMonitor = logMonitor

    def on_modified(self, event):
        if event.src_path == self.logMonitor.source:
            old_lines = self.logMonitor.lines
            self.logMonitor.read()
            new_lines = self.logMonitor.lines[len(old_lines):]
            self.logMonitor.append_new_entries(new_lines)
            self.logMonitor.build()

class LogFileWatcher:
    def __init__(self, logMonitor):
        self.logMonitor = logMonitor
        self.event_handler = LogFileHandler(logMonitor)
        self.observer = Observer()
        # Uncomment the line below to watch the log file path
        # self.observer.schedule(self.event_handler, path=self.logMonitor.source, recursive=False)

    def start(self):
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

    def start_in_thread(self):
        thread = threading.Thread(target=self.start)
        thread.daemon = True
        thread.start()

class logMonitorOP25(object):
    def __init__(self, file="/opt/op25-project/logs/stderr_op25.log"):
        logging.debug(f"Initializing logMonitorOP25 with file: {file}")
        self.source = file
        self.lines = []
        self.entries = []
        try:
            with open(file, "r") as f:
                self.lines = f.readlines()
                logging.debug(f"Read {len(self.lines)} lines from log file")
        except Exception as e:
            raise IOError(f"Unable to read log file: {e}")
        
        self.append_new_entries(self.lines)
        self.build()

    def read(self):
        logging.debug("Reading log file")
        try:
            with open(self.source, "r") as f:
                self.lines = f.readlines()
        except Exception as e:
            raise IOError(f"Unable to read log file: {e}")

    def build(self):
        logging.debug("Building entries from log lines")
        self.entries = []
        for line in self.lines:
            entry = self.interpretLine(line)
            if entry:
                self.entries.append(entry)
        logging.debug(f"Built {len(self.entries)} entries")

    def append_new_entries(self, new_lines):
        logging.debug(f"Appending {len(new_lines)} new lines")
        for line in new_lines:
            entry = self.interpretLine(line)
            if entry:
                self.entries.append(entry)
        logging.debug(f"Total entries after append: {len(self.entries)}")

    def matchTalkgroups(self, dt, TGIDs=[]):
        logging.debug(f"Matching talkgroups after {dt} with TGIDs: {TGIDs}")
        hits = 0
        for entry in self.entries:
            entry_time = f"{entry['date']} {entry['time']}"
            if entry_time > dt and entry['tgid'] in TGIDs:
                hits += 1
        logging.debug(f"Found {hits} matching talkgroups")
        return hits

    def interpretLine(self, line):
        cells = line.split(' ')
        if len(cells) == 7:
            data = {
                "date": cells[0],
                "time": cells[1],
                "action": cells[2],
                "type": cells[3],
                "tgid": int(cells[4]),
                "source": cells[6].strip()
            }
            return data
        else:
            return None

def interactive_prompt():
    monitor = None
    while True:
        
        print("\nSelect an option:")
        print("1. Create logMonitorOP25 instance")
        print("2. Read log file")
        print("3. Build entries")
        print("4. Match talkgroups")
        print("5. Start file watcher")
        print("6. Show entries")
        print("7. Exit")
        choice = input("Enter choice: ").strip()
        if choice == "1":
            file_path = input("Enter log file path (default: /opt/op25-project/logs/stderr_op25.log): ").strip()
            if not file_path:
                file_path = "/opt/op25-project/logs/stderr_op25.log"
            try:
                monitor = logMonitorOP25(file=file_path)
                print("Instance created successfully.")
            except Exception as e:
                print(f"Error creating instance: {e}")
        elif choice == "2":
            if monitor:
                try:
                    monitor.read()
                    print("Log file read successfully.")
                except Exception as e:
                    print(f"Error reading log file: {e}")
            else:
                print("Please create an instance first (option 1).")
        elif choice == "3":
            if monitor:
                monitor.build()
                print("Entries built successfully.")
            else:
                print("Please create an instance first (option 1).")
        elif choice == "4":
            if monitor:
                dt = input("Enter date and time (format: YYYY-MM-DD HH:MM:SS): ").strip()
                tgids_input = input("Enter TGIDs separated by commas: ").strip()
                try:
                    tgids = [int(x.strip()) for x in tgids_input.split(",") if x.strip()]
                except ValueError:
                    print("Invalid TGIDs input.")
                    continue
                hits = monitor.matchTalkgroups(dt, tgids)
                print(f"Matching talkgroups count: {hits}")
            else:
                print("Please create an instance first (option 1).")
        elif choice == "5":
            if monitor:
                watcher = LogFileWatcher(monitor)
                watcher.start_in_thread()
                print("File watcher started in background.")
            else:
                print("Please create an instance first (option 1).")
        elif choice == "6":
            if monitor:
                print("Current entries:")
                for entry in monitor.entries:
                    print(entry)
            else:
                print("Please create an instance first (option 1).")
        elif choice == "7":
            print("Exiting interactive prompt.")
            break
        else:
            print("Invalid option. Try again.")

if __name__ == "__main__":
    interactive_prompt()