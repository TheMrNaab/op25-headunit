import sys
import os
import re
import time
import csv
from enum import Enum
from PySide6.QtCore import QThread, Signal

# PySide6 Core Imports
from PySide6.QtCore import (
    QThread, Signal, QTimer, QMetaObject, QRect, QSize, QCoreApplication
)

# PySide6 GUI Imports
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLCDNumber,
    QVBoxLayout, QHBoxLayout, QGridLayout, QListWidget, QSpacerItem, QSizePolicy, QLayout
)

# Project-Specific Imports
from tts import SpeechEngine
from file_object import FileObject
from file_object import MyConfig
from modules.OP25_Controller import OP25Controller
from customWidgets import BlinkingLabel

class ScanListWorker(QThread):
    signal_complete = Signal()

    def __init__(self, op25_instance, tgids):
        super().__init__()
        self.op25 = op25_instance
        self.tgids = tgids
        self.running = False  # ✅ Prevent multiple threads

    def run(self):
        """Process scan TGIDs in a separate thread."""
        if self.running:
            self.op25.logger.info("[DEBUG] ScanListWorker is already running. Skipping duplicate execution.")
            return

        self.running = True
        print(f"[DEBUG] Processing {len(self.tgids)} TGIDs in scan mode")
        try:
            self.op25.update_scan_list(self.tgids)
        except Exception as e:
            self.op25.logger.info(f"[ERROR] Failed to update scan list: {e}")
        finally:
            self.running = False
            self.signal_complete.emit()  # Notify UI even if there is an error

class OP25InitWorker(QThread):
    """Worker thread for initializing OP25 without blocking the UI."""
    signal_initialized = Signal()  

    def __init__(self, op25_instance):
        super().__init__()
        self.op25 = op25_instance

    def run(self):
        self.op25.start()
        self.signal_initialized.emit()  

class ChangeTalkgroupWorker(QThread):
    """Worker thread for changing the talkgroup without blocking the UI."""
    signal_initialized = Signal()

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.op25 = main_window.op25 
        self.running = False  

    def run(self):
        self.main_window.setDisabled(True)
        QApplication.processEvents()
        if self.running:
            print("[DEBUG] ChangeTalkgroupWorker is already running. Skipping execution.")
            return

        self.running = True
        print("[INFO] Change Talkgroup Thread Started")

        if self.main_window.currentFile.current_tg_index is None:
            print("[ERROR] Current channel index not set")
            self.running = False
            return

        selected_channel = self.main_window.currentFile.get_channel_by_number(self.main_window.currentFile.current_tg_index)
        if not selected_channel:
            print("[ERROR] Selected channel not found")
            self.running = False
            return

        wlist = selected_channel.get('tgid', [])
        print("Line 97")
        
        try:
            self.op25.switchGroup(wlist=wlist)
        except Exception as e:
            print(f"[ERROR] Failed to switch talkgroup: {e}")
            self.running = False
            return  # Exit if switching fails

        if self.main_window.speech_on:
            self.main_window.speech.speak(selected_channel["name"])

        self.running = False
        self.signal_initialized.emit()
        self.main_window.setDisabled(False)
        QApplication.processEvents()

    def cleanup_before_exit(self):
        """Cleanup actions before exiting the application."""
        print("[INFO] Stopping all workers...")

        if hasattr(self, "op25") and self.op25:
            self.op25.stop()  # Ensure OP25 stops properly

        if hasattr(self, "logMonitor") and self.logMonitor:
            self.logMonitor.stop()  # ✅ Stop log monitor thread
            self.logMonitor.wait()  # ✅ Wait for clean exit

        if hasattr(self, "ChangeTalkgroupWorker") and self.ChangeTalkgroupWorker:
            if self.ChangeTalkgroupWorker.isRunning():
                self.ChangeTalkgroupWorker.quit()
                self.ChangeTalkgroupWorker.wait()
        
        self.close()

