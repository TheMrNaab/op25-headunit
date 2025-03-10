#import test
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QListWidget
)
from PyQt5.QtCore import Qt

import subprocess
import time
import os

zones = {
    "Fire": {
        "WC FD ALERT": [46949, 70],
        "Fire Dispatch": [101, 71],
        "FD OPS 1": [46800, 1],
        "FD OPS 2": [46801, 2],
        "FD OPS 3": [46802, 3],
        "FD OPS 4": [46803, 4],
        "FD OPS 5": [46804, 5],
        "FD OPS 6": [46805, 6],
        "FD OPS 7": [46806, 7],
        "FD OPS 8": [46807, 8],
        "FD OPS 9": [46808, 9],
        "FD OPS 10": [46809, 10],
        "FD OPS 11": [46810, 11],
        "FD OPS 12": [46811, 12],
        "PS TAC 13": [46812, 13],
        "PS TAC 14": [46813, 14],
        "PS TAC 15": [46814, 15],
        "PS TAC 16": [46815, 16],
        "PS TAC 17": [46816, 17],
        "PS TAC 18": [46817, 18],
        "PS TAC 19": [46818, 19],
        "PS TAC 20": [46819, 20],
        "PS TAC 21": [46820, 21],
        "PS TAC 22": [46821, 22],
        "PS TAC 23": [46822, 23],
        "PS TAC 24": [46823, 24],
        "PS TAC 25": [46824, 25],
        "PS TAC 26": [46825, 26],
        "PS TAC 27": [46826, 27],
        "PS TAC 28": [46827, 28],
        "PS TAC 29": [46828, 29],
        "PS TAC 30": [46829, 30],
        "PS TAC 31": [46830, 31],
        "PS TAC 32": [46831, 32],
        "PS TAC 33": [46832, 33],
        "PS TAC 34": [46833, 34],
        "PS TAC 35": [46834, 35],
        "PS TAC 36": [46835, 36],
        "PS TAC 37": [46836, 37],
        "PS TAC 38": [46837, 38],
        "PS TAC 39": [46838, 39]
    },
    "EMS": {
        "EMS Dispatch": [201, 100]
    },
    "Police": {
        "RPD NE": [301, 43]
    }
}

