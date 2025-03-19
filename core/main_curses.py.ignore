import curses
import csv
from tts import SpeechEngine
from ir import IRRemoteHandler
from file_object import FileObject
from control import OP25Controller  # This must import properly
from PySide6.QtCore import QThread, Signal
from logger import CustomLogger
import re
import time
import sys
import os

class MonitorLogFileWorker(QThread):
    import csv 
    """Worker thread for monitoring the OP25 log file without blocking the UI."""
    signal_tg_update = Signal(str)  # Signal to send back the TG number

    def __init__(self, op25_instance, stderr_path):
        super().__init__()
        self.stderr_path = stderr_path
        self.op25 = op25_instance
        self.tg_dict = {}
        self.load_csv(self.op25.tgroups_file)

    def extract_tg_number(self, line):
        """Extracts the TG number from a voice update line."""
        import re
        match = re.search(r'voice update:.*tg\((\d+)\)', line)
        return match.group(1) if match else None

    def load_csv(self, csv_file):
        """Loads the talkgroup CSV file into a dictionary."""
        try:
            with open(csv_file, "r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    decimal = row["Decimal"].strip()  # Ensure no spaces
                    alpha_tag = row["Alpha Tag"].strip()
                    self.tg_dict[decimal] = alpha_tag  # Store in dictionary
        except FileNotFoundError:
            print(f"[ERROR] CSV file '{csv_file}' not found.")

    def lookup_tg(self, arg):
        """Returns the Alpha Tag if found, otherwise returns the original arg."""
        return self.tg_dict.get(str(arg), str(arg))  # Convert arg to string for safe lookup


    def run(self):
        """Monitors the log file and emits TG number when a new voice update appears."""
        try:
            with open(self.stderr_path, "r") as file:
                file.seek(0, 2)  # Move to the end of the file to only capture new lines

                while True:
                    line = file.readline()
                    if not line:
                        continue  # No new line, keep waiting

                    tg_number = self.extract_tg_number(line)
                    if tg_number:
                        alpha = self.lookup_tg(tg_number)
                        self.signal_tg_update.emit(alpha)  # ✅ Emit the TG number
                        print(f"[ACTIVE TG]: {alpha}")  # Debug print

        except FileNotFoundError:
            print(f"[ERROR] File '{self.stderr_path}' not found.")

class CursesUI:
    def __init__(self, stdscr):
        self.op25 = OP25Controller()
        self.op25.start()
        self.log = CustomLogger(self.op25.logFile)
        self.currentFile = FileObject()
         # Select the first zone
        self.current_tg_text = "[No Talkgroup]"
        self.current_channel_text = f"[Channel Name] ()"
        self.stdscr = stdscr
        self.ir_on = True
        self.speech_on = False
        self.currentFile = FileObject()
        self.isMenuActive = False
        self.current_tg_text = ""
        self.selected_button = None
        self.zone_names = self.currentFile.zone_names
        self.current_channel_name = "None"
        self.current_channel_number = 0
        self.current_zone_index = 0
        if self.speech_on:
            self.speech = SpeechEngine()
        

        # Initialize curses
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Title Bar
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Yellow text for Current TG
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)  # White text; Yellow BG
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)  # White text; Yellow BG

 
        first_zone = self.currentFile.get_zone(0)

        if first_zone is not None:
            channels = self.currentFile.get_channels_by_zone(first_zone)
            if channels and len(channels) > 0:
                # Set the first channel in the first zone as the current
                self.currentFile.current_zone_index = 0
                self.currentFile.current_tg_index = 0
                self.currentFile.current_channel_number = 0
                self.select_talkgroup()
                # Update the curses display
                self.update_display()
            else:
                print("[ERROR] No channels found in the first zone")
        else:
            print("[ERROR] No zones available")

       

        self.connection_status = "󰢦"  # Trusted Workspace
        self.progress_status = "󰑍"  # Spinner
        self.sound_status = "󰖁"  # Mute

        try:
            self.draw_ui()
        except curses.error as e:
            self.log.error(e)

    def on_op25_initialized(self):
        """Handles OP25 initialization and sets the initial zone and channel in the curses UI."""
        self.current_status = "Connected"  # Update status message

        # Select the first zone
        first_zone = self.currentFile.get_zone(0)
        if first_zone is not None:
            channels = self.currentFile.get_channels_by_zone(first_zone)
            if channels and len(channels) > 0:
                # Set the first channel in the first zone as the current
                self.currentFile.current_zone_index = 0
                self.currentFile.current_tg_index = 0
                self.select_talkgroup()
                # Update the curses display
                self.update_display()
            else:
                print("[ERROR] No channels found in the first zone")
        else:
            print("[ERROR] No zones available")

        # Perform additional setup
        self.connection_status = "󰢦"  # Trusted Workspace (Default)
        self.progress_status = ""  # Stop any loading indication
        self.update_display()

        self.logMonitor = MonitorLogFileWorker(self.op25, self.op25.stderr_file)
        self.logMonitor.signal_tg_update.connect(self.update_status_bar)
        self.logMonitor.start()
    
    def update_current_tg_text(self, new_text):
        """Updates the current talkgroup text and refreshes the curses UI."""
        self.current_tg_text = f"[TG] {new_text}"  # Format text with TG prefix
        self.update_display()  # Refresh the UI to reflect changes

    def update_current_tg_text(self, new_text):
        """Updates the current TG text."""
        self.current_tg_text = new_text
        self.update_display()
    
    def extract_tg_number(self, line):
        """Extracts the talkgroup number from a voice update line."""
        match = re.search(r'voice update:.*tg\((\d+)\)', line)
        return match.group(1) if match else None

    def monitor_stderr(self, file_path):
        """Monitors the stderr2 file for new voice update lines and updates the UI."""
        try:
            with open(file_path, "r") as file:
                file.seek(0, 2)  # Move to the end of the file

                while True:
                    line = file.readline().strip()
                    if not line:
                        continue  # No new line, keep waiting

                    tg_number = self.extract_tg_number(line)
                    if tg_number:
                        print(f"[ACTIVE TG]: {tg_number}")  # Print the latest TG number
                        self.update_current_tg_text(tg_number)  # Update UI with the new talkgroup

        except FileNotFoundError:
            print(f"[ERROR] File '{file_path}' not found.")

    def load_first_channel(self):
        """Loads the first channel of the current zone and applies its talkgroup settings in the curses UI."""
        first_channel = self.currentFile.get_channels_by_zone(
            self.currentFile.zone_names[self.currentFile.current_zone_index]
        )

        if not first_channel:  # Prevents index error if zone is empty
            print("[WARNING] No channels found in the current zone.")
            return
        
        self.currentFile.current_tg_index = first_channel[0]["channel_number"]

        self.update_display()
        self.change_talkgroup()  # Ensure the talkgroup is updated

    def change_talkgroup(self):
        """Applies the correct talkgroup or scan list based on the current channel in the curses UI."""
        
        # First, check if the current channel index is valid
        if self.currentFile.current_tg_index is None:
            print("[ERROR] Current channel index not set")
            return

        selected_channel = self.currentFile.get_channel_by_number(self.currentFile.current_tg_index)
        if not selected_channel:
            print("[ERROR] Selected channel not found")
            return

        # Get the list of Talkgroup IDs (TGIDs) for the whitelist
        wlist = selected_channel.get('tgid', [])  # Safely get 'tgid' with a default empty list if not found

        # Switch the talkgroup using the retrieved list
        self.op25.switchGroup(wlist=wlist)  # Ensure switchGroup is expecting a keyword argument

        # Update the UI to reflect the selected talkgroup
        self.update_display()
        
        # Speak the channel name if speech is enabled
        if self.speech_on:
            self.speech.speak(selected_channel["name"])

    def select_talkgroup(self):
        """Handles user selecting a talkgroup from the menu and applies it in the curses UI."""
        
        # Hide the talkgroup menu after selection
        self.toggle_talkgroup_menu()

        self.current_tg_text = "LOADING..."
        self.current_zone_text = "ZONE"

        time.sleep(2)  # TODO: Implement threading; for now allows time to change status

        # Ensure current zone index is within bounds
        if self.currentFile.current_zone_index >= len(self.currentFile.zone_names):
            print("[ERROR] Current zone index out of bounds")
            return
        
        current_zone = self.currentFile.zone_names[self.currentFile.current_zone_index]
        talkgroup_name = self.talkgroup_list[self.selected_talkgroup]  # Retrieve selected talkgroup name

        # Attempt to find the selected channel from JSON using the current zone and talkgroup name
        selected_channel = next(
            (ch for ch in self.currentFile.get_channels_by_zone(current_zone) if ch["name"] == talkgroup_name),
            None
        )

        if not selected_channel:
            print("[ERROR] Selected talkgroup not found in JSON")
            return  # Exit function if selection is invalid
  
        self.current_channel_text = f"{selected_channel["name"]} ({selected_channel["channel_number"]})"
        # Update the currently selected talkgroup index
        self.currentFile.current_tg_index = selected_channel["channel_number"]

        # Update the display and change to the new talkgroup if the index is valid
        self.update_display()  # Refresh UI
        self.change_talkgroup()  # Apply the new talkgroup settings

    def close_app(self):
        """Closes the curses application."""
        print("Closing application...")
        if self.speech_on:
            self.speech.stop()  # Stop speech engine before exit
        self.op25.stop()  # TODO: Send request to OP25 to stop gracefully.
        exit()

    def channel_up(self):
        """Moves to the next channel using FileObject's methods in curses UI."""
        current_channel_number = self.currentFile.current_tg_index
        next_channel = self.currentFile.get_channel_by_number(current_channel_number + 1)

        if next_channel:
            self.currentFile.current_tg_index = next_channel["channel_number"]
        else:
            # If no next channel, loop back to the first channel
            first_channel = self.currentFile.get_channels_by_zone(self.currentFile.zone_names[self.currentFile.current_zone_index])
            self.currentFile.current_tg_index = first_channel[0]["channel_number"] if first_channel else 0

        self.update_display()
        self.change_talkgroup()

    def channel_down(self):
        """Moves to the previous channel using FileObject's methods in curses UI."""
        current_channel_number = self.currentFile.current_tg_index
        previous_channel = self.currentFile.get_previous_channel(current_channel_number)

        if previous_channel:
            self.currentFile.current_tg_index = previous_channel["channel_number"]
        else:
            # If no previous channel, loop to the last channel in the zone
            last_channel = self.currentFile.get_channels_by_zone(self.currentFile.zone_names[self.currentFile.current_zone_index])
            self.currentFile.current_tg_index = last_channel[-1]["channel_number"] if last_channel else 0

        self.update_display()
        self.change_talkgroup()

    def zone_up(self):
        """Moves to the next zone, loops back if at the last zone in curses UI."""
        next_zone = self.currentFile.get_next_zone(self.currentFile.current_zone_index)
        if next_zone:
            self.currentFile.current_zone_index = self.currentFile.zone_names.index(next_zone)
            self.load_first_channel()

            if self.currentFile.current_tg_index is not None:
                self.update_display()
                current_zone = self.currentFile.zone_names[self.currentFile.current_zone_index]
                first_channel = self.currentFile.get_channel_by_number(self.currentFile.current_tg_index)
                if self.speech_on:
                    self.speech.speak(f"{current_zone} - {first_channel['name'] if first_channel else 'No Channels'}")

            self.change_talkgroup()

    def zone_down(self):
        """Moves to the previous zone, loops to the last if at the first in curses UI."""
        prev_zone = self.currentFile.get_previous_zone(self.currentFile.current_zone_index)
        if prev_zone:
            self.currentFile.current_zone_index = self.currentFile.zone_names.index(prev_zone)
            self.load_first_channel()

            if self.currentFile.current_tg_index is not None:
                self.update_display()
                current_zone = self.currentFile.zone_names[self.currentFile.current_zone_index]
                first_channel = self.currentFile.get_channel_by_number(self.currentFile.current_tg_index)
                if self.speech_on:
                    self.speech.speak(f"{current_zone} - {first_channel['name'] if first_channel else 'No Channels'}")

            self.change_talkgroup()

    def update_display(self):
        """Forces a UI refresh by calling draw_ui()."""
        self.draw_ui()
        self.stdscr.refresh()

    def open_talkgroup_menu(self):
        """Opens the talkgroup menu for the current zone in the curses UI."""
        current_zone = self.currentFile.zone_names[self.currentFile.current_zone_index]
        self.talkgroup_list = [channel["name"] for channel in self.currentFile.get_channels_by_zone(current_zone)]

        if not self.talkgroup_list:
            print("[WARNING] No channels available in the current zone.")
        else:
            self.isMenuActive = True  # Ensure the menu becomes visible
            self.selected_talkgroup = 0  # Reset selection to first item

        self.update_display()  # Refresh UI to display the talkgroup menu

    def toggle_talkgroup_menu(self):
        """Toggles the talkgroup menu visibility in the curses UI."""
        self.isMenuActive = not self.isMenuActive  # Toggle menu state
        self.update_display()  # Refresh UI to show or hide the talkgroup menu

    def toggle_mute(self):
        """Toggles mute status and updates the UI."""
        self.sound_status = "󰕾" if self.sound_status == "󰖁" else "󰖁"  # Toggle between mute/unmute icons
        self.update_display()
        print("[DEBUG] Mute toggled")

    def confirm_tgid_input(self):
        """Applies the entered TGID, updates the zone, and changes the channel in curses."""
        if not self.current_tg_text.isdigit():
            print("[ERROR] No valid TGID entered.")
            return

        tgid = int(self.current_tg_text)

        # Find channel with matching TGID
        found_channel = None
        found_zone = None

        for zone_name in self.currentFile.zone_names:
            channels = self.currentFile.get_channels_by_zone(zone_name)
            for channel in channels:
                if "channel_number" in channel and channel["channel_number"] == tgid:
                    found_channel = channel
                    found_zone = zone_name
                    break
            if found_channel:
                break  # Stop searching if found

        if not found_channel or not found_zone:
            print(f"[ERROR] TGID {tgid} not found in any zone.")
            return

        # Update to the correct zone and channel
        self.currentFile.current_zone_index = self.currentFile.zone_names.index(found_zone)
        self.currentFile.current_tg_index = found_channel["channel_number"]

        self.update_display()
        self.change_talkgroup()

        if self.speech_on:
            self.speech.speak(f"Channel {tgid} in {found_zone}")

    def clear_keypad_input(self):
        """Clears the TGID input in the curses UI."""
        self.update_current_tg_text("")

    def start_ir_listener(self):
        """Runs the IR listener in a separate thread to prevent blocking the curses UI."""
        # TODO: Implement threading and IR Listener
        # ir_thread = threading.Thread(target=self.ir_handler.listen, daemon=True)
        # ir_thread.start()
        pass

    def keypad_input(self, digit):
        """Handles numeric button input for direct TGID entry with TV-style shifting in curses."""
        current_text = self.current_tg_text if self.current_tg_text.isdigit() else ""

        if len(current_text) >= 3:
            current_text = current_text[1:]  # Remove the leftmost digit (shift behavior)

        if self.speech_on:
            self.speech.speak(f"{digit}")

        new_text = current_text + digit
        self.update_current_tg_text(new_text)  # Update the displayed TGID in curses

    def update_display(self):
        self.current_zone_index = self.currentFile.current_tg_index
    
        self.current_channel_text = f"[Channel Name] ()"
        self.draw_ui()
    
    def writeTextAligned(self, yStart: int, windowWidth, prefixText, suffixText, prefixColor: int, suffixColor: int, manualWidth=-1):
        """Writes aligned text at a specific position on the screen."""

        # Ensure suffixText has a default value to prevent issues
        suffixText = suffixText if suffixText else "N/A"

        # Combine both parts to calculate correct centering
        full_text = f"{prefixText} {suffixText}"
        
        # Ensure proper centering
        if manualWidth == -1:
            x = (windowWidth - len(full_text)) // 2
        else:
            x = (windowWidth - manualWidth) // 2

        # ✅ Prevent writing out of bounds
        if x < 0 or yStart < 0 or x + len(full_text) >= windowWidth:
            return  # Avoid writing out of bounds

        # Draw Prefix Text (Colored)
        try:
            self.stdscr.attron(curses.color_pair(prefixColor) | curses.A_BOLD)
            self.stdscr.addstr(yStart, x, prefixText)
            self.stdscr.attroff(curses.color_pair(prefixColor) | curses.A_BOLD)

            # Draw Suffix Text (Colored) - Position it AFTER the prefix correctly
            self.stdscr.attron(curses.color_pair(suffixColor) | curses.A_BOLD)
            self.stdscr.addstr(yStart, x + len(prefixText) + 1, suffixText)  # +1 for spacing
            self.stdscr.attroff(curses.color_pair(suffixColor) | curses.A_BOLD)

        except curses.error as e:
            self.log.error(f"[CURSES ERROR] {e}")  # ✅ Log instead of crashing

    def btn(self,x,y,label, offset=0):
       
        attr = curses.A_REVERSE if self.selected_button == self.btn_index else curses.A_NORMAL | curses.A_BOLD
        text = f"[{label.upper()}]"
        self.stdscr.addstr(y, x, text, attr)

        self.btn_index += 1
        return   
    def writeTextAligned(self, yStart:int, windowWidth, prefixText, suffixText, prefixColor:int, suffixColor:int, manualWidth = -1):
        # Combine both parts to calculate correct centering
        full_text = f"{prefixText} {suffixText}"

        if (manualWidth == -1):
            x = (windowWidth - len(full_text)) // 2  # Proper centering
        else:
            x = (windowWidth - manualWidth) // 2  # Proper centering

        # Draw Prefix Text (Colored)
        self.stdscr.attron(curses.color_pair(prefixColor) | curses.A_BOLD)
        self.stdscr.addstr(yStart, x, prefixText)
        self.stdscr.attroff(curses.color_pair(prefixColor) | curses.A_BOLD)

        # Draw Suffix Text (Colored) - Position it AFTER the prefix correctly
        self.stdscr.attron(curses.color_pair(suffixColor) | curses.A_BOLD)
        self.stdscr.addstr(yStart, x + len(prefixText) + 1, suffixText)  # +1 for spacing
        self.stdscr.attroff(curses.color_pair(suffixColor) | curses.A_BOLD)

    def getHighestCenterAlignedLength(self, list=[]):
        lengths = []
        for i in list:
           # Calculate Length
            length = len(f"{i}") + 1
            lengths.append(length)

        return max(lengths) if lengths else 0  # Return max or default

    def draw_ui(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()

        # Title Bar (White from edge to edge with right-aligned status icons)
        title = "OP25 Scanner"
        status_text = f" {self.connection_status} {self.progress_status} {self.sound_status} "
        title_x = (w - len(title)) // 2
        status_x = w - len(status_text) - 1
        
        # self.stdscr.attron(curses.color_pair(1))
        # self.stdscr.addstr(0, 0, " " * w)  # Fill the entire row with spaces
        # self.stdscr.addstr(0, max(0, title_x), title, curses.A_BOLD | curses.A_REVERSE)
        # self.stdscr.addstr(0, max(0, status_x), status_text, curses.A_BOLD | curses.A_REVERSE)
        # self.stdscr.attroff(curses.color_pair(1))

        if w < 80:
            self.stdscr.addstr(2, 2, "Terminal too small! Resize and restart.", curses.A_BOLD)
            self.stdscr.refresh()
            return
        
        vals = []
        # Zone Selection (Centered)
        y = 3
        vals.append(f"[ZN] {self.zone_names[self.current_zone_index]}")
        vals.append(f"[CH] {self.current_channel_text}")
        vals.append(f"[TG] {self.current_tg_text}")
        manual = self.getHighestCenterAlignedLength(vals)

        
        # WRITE MENU BUTTONS
        self.btn_index = 0  # ✅ Reset indexing before drawing buttons
        end_x = w - 8
        

        self.writeTextAligned(6, w, "[ZN]", self.zone_names[self.current_zone_index], 3 , 4, manual )
        self.writeTextAligned(9, w, "[CH]", self.current_channel_text, 3 , 4, manual )
        self.writeTextAligned(12, w, "[TG]", self.current_tg_text, 3 , 4, manual)

        self.btn(1, 6, "ZN ▲")          # 1
        self.btn(1, 9, "ZN ▼")          # 2
        self.btn(1, 12, "MENU")         # 3
        self.btn(1, 15, "EXIT")         # 4

        self.btn(end_x, 6, "CH ▲")      # 5
        self.btn(end_x, 9 , "CH ▼")     # 6
        self.btn(end_x, 12, "LOCK")     # 7


        self.stdscr.refresh()

    def handle_input(self):
        key = self.stdscr.getch()
        
        # Define button layout (indexed based on draw_ui positions)
        left_buttons = [0, 1, 2, 3]  # Zn ▲, Zn ▼, Menu, Exit
        right_buttons = [4, 5, 6]  # Ch ▲, Ch ▼, Lock

        if key == curses.KEY_UP:
            if self.selected_button in left_buttons:
                index = left_buttons.index(self.selected_button)
                self.selected_button = left_buttons[(index - 1) % len(left_buttons)]
            elif self.selected_button in right_buttons:
                index = right_buttons.index(self.selected_button)
                self.selected_button = right_buttons[(index - 1) % len(right_buttons)]

        elif key == curses.KEY_DOWN:
            if self.selected_button in left_buttons:
                index = left_buttons.index(self.selected_button)
                self.selected_button = left_buttons[(index + 1) % len(left_buttons)]
            elif self.selected_button in right_buttons:
                index = right_buttons.index(self.selected_button)
                self.selected_button = right_buttons[(index + 1) % len(right_buttons)]

        elif key == curses.KEY_LEFT:
            if self.selected_button in right_buttons:
                index = right_buttons.index(self.selected_button)
                if index < len(left_buttons):  # Ensure the index exists in left_buttons
                    self.selected_button = left_buttons[index]

        elif key == curses.KEY_RIGHT:
            if self.selected_button in left_buttons:
                index = left_buttons.index(self.selected_button)
                if index < len(right_buttons):  # Ensure the index exists in right_buttons
                    self.selected_button = right_buttons[index]

        elif key == ord('\n'):  # Enter key
            self.handle_button_action()
        
        elif key == ord('x') or key == ord('X'):  # Exit
            exit()

        self.update_display()

    def handle_button_action(self):
        btn = self.buttons[self.selected_button]
        if btn[1].strip() == "EXIT":
            exit()
    
    def run(self):
        """Starts the curses UI loop."""
        self.stdscr.nodelay(False)
        self.stdscr.keypad(True)
        while True:
            self.update_display()
            self.handle_input()

def main(stdscr):
    """Initialize and start the Curses UI."""
    ui = CursesUI(stdscr)  
    ui.run()  


import traceback

if __name__ == "__main__":
    try:
        curses.wrapper(main)  # Properly initializes and runs the UI
    except Exception as e:
        print(f"[ERROR] {e}")
        traceback.print_exc()  # ✅ This prints a full traceback for debugging