class MonitorLogFileWorker(QThread):
    """Worker thread for monitoring the OP25 log file without blocking the UI."""
    signal_tg_update = Signal(str)  # Signal to send back the TG number

    def __init__(self, op25_instance, stderr_path):
        super().__init__()
        self.stderr_path = stderr_path
        self.op25 = op25_instance
        self.tg_dict = {}
        self.running = True 
        self.load_csv(self.op25.tgroups_file)

    def load_csv(self, file):
        """Loads the talkgroup mappings from a CSV file into a dictionary."""
        try:
            with open(file, mode='r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if len(row) >= 2:
                        tg_id, alpha_tag = row[0].strip(), row[1].strip()
                        if tg_id.isdigit():  # Ensure first column is a number
                            self.tg_dict[tg_id] = alpha_tag
        except FileNotFoundError:
            print(f"[ERROR] CSV file '{file}' not found.")
        except Exception as e:
            print(f"[ERROR] Failed to load CSV: {e}")

    def extract_tg_number(self, line):
        """Extracts the TG number from a voice update line."""
        match = re.search(r'voice update:.*tg\((\d+)\)', line)
        return match.group(1) if match else None

    def run(self):
        """Monitors the log file and emits TG number when a new voice update appears."""
        try:
            with open(self.stderr_path, "r") as file:
                file.seek(0, 2)  # Move to the end of the file

                while self.running:
                    line = file.readline()
                    if not line:
                        time.sleep(0.1)  # ✅ Small delay to prevent CPU overuse
                        continue  

                    tg_number = self.extract_tg_number(line)
                    if tg_number:
                        alpha = self.lookup_tg(tg_number)
                        self.signal_tg_update.emit(alpha)  
                        print(f"[ACTIVE TG]: {alpha}")

        except FileNotFoundError:
            print(f"[ERROR] File '{self.stderr_path}' not found.")

    def extract_tg_number(self, line):
        """Extracts the TG number from a voice update line."""
        match = re.search(r'voice update:.*tg\((\d+)\)', line)
        return match.group(1) if match else None

    def stop(self):
        """Gracefully stops the log monitoring thread."""
        self.running = False

class MainWindow(QMainWindow):
    update_display_signal = Signal() 
    def __init__(self):
        super().__init__()
        self.update_display_signal.connect(self.update_display)
        sys.stdout = open("/opt/op25-project/logs/stdout_main.txt", "w")
        sys.stderr = open("/opt/op25-project/logs/stderr_main.txt", "w")
        # NEW: config.ini 
        self.config = MyConfig("config.ini")

        self.speech_on = False      
        self.currentFile = FileObject()
        self.isMenuActive = False  

        self.op25 = OP25Controller()
        self.op25_worker = OP25InitWorker(self.op25)
        self.op25_worker.signal_initialized.connect(self.on_op25_initialized)  # Connect signal to slot
        self.op25_worker.start()

        if not hasattr(self, "ChangeTalkgroupWorker") or not self.ChangeTalkgroupWorker.isRunning():
            self.ChangeTalkgroupWorker = ChangeTalkgroupWorker(self)

        if(self.speech_on):         # Work in Progress
            self.speech = SpeechEngine()
        
        # Initialize GUI first!
        self.setupUi(self)
        self.setDisabled(True)
        QApplication.processEvents()
        self.apply_stylesheet()
        self.showMaximized()
    

    def on_talkgroup_changed(self):
        """Slot that gets called when OP25 is initialized and sets the initial zone and channel."""
        print("[INFO] on_talkgroup_changed() Triggered")
        self.lblConnectionStatus.show()
        self.lblSync.stop_blink()
        self.lblSync.hide()
        self.update_display()
        
    def on_op25_initialized(self):
        """Slot that gets called when OP25 is initialized and sets the initial zone and channel."""
        self.lblChannelName_2.setText("Connected")  # Update the label text

        # Select the first zone
        first_zone = self.currentFile.get_zone(0)
        if first_zone is not None:
            channels = self.currentFile.get_channels_by_zone(first_zone)
            if channels and len(channels) > 0:
                # Set the first channel in the first zone as the current
                self.currentFile.current_zone_index=0
                self.currentFile.current_tg_index=1
                # Now, you can update your display or perform other actions based on the selected channel
                self.update_display()  # Assuming this updates your UI with the selected channel info
            else:
                print("[ERROR] No channels found in the first zone")
        else:
            print("[ERROR] No zones available")

        # If you have additional setup steps, such as triggering scan or talkgroup changes, do that here
        self.lblConnectionStatus.show()
        self.lblSync.stop_blink()
        self.lblSync.hide()
        self.change_talkgroup()
        self.update_display()
        
        self.logMonitor = MonitorLogFileWorker(self.op25, self.op25.stderr_file)
        self.logMonitor.signal_tg_update.connect(self.updateStatusBar)
        self.logMonitor.start()

    def updateStatusBar(self, arg):
        """Updates the status bar with the latest talkgroup name."""
        self.lblChannelName_2.setText(f"{arg}")
                # INITIAL STATUS ICONS
        self.lblSync.start_blink(900)
        self.lblSoundStatus.hide()      #TODO: Implement in future
        self.lblError.hide()            #TODO: Implement in future
        self.lblConnectionStatus.hide()

        self.lblChannelName_2.setText("Connecting...")
        self.lblSoundStatus.hide()

    def updateStatusBarV2(self, zone_name, channel_name, channel_number = -1):
        """Updates the status bar with the latest talkgroup number."""
        self.lblChannelName_2.setText(f"{channel_name}")
        self.lblZone.setText(f"{zone_name}")
        if channel_number > -1: 
            self.lcdNumber.display(int(channel_number))


    class icons(Enum):
        MUTE = ""
        UNMUTE = ""
        SCAN = ""

    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
            
        MainWindow.resize(300, 300)
        MainWindow.setStyleSheet(u"background-color:black;")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayoutWidget = QWidget(self.centralwidget)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(0, 0, 682, 749))
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.topSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.verticalLayout.addItem(self.topSpacer)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setSpacing(0)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.onscreenDisplayLayout = QVBoxLayout()
        self.onscreenDisplayLayout.setSpacing(0)
        self.onscreenDisplayLayout.setObjectName(u"onscreenDisplayLayout")
        self.statusBarLayout = QHBoxLayout()
        self.statusBarLayout.setSpacing(0)
        self.statusBarLayout.setObjectName(u"statusBarLayout")
        self.lblZone = QLabel(self.horizontalLayoutWidget)
        self.lblZone.setObjectName(u"lblZone")
        self.lblZone.setMinimumSize(QSize(0, 30))
        self.lblZone.setMaximumSize(QSize(16777215, 30))
        self.lblZone.setStyleSheet(u"background-color:white; border: none; margin-left: 3px;")

        fontAwesome = QFont()
        fontAwesome.setFamily(u"FontAwesome")
        fontAwesome.setPointSize(12)
        
        self.statusBarLayout.addWidget(self.lblZone)

        self.lblChannelName_2 = BlinkingLabel(self.horizontalLayoutWidget)
        self.lblChannelName_2.setObjectName(u"lblChannelName_2")
        self.lblChannelName_2.setMaximumSize(QSize(16777215, 30))
        self.lblChannelName_2.setStyleSheet(u"background-color:white; border: none;")

        self.statusBarLayout.addWidget(self.lblChannelName_2)

        self.lblSoundStatus = BlinkingLabel(self.horizontalLayoutWidget)
        self.lblSoundStatus.setObjectName(u"lblSoundStatus")
        self.lblSoundStatus.setMaximumSize(QSize(20, 30))
        self.lblSoundStatus.setFont(fontAwesome)

        self.statusBarLayout.addWidget(self.lblSoundStatus)

        self.lblError = BlinkingLabel(self.horizontalLayoutWidget)
        self.lblError.setObjectName(u"lblError")
        self.lblError.setMinimumSize(QSize(10, 0))
        self.lblError.setMaximumSize(QSize(20, 30))

        self.statusBarLayout.addWidget(self.lblError)

        self.lblChanelType = QLabel(self.horizontalLayoutWidget)
        self.lblChanelType.setObjectName(u"lblChanelType")
        self.lblChanelType.setMinimumSize(QSize(10, 0))
        self.lblChanelType.setMaximumSize(QSize(20, 30))
        self.lblChanelType.setFont(fontAwesome)

        self.statusBarLayout.addWidget(self.lblChanelType)

        self.lblSync = BlinkingLabel(self.horizontalLayoutWidget)
        self.lblSync.setObjectName(u"lblSync")
        self.lblSync.setMinimumSize(QSize(10, 0))
        self.lblSync.setMaximumSize(QSize(20, 30))
        self.lblSync.setFont(fontAwesome)

        self.statusBarLayout.addWidget(self.lblSync)

        self.lblConnectionStatus = BlinkingLabel(self.horizontalLayoutWidget)
        self.lblConnectionStatus.setObjectName(u"lblConnectionStatus")
        self.lblConnectionStatus.setMinimumSize(QSize(10, 0))
        self.lblConnectionStatus.setMaximumSize(QSize(20, 30))
        self.lblConnectionStatus.setFont(fontAwesome)

        self.statusBarLayout.addWidget(self.lblConnectionStatus)


        self.onscreenDisplayLayout.addLayout(self.statusBarLayout)

        self.lcdNumber = QLCDNumber(self.horizontalLayoutWidget)
        self.lcdNumber.setObjectName(u"lcdNumber")
        self.lcdNumber.setMinimumSize(QSize(430, 161))
        self.lcdNumber.setMaximumSize(QSize(430, 161))
        self.lcdNumber.setStyleSheet(u"background-color:white; border: none; margin-left: 3px")

        self.onscreenDisplayLayout.addWidget(self.lcdNumber)


        self.verticalLayout_2.addLayout(self.onscreenDisplayLayout)


        self.horizontalLayout_14.addLayout(self.verticalLayout_2)


        self.verticalLayout_3.addLayout(self.horizontalLayout_14)


        self.horizontalLayout_10.addLayout(self.verticalLayout_3)

        self.keypadLayout = QGridLayout()
        self.keypadLayout.setObjectName(u"keypadLayout")
        self.keypadLayout.setHorizontalSpacing(-1)
        
        self.btnGo = QPushButton(self.horizontalLayoutWidget)
        self.btnGo.setObjectName(u"btnGo")

        self.keypadLayout.addWidget(self.btnGo, 4, 2, 1, 1)

        self.btn0 = QPushButton(self.horizontalLayoutWidget)
        self.btn0.setObjectName(u"btn0")
 
        self.keypadLayout.addWidget(self.btn0, 4, 1, 1, 1)

        self.btn3 = QPushButton(self.horizontalLayoutWidget)
        self.btn3.setObjectName(u"btn3")
        self.keypadLayout.addWidget(self.btn3, 0, 2, 1, 1)

        self.btn5 = QPushButton(self.horizontalLayoutWidget)
        self.btn5.setObjectName(u"btn5")
        self.keypadLayout.addWidget(self.btn5, 1, 1, 1, 1)

        self.btn8 = QPushButton(self.horizontalLayoutWidget)
        self.btn8.setObjectName(u"btn8")
        self.keypadLayout.addWidget(self.btn8, 2, 1, 1, 1)

        self.btn9 = QPushButton(self.horizontalLayoutWidget)
        self.btn9.setObjectName(u"btn9")

        self.keypadLayout.addWidget(self.btn9, 2, 2, 1, 1)

        self.btnDel = QPushButton(self.horizontalLayoutWidget)
        self.btnDel.setObjectName(u"btnDel")

        font4 = QFont()
        font4.setFamily(u"FontAwesome")
        font4.setWeight(QFont.Weight.Normal)

        self.keypadLayout.addWidget(self.btnDel, 4, 0, 1, 1)
    
        self.btn4 = QPushButton(self.horizontalLayoutWidget)
        self.btn4.setObjectName(u"btn4")
        self.keypadLayout.addWidget(self.btn4, 1, 0, 1, 1)

        self.btn2 = QPushButton(self.horizontalLayoutWidget)
        self.btn2.setObjectName(u"btn2")

        self.keypadLayout.addWidget(self.btn2, 0, 1, 1, 1)

        self.btn1 = QPushButton(self.horizontalLayoutWidget)
        self.btn1.setObjectName(u"btn1")

        self.keypadLayout.addWidget(self.btn1, 0, 0, 1, 1)

        self.btn6 = QPushButton(self.horizontalLayoutWidget)
        self.btn6.setObjectName(u"btn6")

        self.keypadLayout.addWidget(self.btn6, 1, 2, 1, 1)

        self.btn7 = QPushButton(self.horizontalLayoutWidget)
        self.btn7.setObjectName(u"btn7")
        self.keypadLayout.addWidget(self.btn7, 2, 0, 1, 1)

        self.horizontalLayout_10.addLayout(self.keypadLayout, 1)  # Stretch factor of 1
        self.keypadLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.horizontalLayout_10.addLayout(self.keypadLayout)
        self.verticalLayout.addLayout(self.horizontalLayout_10)

        for button in [self.btnGo, self.btn0, self.btn3, self.btn5, self.btn8, self.btn9,
               self.btnDel, self.btn4, self.btn2, self.btn1, self.btn6, self.btn7]:
                    button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # -- FUNCTION BUTTON GRID LAYOUT (MENU, MUTE, EXIT)
        self.functionButtonLayout = QGridLayout()
        self.functionButtonLayout.setObjectName(u"functionButtonLayout")

        # -- FUNCTION BUTTON HORIZONTAL LAYOUT (ROW)
        self.functionButtonLayoutRow = QHBoxLayout()
        self.functionButtonLayoutRow.setObjectName(u"functionButtonLayoutRow")
        
        # -- #1: MENU BUTTON
        self.btnMenu = self.createButton(self.horizontalLayoutWidget, "btnMenu", u"\uf0c9 ZONES" , "MainWindow", font4, self.toggle_talkgroup_menu)
        self.btnMenu.setDisabled(True)   #TODO: Implement Menu Button & Remove
        self.functionButtonLayoutRow.addWidget(self.btnMenu)
       
        
        # -- #2: GROUPS BUTTON
        self.btnGroups = self.createButton(self.horizontalLayoutWidget, "btnGroups", u"\uf009 CHANNELS" , "MainWindow", font4, self.toggle_talkgroup_menu)
        self.functionButtonLayoutRow.addWidget(self.btnGroups)

        # -- #3: MUTE BUTTON
        self.btnMute = QPushButton(self.horizontalLayoutWidget)
        self.btnMute.setObjectName(u"btnMute")
        self.btnMute.setDisabled(True)  # Ensure it's disabled initially
        self.functionButtonLayoutRow.addWidget(self.btnMute)  # Add to layout

        # -- #4: EXIT BUTTON
        self.btnExit_2 = QPushButton(self.horizontalLayoutWidget)
        self.btnExit_2.setObjectName(u"btnExit_2")
        self.functionButtonLayoutRow.addWidget(self.btnExit_2)

        # + ADD FUNCTION BUTTON ROW LAYOUT (ZONES, CHANNEL)
  
        # -- MENU, MUTE, GROUPS, EXIT ROW
        self.horizontalLayout_12 = QHBoxLayout()

        #ifndef Q_OS_MAC
        self.horizontalLayout_12.setSpacing(-1)
        #endif
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.btnZnDown = QPushButton(self.horizontalLayoutWidget)
        self.btnZnDown.setObjectName(u"btnZnDown")
        self.btnZnDown.setFont(font4)
        self.btnZnDown.setObjectName("btnZnDown")

        self.horizontalLayout_12.addWidget(self.btnZnDown)

        self.btnZnUp = QPushButton(self.horizontalLayoutWidget)
        self.btnZnUp.setFont(font4)
        self.btnZnUp.setObjectName("btnZnUp")
        self.horizontalLayout_12.addWidget(self.btnZnUp)

        # Add a spacer between the buttons
        spacer = QSpacerItem(70, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_12.addItem(spacer)

        # -- Channel Up
        self.btnChUp = QPushButton(self.horizontalLayoutWidget)
        self.btnChUp.setFont(font4)
        self.btnChUp.setObjectName("btnChUp")
        self.horizontalLayout_12.addWidget(self.btnChUp)

        # -- Channel Down
        self.btnChDown = QPushButton(self.horizontalLayoutWidget)
        self.btnChDown.setObjectName(u"btnChDown")
        self.btnChDown.setFont(font4)
        self.horizontalLayout_12.addWidget(self.btnChDown)

        # ROW 2
        self.functionButtonLayout.addLayout(self.horizontalLayout_12, 1, 0, 1, 1)
        # ROW 0
        self.functionButtonLayout.addLayout(self.functionButtonLayoutRow, 0, 0, 1, 1) # BOTTOM
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.functionButtonLayout.addItem(self.verticalSpacer, 2, 0, 1, 1)

        self.verticalLayout.addLayout(self.functionButtonLayout)

        self.horizontalLayout.addLayout(self.verticalLayout)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

        # Inside setupUi:
        self.tg_list = QListWidget(self.centralwidget)
        self.tg_list.setObjectName("tg_list")
        self.tg_list.setStyleSheet("QListWidget { background-color:white; color:black; margin-left: 3px; }")
        self.tg_list.setVisible(False)  # Start hidden
        self.tg_list.setMinimumSize(QSize(420, 161))
        self.tg_list.setMaximumHeight(200)
        self.tg_list.setMaximumSize(QSize(420, 161))
        
        self.tg_list.itemClicked.connect(self.select_talkgroup)
        self.verticalLayout_2.addWidget(self.tg_list)

        self.apply_stylesheet()   
    # setupUi
    def apply_stylesheet(self):
        """Loads the stylesheet from an external file."""
        # Get the directory where the Python file is located
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # Example: Define a relative path for a file (e.g., a stylesheet)
        stylesheet_path = os.path.join(BASE_DIR, "styles.css")
        with open(stylesheet_path, "r") as file:
            self.setStyleSheet(file.read())

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.lblZone.setText(QCoreApplication.translate("MainWindow", u"Zone", None))
        self.lblChannelName_2.setText(QCoreApplication.translate("MainWindow", u"Channel Name", None))
        self.lblSoundStatus.setText(QCoreApplication.translate("MainWindow", u"\uf028", None))
        self.lblError.setText(QCoreApplication.translate("MainWindow", u"\uf071", None))
        self.lblChanelType.setText(QCoreApplication.translate("MainWindow", u"\uf0c0", None))
        self.lblSync.setText(QCoreApplication.translate("MainWindow", u"\uf021", None))
        self.lblConnectionStatus.setText(QCoreApplication.translate("MainWindow", u"\uf012", None))
        self.btnGo.setText(QCoreApplication.translate("MainWindow", u"\uf069 GO", None))
        self.btn0.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.btn3.setText(QCoreApplication.translate("MainWindow", u"3", None))
        self.btn5.setText(QCoreApplication.translate("MainWindow", u"5", None))
        self.btn8.setText(QCoreApplication.translate("MainWindow", u"8", None))
        self.btn9.setText(QCoreApplication.translate("MainWindow", u"9", None))
        self.btnDel.setText(QCoreApplication.translate("MainWindow", u"\uf00d DEL", None))
        self.btn4.setText(QCoreApplication.translate("MainWindow", u"4", None))
        self.btn2.setText(QCoreApplication.translate("MainWindow", u"2", None))
        self.btn1.setText(QCoreApplication.translate("MainWindow", u"1", None))
        self.btn6.setText(QCoreApplication.translate("MainWindow", u"6", None))
        self.btn7.setText(QCoreApplication.translate("MainWindow", u"7", None))
        self.btnMute.setText(QCoreApplication.translate("MainWindow", u"MUTE", None))
        self.btnExit_2.setText(QCoreApplication.translate("MainWindow", u"EXIT", None))
        self.btnZnDown.setText(QCoreApplication.translate("MainWindow", u"Zn \uf107", None))
        self.btnZnUp.setText(QCoreApplication.translate("MainWindow", u"Zn \uf106", None))
        self.btnChDown.setText(QCoreApplication.translate("MainWindow", u"Ch \uf106", None))
        self.btnChUp.setText(QCoreApplication.translate("MainWindow", u"Ch \uf106", None))
        self.btn0.clicked.connect(lambda: self.keypad_input("0"))
        self.btn1.clicked.connect(lambda: self.keypad_input("1"))
        self.btn2.clicked.connect(lambda: self.keypad_input("2"))
        self.btn3.clicked.connect(lambda: self.keypad_input("3"))
        self.btn4.clicked.connect(lambda: self.keypad_input("4"))
        self.btn5.clicked.connect(lambda: self.keypad_input("5"))
        self.btn6.clicked.connect(lambda: self.keypad_input("6"))
        self.btn7.clicked.connect(lambda: self.keypad_input("7"))
        self.btn8.clicked.connect(lambda: self.keypad_input("8"))
        self.btn9.clicked.connect(lambda: self.keypad_input("9"))
        self.btnDel.clicked.connect(self.clear_keypad_input)  # Clear Input
        self.btnGo.clicked.connect(self.confirm_tgid_input)  # Apply TGID
        
        self.btnMute.clicked.connect(self.toggle_mute)  # Mute Toggle
        self.btnExit_2.clicked.connect(self.close_app)  # Exit Application

        self.btnChUp.clicked.connect(self.channel_up)
        self.btnChDown.clicked.connect(self.channel_down)
        self.btnZnUp.clicked.connect(self.zone_up)   # CH ▲
        self.btnZnDown.clicked.connect(self.zone_down)   # CH ▼

    # retranslateUi

    def monitor_stderr(self, file_path):
        """Monitors the stderr2 file for new voice update lines."""
        try:
            with open(file_path, "r") as file:
                file.seek(0, 2)  # Move to the end of the file

                while True:
                    line = file.readline()
                    if not line:
                        continue  # No new line, keep waiting

                    tg_number = self.extract_tg_number(line)
                    if tg_number:
                        print(f"[ACTIVE TG]: {tg_number}")  # Print the latest TG number

        except FileNotFoundError:
            print(f"[ERROR] File '{file_path}' not found.")

    def keypad_input(self, digit):
        """Handles numeric button input for direct TGID entry and menu navigation."""
        if self.isMenuActive:
            if digit == "3":
                print("[DEBUG] Moving selection up")
                self.move_selection_up()
            elif digit == "9":
                print("[DEBUG] Moving selection down")
                self.move_selection_down()
            return  # Stop normal keypad behavior when menu is active

        # Normal keypad input processing
        current_text = str(int(self.lcdNumber.value())) if self.lcdNumber.value() else ""

        if len(current_text) >= 3:
            current_text = current_text[1:]  # Shift digits
        if self.speech_on:
            self.speech.speak(f"{digit}")

        new_text = current_text + digit
        self.lcdNumber.display(new_text)

    def toggle_mute(self):
        """Toggles mute status (Placeholder for future implementation)."""
        print("[DEBUG] Mute toggled")

    def confirm_tgid_input(self):
        """Handles TGID entry normally, but if the menu is open, triggers selection in the list."""
        if self.isMenuActive:
            current_row = self.tg_list.currentRow()  # Get selected row
            if current_row >= 0:  # Ensure a valid selection
                print(f"[DEBUG] Confirming selection of row {current_row}")
                item = self.tg_list.item(current_row)
                if item:
                    item.setSelected(True)  # Ensure it's visually selected
                    self.select_talkgroup(item)  # Trigger the selection event
            return  # Stop normal processing if menu is open

        # Normal TGID processing
        tgid = int(self.lcdNumber.intValue()) if self.lcdNumber.intValue() else None  

        if not tgid:
            print("[ERROR] No valid TGID entered.")
            return

        # Find the channel with the matching TGID
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
                break  # Stop searching once found

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

    def update_display(self):
        """Updates the UI labels and LCD screen with the current zone and talkgroup info."""
        
        if self.currentFile.current_tg_index is None:
            print("[ERROR] No current channel index set.")
            return

        current_zone = self.currentFile.zone_names[self.currentFile.current_zone_index]

        current_channel = self.currentFile.get_channel_by_number(self.currentFile.current_tg_index)
        
        if not current_channel:
            print("[ERROR] No channel found for index", self.currentFile.current_tg_index)
            self.lblChannelName_2.setText("No Channel")
            self.lcdNumber.display(0)  # Ensure LCD shows zero instead of old value
            return

        tg_name = current_channel["name"]
        tg_number = current_channel["channel_number"]

        # Debugging to ensure values are correct
        print(f"[DEBUG] Updating Display: Zone: {current_zone}, Channel: {tg_name}, Number: {tg_number}")

        # Update UI components
        self.lblZone.setText(current_zone)
        self.lblChannelName_2.setText(tg_name)
        self.lcdNumber.display(int(tg_number))  # Use display() instead of setValue()

        # Set the channel type icon
        if current_channel["type"] == "scan":
            self.lblChanelType.setText("\uf002")  
        else:
            self.lblChanelType.setText("\uf0c0")

    def clear_keypad_input(self):
        """Clears the TGID input on the LCD screen."""
        self.lcdNumber.display("")
   
    def createButton(self, parent, objectName, text, context="MainWindow", font=None, callback=None):
        btn = QPushButton(parent)
        btn.setObjectName(objectName)
        btn.setText(QCoreApplication.translate(context, text, None))
        if font:
            btn.setFont(font)
        if callback:
            btn.clicked.connect(callback)
        return btn

    def toggle_talkgroup_menu(self):
        """Toggles the talkgroup menu visibility."""

        if self.isMenuActive:
            # The menu is currently open, so we will close it
            # Hide the talkgroup list and show all other relevant UI elements
            self.tg_list.hide()
            self.lcdNumber.show()
            self.lblChanelType.show()
            self.lblSoundStatus.show()
            self.lblChannelName_2.show()
            self.lblError.show()
            self.lblConnectionStatus.show()

            self.btn0.show()
            self.btn1.show()
            self.btn2.show()
            self.btn3.setText("3")
            self.btn4.show()
            self.btn5.show()
            self.btn6.show()
            self.btn7.show()
            self.btn8.show()
            self.btn9.setText("9")
            self.btnDel.show()
            self.btnGo.show()
            self.isMenuActive = False  # Update state to indicate menu is closed
        else:
            # The menu is currently closed, so we will open it
            # Hide non-essential interface elements and show the talkgroup list
            self.isMenuActive = True
            self.tg_list.show()
            self.lcdNumber.hide()
            self.lblChanelType.hide()
            self.lblSoundStatus.hide()
            self.lblChannelName_2.hide()
            self.lblError.hide()
            self.btn0.hide()
            self.btn1.hide()
            self.btn2.hide()
            self.btn3.setText("UP")
            self.btn4.hide()
            self.btn5.hide()
            self.btn6.hide()
            self.btn7.hide()
            self.btn8.hide()
            self.btn9.setText("DWN")
            self.btnDel.hide()
            self.btnGo.show()
            self.lblConnectionStatus.hide()
            self.open_talkgroup_menu()  # Assuming this method sets up the talkgroup list for display

    def open_talkgroup_menu(self):
        """Opens the talkgroup menu for the current zone."""
        current_zone = self.currentFile.zone_names[self.currentFile.current_zone_index]
        self.tg_list.clear()  # Clear old items

        # Retrieve channel names from the file object
        channel_list = [channel["name"] for channel in self.currentFile.get_channels_by_zone(current_zone)]

        if channel_list:
            self.tg_list.addItems(channel_list)
            self.tg_list.show() 
        else:
            print("[WARNING] No channels available in the current zone.")
    
    def move_selection_down(self):
        """Moves the selection down by one in a QListWidget."""
        current_row = self.tg_list.currentRow()

        if current_row < self.tg_list.count() - 1:  # Ensure within bounds
            self.tg_list.setCurrentRow(current_row + 1)  # Move down
            self.tg_list.item(current_row + 1).setSelected(True)  # Ensure it's selected
            self.tg_list.scrollToItem(self.tg_list.item(current_row + 1))  # Ensure visibility
   
    def move_selection_up(self):
        """Moves the selection up by one in a QListWidget."""
        current_row = self.tg_list.currentRow()

        if current_row > 0:  # Ensure within bounds
            self.tg_list.setCurrentRow(current_row - 1)  # Move up
            self.tg_list.item(current_row - 1).setSelected(True)  # Ensure it's selected
            self.tg_list.scrollToItem(self.tg_list.item(current_row - 1))  # Ensure visibility
    
    def select_talkgroup(self, item):
        """Handles user selecting a talkgroup from the menu and applies it."""
        self.setUpdatesEnabled(False)
        self.setDisabled(True)
        self.toggle_talkgroup_menu()
        self.setUpdatesEnabled(True)
        QApplication.processEvents()

        self.talkgroup_name = item.text()
        self.current_zone_index = self.currentFile.current_zone_index

        # Ensure current zone index is valid before proceeding
        if self.current_zone_index >= len(self.currentFile.zone_names):
            print("[ERROR] Current zone index out of bounds")
            return

        self.current_zone = self.currentFile.zone_names[self.current_zone_index]

        # Find selected channel
        selected_channel = next(
            (ch for ch in self.currentFile.get_channels_by_zone(self.current_zone) if ch["name"] == self.talkgroup_name),
            None
        )

        if not selected_channel:
            print(f"[ERROR] Talkgroup '{self.talkgroup_name}' not found in zone '{self.current_zone}'")
            return  # ✅ Exit early if the selection is invalid

        # Set the selected talkgroup index
        self.currentFile.current_tg_index = selected_channel["channel_number"]

        # Use QTimer to delay execution without freezing UI
        QTimer.singleShot(2000, self.change_talkgroup)  # ⏳ Delayed switch (non-blocking)

    def close_app(self):
        """Closes the application."""
        print("Closing application...")
        if(self.speech_on):
            self.speech.stop()  # Stop speech engine before exit
        self.op25.stop()        #TODO: Send request to OP25 to stop gracefully.
        self.monitor.stop()  # Ensures cleanup on exit
        self.close()

    def channel_up(self):
        """Moves to the next channel using FileObject's methods."""
        self.setDisabled(True)
        QApplication.processEvents()  # Force UI to refresh immediately
        current_channel_number = self.currentFile.current_tg_index
        next_channel = self.currentFile.get_channel_by_number(current_channel_number + 1)

        if next_channel:
            self.currentFile.current_tg_index = next_channel["channel_number"]
        else:
            # If no next channel, loop back to the first channel
            first_channel = self.currentFile.get_channels_by_zone(self.currentFile.zone_names[self.currentFile.current_zone_index])
            self.currentFile.current_tg_index = first_channel[0]["channel_number"] if first_channel else 0

        self.change_talkgroup()
        self.setDisabled(False)

    def channel_down(self):
        """Moves to the previous channel using FileObject's methods."""
        self.setDisabled(True)
        QApplication.processEvents()  # Force UI to refresh immediately
        current_channel_number = self.currentFile.current_tg_index
        previous_channel = self.currentFile.get_previous_channel(current_channel_number)

        if previous_channel:
            self.currentFile.current_tg_index = previous_channel["channel_number"]
        else:
            # If no previous channel, loop to the last channel in the zone
            last_channel = self.currentFile.get_channels_by_zone(self.currentFile.zone_names[self.currentFile.current_zone_index])
            self.currentFile.current_tg_index = last_channel[-1]["channel_number"] if last_channel else 0

        self.change_talkgroup()  # Apply the new talkgroup or scan list
        self.setDisabled(False)

    def zone_up(self):
        """Moves to the next zone, loops back if at the last zone."""
        self.setDisabled(True)  # Disable UI to prevent rapid multiple clicks
        QApplication.processEvents()  # Allow UI to update

        try:
            # Increment the zone index with wrap-around
            self.currentFile.current_zone_index = (
                self.currentFile.current_zone_index + 1
            ) % len(self.currentFile.zone_names)
            
            current_zone = self.currentFile.zone_names[self.currentFile.current_zone_index]
            # Retrieve the first channel object in the new zone
            first_channel_obj = self.currentFile.get_first_channel_in_zone(self.currentFile.current_zone_index)
            
            if first_channel_obj is not None:
                # Update the current talkgroup index with the channel's number
                self.currentFile.current_tg_index = first_channel_obj["channel_number"]

                if self.speech_on:
                    self.speech.speak(f"{current_zone} - {first_channel_obj['name']}")
                
                self.change_talkgroup()
                self.update_display()
        except Exception as e:
            print(f"[ERROR] zone_up encountered an issue: {e}")
        finally:
            self.setDisabled(False)  # Ensure UI is always re-enabled

    def zone_down(self):
        """Moves to the previous zone, loops to the last if at the first."""
        self.setDisabled(True)
        QApplication.processEvents() 
        
        try:
            prev_zone = self.currentFile.get_previous_zone(self.currentFile.current_zone_index)
            if not prev_zone:
                print("[ERROR] No previous zone found.")
                return  # Exit early if no previous zone
            
            self.currentFile.current_zone_index = self.currentFile.zone_names.index(prev_zone)
            
            if self.currentFile.current_tg_index is not None:
                self.update_display()
                current_zone = self.currentFile.zone_names[self.currentFile.current_zone_index]
                first_channel = self.currentFile.get_channel_by_number(self.currentFile.current_tg_index)
                
                if self.speech_on: 
                    self.speech.speak(f"{current_zone} - {first_channel['name'] if first_channel else 'No Channels'}")

                self.change_talkgroup()

            
        except Exception as e:
            print(f"[ERROR] zone_down encountered an issue: {e}")
        finally:
            self.setDisabled(False)  # Ensure UI is always re-enabled

    def load_first_channel(self):
        """Loads the first channel of the current zone and applies its talkgroup settings."""
        first_channel = self.currentFile.get_channels_by_zone(
            self.currentFile.zone_names[self.currentFile.current_zone_index]
        )

        if not first_channel:  # Prevents index error if zone is empty
            print("[WARNING] No channels found in the current zone.")
            return
        
        self.currentFile.current_tg_index = first_channel[0]["channel_number"]

        self.change_talkgroup()  # Ensure the talkgroup is updated


    def change_talkgroup(self):
        """Applies the correct talkgroup or scan list based on the current channel."""
        
        if self.currentFile.current_tg_index is None:
            print("[ERROR] Current channel index not set")
            return

        selected_channel = self.currentFile.get_channel_by_number(self.currentFile.current_tg_index)
        if not selected_channel:
            print("[ERROR] Selected channel not found")
            return

        wlist = selected_channel.get('tgid')
        if not wlist:
            print("[ERROR] No TGID found in selected channel")
            return

        if self.op25:
            try:
                self.op25.switchGroup(wlist=wlist)
            except Exception as e:
                print(f"[ERROR] Failed to switch talkgroup: {e}")
                return

        # Stop old worker before starting a new one
        if hasattr(self, "changeTalkgroupWorker") and self.changeTalkgroupWorker:
            if self.changeTalkgroupWorker.isRunning():
                print("[DEBUG] Previous ChangeTalkgroupWorker still running, waiting...")
                self.changeTalkgroupWorker.quit()
                self.changeTalkgroupWorker.wait()
            self.changeTalkgroupWorker = None  

        # Start a new worker safely
        self.changeTalkgroupWorker = ChangeTalkgroupWorker(self)
        self.changeTalkgroupWorker.signal_initialized.connect(self.update_display_signal.emit)  # ✅ Emit Signal
        self.changeTalkgroupWorker.start()

       

    def cleanup_before_exit(self):
        """Cleanup actions before exiting the application."""
        print("[INFO] Stopping OP25...")
        if hasattr(self, "op25"):
            self.op25.stop()  # Ensure OP25 shuts down properly

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()  # Instantiating MainWindow directly
    mainWindow.show()
    sys.exit(app.exec())