class ScannerUI(QWidget):


    def __init__(self):
        super().__init__()
        print("--")
        self.current_zone_index = 0
        self.current_tg_index = 0
        self.zone_names = list(zones.keys())
        self.menu_active = False  # Tracks if talkgroup menu is active

        if not hasattr(self, 'op25') or self.op25 is None:
            print("[DEBUG] Creating OP25Controller instance")
            self.op25 = OP25Controller()
        else:
            print("[DEBUG] OP25Controller instance already exists")

        # Start OP25 in the background
        self.op25.start()

        time.sleep(5)  # Give OP25 some time to initialize
        self.initUI()

    def stop_op25(self):
        """Gracefully stop the OP25 process, close the application, and exit Openbox."""
        try:
            # Stop OP25 if it's running
            if hasattr(self, 'op25_process') and self.op25 and self.op25.poll() is None:
                print("Stopping OP25...")
                self.op25.terminate()  # Send termination signal
                try:
                    self.op25.wait(timeout=5)  # Wait for it to exit gracefully
                except subprocess.TimeoutExpired:
                    print("OP25 did not terminate in time. Forcing shutdown.")
                    self.op25.kill()  # Forcefully stop it

            print("Exiting application.")
            self.close()  # Close the application window

            # Exit Openbox and return to the console
            print("Exiting Openbox...")
            subprocess.run(["openbox", "--exit"], check=True)

        except Exception as e:
            print(f"Error during shutdown: {e}")


    def initUI(self):
        self.setWindowTitle("SDR-Trunk Scanner")
        self.setGeometry(100, 100, 600, 400)  # Window size
        self.setStyleSheet("background-color: black;")  # Set background to black

        # ZONE Controls
        self.zone_label = QLabel(self.zone_names[self.current_zone_index], self)
        self.zone_label.setAlignment(Qt.AlignCenter)
        self.zone_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")

        self.zone_up_btn = self.create_button("ZONE ▲")
        self.zone_up_btn.clicked.connect(self.zone_up)

        self.zone_down_btn = self.create_button("ZONE ▼")
        self.zone_down_btn.clicked.connect(self.zone_down)

        # Current Talkgroup Display
        self.tg_label = QLabel(self.get_current_tg_name(), self)
        self.tg_label.setAlignment(Qt.AlignCenter)
        self.tg_label.setStyleSheet("""
            background-color: #d4ff00;
            color: black;
            font-size: 24px;
            font-weight: bold;
            border: 2px solid #555;
            padding: 10px;
        """)

        # Talkgroup List
        self.tg_list = QListWidget(self)
        self.tg_list.hide()
        self.tg_list.setStyleSheet("""
            background-color: #d4ff00;
            color: black;
            font-size: 18px;
            border: 2px solid #555;
        """)
        self.tg_list.itemClicked.connect(self.select_talkgroup)

        # CHANNEL Controls
        self.ch_up_btn = self.create_button("CH ▲", "green")
        self.ch_up_btn.clicked.connect(self.channel_up)

        self.ch_down_btn = self.create_button("CH ▼", "red")
        self.ch_down_btn.clicked.connect(self.channel_down)

        # Function Buttons
        self.func1_btn = self.create_button("GROUPS")
        self.func1_btn.clicked.connect(self.toggle_talkgroup_menu)

        self.func2_btn = self.create_button("MUTE")

        # Menu Buttons
        self.menu_btn = self.create_button("MENU")
        self.back_btn = self.create_button("BACK")
        self.exit_btn = self.create_button("EXIT")
        self.exit_btn.clicked.connect(self.stop_op25)


        # Layouts
        zone_layout = QHBoxLayout()
        zone_layout.addWidget(self.zone_up_btn)
        zone_layout.addWidget(self.zone_label)
        zone_layout.addWidget(self.zone_down_btn)

        talkgroup_layout = QVBoxLayout()
        talkgroup_layout.addWidget(self.tg_label)
        talkgroup_layout.addWidget(self.tg_list)


        
        channel_layout = QHBoxLayout()
        channel_layout.addWidget(self.ch_up_btn)
        channel_layout.addWidget(self.func1_btn)
        channel_layout.addWidget(self.func2_btn)
        channel_layout.addWidget(self.ch_down_btn)

        menu_layout = QHBoxLayout()
        menu_layout.addWidget(self.menu_btn)
        menu_layout.addWidget(self.back_btn)
        menu_layout.addWidget(self.exit_btn)

        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(zone_layout)
        main_layout.addLayout(talkgroup_layout)
        main_layout.addLayout(channel_layout)
        main_layout.addLayout(menu_layout)

        self.setLayout(main_layout)
        
    def switchGroup(self, grp):
        try:
            grp = int(grp)  # Ensure the input is numeric
            command = f"W{grp}\n"
            self.op25.stdin.write(command)
            self.op25.stdin.flush()
            #print(f"Switched to talkgroup {grp}.")
        except ValueError:
            print("Invalid input. Enter a numeric talkgroup.")

    def create_button(self, text, color=None):
        """Creates a Motorola-style button"""
        button = QPushButton(text)
        base_style = """
            QPushButton {
                background-color: #444;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #666;
                padding: 8px;
            }
            QPushButton:pressed {
                background-color: #666;
            }
        """
        if color == "green":
            button.setStyleSheet(base_style.replace("#444", "#008000"))
        elif color == "red":
            button.setStyleSheet(base_style.replace("#444", "#800000"))
        else:
            button.setStyleSheet(base_style)

        return button

    def get_current_tg_name(self):
        """Returns the current talkgroup name based on indices."""
        current_zone = self.zone_names[self.current_zone_index]
        return list(zones[current_zone].keys())[self.current_tg_index]

    def get_current_tg_id(self):
        """Returns the current talkgroup ID based on indices."""
        current_zone = self.zone_names[self.current_zone_index]
        tg_name = self.get_current_tg_name()
        return zones[current_zone][tg_name]

    def zone_up(self):
        if self.current_zone_index < len(self.zone_names) - 1:
            self.current_zone_index += 1
            self.current_tg_index = 0
            self.update_display()

    def zone_down(self):
        if self.current_zone_index > 0:
            self.current_zone_index -= 1
            self.current_tg_index = 0
            self.update_display()

    def channel_up(self):
        current_zone = self.zone_names[self.current_zone_index]
        if self.current_tg_index < len(zones[current_zone]) - 1:
            self.current_tg_index += 1
            self.update_display()

    def channel_down(self):
        if self.current_tg_index > 0:
            self.current_tg_index -= 1
            self.update_display()

    def toggle_talkgroup_menu(self):
        if self.menu_active:
            self.tg_list.hide()
            self.tg_label.show()
            self.menu_active = False
        else:
            self.menu_active = True
            self.open_talkgroup_menu()

    def open_talkgroup_menu(self):
        current_zone = self.zone_names[self.current_zone_index]
        self.tg_list.clear()
        self.tg_list.addItems(zones[current_zone].keys())
        self.tg_label.hide()
        self.tg_list.show()

    def select_talkgroup(self, item):
        current_zone = self.zone_names[self.current_zone_index]
        talkgroup_name = item.text()

        if talkgroup_name in zones[current_zone]:
            self.current_tg_index = list(zones[current_zone].keys()).index(talkgroup_name)
            self.update_display()
            self.toggle_talkgroup_menu()

            # Send API request to filter the selected talkgroup
            tg_id = zones[current_zone][talkgroup_name][0]
            self.op25.switchGroup(tg_id)

    def set_op25_talkgroup(self, tg_id):
        print(f"Sending talkgroup change request: {tg_id}")
        self.op25.switchGroup(f"{tg_id}")

    def update_display(self):
        self.zone_label.setText(self.zone_names[self.current_zone_index])
        self.tg_label.setText(self.get_current_tg_name())

