import os
import sys
from file_object import FileObject
from control import OP25Controller
from PyQt5.QtWidgets import ( # type: ignore
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QListWidget
)
from PyQt5.QtCore import Qt # type: ignore



class ScannerUI(QWidget):

    def __init__(self):
        super().__init__()
        print("--")

        self.currentFile = FileObject()
         
     
        self.isMenuActive = False  # Tracks if talkgroup menu is active

        if not hasattr(self, 'op25') or self.op25 is None:
            print("[DEBUG] Creating OP25Controller instance")
            self.op25 = OP25Controller()
            
        else:
            print("[DEBUG] OP25Controller instance already exists")

        # Start OP25 in the background
        self.op25.start()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("SDR-Trunk Scanner")
        self.setGeometry(100, 100, 600, 400)  # Window size
        self.setStyleSheet("background-color: black;")  # Set background to black

        # ZONE Controls
        self.zone_label = QLabel(self.currentFile.zone_names[self.currentFile.current_zone_index], self)
        self.zone_label.setAlignment(Qt.AlignCenter)
        self.zone_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")

        self.zone_up_btn = self.create_button("ZONE ▲")
        self.zone_up_btn.clicked.connect(self.zone_up)

        self.zone_down_btn = self.create_button("ZONE ▼")
        self.zone_down_btn.clicked.connect(self.zone_down)

        # Current Talkgroup Display
        self.tg_label = QLabel("", self)  # Placeholder label
        self.update_display()  # Call display update after UI initialization
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
        self.exit_btn.clicked.connect(self.close_app)


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
        
    def load_stylesheet(self):
        """Loads styles from an external QSS file."""
        stylesheet_path = "styles.qss"  # Adjust path if needed
        if os.path.exists(stylesheet_path):
            with open(stylesheet_path, "r") as file:
                self.setStyleSheet(file.read())
        else:
            print(f"[WARNING] Stylesheet '{stylesheet_path}' not found.")

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

    def zone_up(self):
        """Moves to the next zone, loops back if at the last zone."""
        next_zone = self.currentFile.get_next_zone(self.currentFile.current_zone_index)
        if next_zone:
            self.currentFile.current_zone_index = self.currentFile.zone_names.index(next_zone)
            self.load_first_channel()  # Load first channel of the new zone
            self.update_display()

    def zone_down(self):
        """Moves to the previous zone, loops to the last if at the first."""
        prev_zone = self.currentFile.get_previous_zone(self.currentFile.current_zone_index)
        if prev_zone:
            self.currentFile.current_zone_index = self.currentFile.zone_names.index(prev_zone)
            self.load_first_channel()  # Load first channel of the new zone
            self.update_display()

    def channel_up(self):
        """Moves to the next channel using FileObject's methods."""
        current_channel_number = self.currentFile.current_tg_index
        next_channel = self.currentFile.get_channel_by_number(current_channel_number + 1)

        if next_channel:
            self.currentFile.current_tg_index = next_channel["channel_number"]
        else:
            # If no next channel, loop back to the first channel
            first_channel = self.currentFile.get_channels_by_zone(self.currentFile.zone_names[self.currentFile.current_zone_index])
            self.currentFile.current_tg_index = first_channel[0]["channel_number"] if first_channel else 0

        self.update_display()

    def channel_down(self):
        """Moves to the previous channel using FileObject's methods."""
        current_channel_number = self.currentFile.current_tg_index
        previous_channel = self.currentFile.get_previous_channel(current_channel_number)

        if previous_channel:
            self.currentFile.current_tg_index = previous_channel["channel_number"]
        else:
            # If no previous channel, loop to the last channel in the zone
            last_channel = self.currentFile.get_channels_by_zone(self.currentFile.zone_names[self.currentFile.current_zone_index])
            self.currentFile.current_tg_index = last_channel[-1]["channel_number"] if last_channel else 0

        self.update_display()

    def load_first_channel(self):
        """Loads the first channel of the current zone."""
        first_channel = self.currentFile.get_channels_by_zone(
            self.currentFile.zone_names[self.currentFile.current_zone_index]
        )
        self.currentFile.current_tg_index = first_channel[0]["channel_number"] if first_channel else 0
 
    def toggle_talkgroup_menu(self):
        """Toggles the talkgroup menu visibility."""
        if self.isMenuActive:
            self.tg_list.hide()
            self.tg_label.show()
            self.isMenuActive = False
        else:
            self.isMenuActive = True
            self.open_talkgroup_menu()

    def open_talkgroup_menu(self):
        """Opens the talkgroup menu for the current zone."""
        current_zone = self.currentFile.zone_names[self.currentFile.current_zone_index]
        self.tg_list.clear()

        # Retrieve channel names from the file object
        channel_list = [channel["name"] for channel in self.currentFile.get_channels_by_zone(current_zone)]
        
        self.tg_list.addItems(channel_list)
        self.tg_label.hide()
        self.tg_list.show()

    def select_talkgroup(self, item):
        """Handles user selecting a talkgroup from the menu."""
        current_zone = self.currentFile.zone_names[self.currentFile.current_zone_index]
        talkgroup_name = item.text()

        # Find the selected channel from JSON
        selected_channel = next(
            (ch for ch in self.currentFile.get_channels_by_zone(current_zone) if ch["name"] == talkgroup_name),
            None
        )

        if not selected_channel:
            print("@ERROR: Selected talkgroup not found in JSON")
            return  # Exit function if selection is invalid

        # Update the currently selected talkgroup
        self.currentFile.current_tg_index = selected_channel["channel_number"]
        self.update_display()
        self.toggle_talkgroup_menu()

        if selected_channel["type"] == "talkgroup":
            self.op25.switchGroup(str(selected_channel["tgid"]))  # Send single TGID
        elif selected_channel["type"].lower() == "scan":
            if isinstance(selected_channel["tgid"], list):  # Ensure it's a list
                print("@254:", selected_channel["tgid"])
                self.op25.switchGroup(",".join(map(str, selected_channel["tgid"])))  # Send comma-separated TGIDs
            else:
                print("@ERROR: Expected list for scan mode, got", type(selected_channel["tgid"])) 

    def update_display(self):
        """Updates the display with the current zone and channel information."""
        current_zone = self.currentFile.zone_names[self.currentFile.current_zone_index]
        self.zone_label.setText(current_zone)  # Update zone display

        # Ensure the channel exists
        current_channel = self.currentFile.get_channel_by_number(self.currentFile.current_tg_index)

        if current_channel:
            display_text = f"{current_channel['channel_number']}: {current_channel['name']}"
            if current_channel["type"] == "scan":
                display_text += " (Scan)"
            self.tg_label.setText(display_text)
        else:
            self.tg_label.setText("No Channels")

    def close_app(self):
        """Closes the application."""
        print("Closing application...")
        self.close()
            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ScannerUI()
    ex.show()
    sys.exit(app.exec_())