class OP25Controller:
    def __init__(self):  # Fixed method name
        # Define OP25 executable path
        rx_script = os.path.expanduser("~/op25/op25/gr-op25_repeater/apps/rx.py")

        # Start OP25 in the background
        try:
            self.op25_process = subprocess.Popen(
                [
                    "python3", rx_script, "--args", "rtl=0", "-N", "LNA:35",
                    "-S", "2500000", "-q", "0", "-T", "trunk.tsv", "-V", "-2", "-U"
                ],
                cwd=os.path.dirname(rx_script),  # Ensure the script runs in the correct directory
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,  # Suppress stdout to avoid triggering gnuplot
                stderr=subprocess.DEVNULL,  # Suppress errors to prevent gnuplot launch
                text=True
            )

            time.sleep(5)  # Give OP25 time to initialize

        except Exception as e:
            print(f"Failed to start OP25: {e}")
            exit(1)

    def switchGroup(self, grp):
        """ Switches OP25 to a new talkgroup. """
        if self.op25_process.poll() is not None:
            print("Error: OP25 is not running.")
            return
        try:
            grp = int(grp)  # Ensure numeric input
            command = f"W {grp}\n"  # OP25 uses 'w' to change talkgroup
            print(command)
            self.op25_process.stdin.write(command)
            self.op25_process.stdin.flush()
        except ValueError:
            print("Invalid input. Enter a numeric talkgroup.")

    def start(self):
        # Check if the process is still running
        if self.op25_process.poll() is None:
            print("OP25 started successfully!")
        else:
            print("OP25 failed to start.")
            error_message = self.op25_process.stderr.read()
            print("Error Output:\n", error_message)
            self.op25_process.terminate()  # Ensure the process does not hang
            exit(1)

    def stop(self):
        if self.op25_process and self.op25_process.poll() is None:
            print("Stopping OP25...")
            self.op25_process.terminate()
            self.op25_process.wait()
            print("OP25 stopped successfully.")
        else:
            print("OP25 is not running.")

    def restart(self):
        print("Restarting OP25...")
        self.stop()
        self.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ScannerUI()
    ex.show()
    sys.exit(app.exec_())


