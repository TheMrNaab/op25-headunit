import sys
import os
import csv
import re
# PySide6 Core Imports
from PySide6.QtCore import QThread, Signal, QTimer, QMetaObject, QRect, QSize, QCoreApplication, Qt, QPropertyAnimation, QVariantAnimation

# PySide6 GUI Imports
from PySide6.QtGui import QFont, QFontDatabase, QTransform, QPixmap

# PySide6 Widgets
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QFrame, QPushButton, QLCDNumber, 
    QSizePolicy, QSpacerItem, QVBoxLayout, QHBoxLayout, QGridLayout, QListWidget
)

# Project-Specific Imports
from tts import SpeechEngine
from ir import IRRemoteHandler
from file_object import FileObject
from control import OP25Controller  # This must import properly
from customWidgets import BlinkingLabel

class ScanListWorker(QThread):
    signal_complete = Signal()

    def __init__(self, op25_instance, tgids):
        super().__init__()
        self.op25 = op25_instance
        self.tgids = tgids

    def run(self):
        """Process scan TGIDs in a separate thread."""
        print(f"[DEBUG] Processing {len(self.tgids)} TGIDs in scan mode")
        self.op25.update_scan_list(self.tgids)
        self.signal_complete.emit()  # Notify UI when done

class OP25InitWorker(QThread):
    """Worker thread for initializing OP25 without blocking the UI."""
    signal_initialized = Signal()  

    def __init__(self, op25_instance):
        super().__init__()
        self.op25 = op25_instance

    def run(self):
        self.op25.start()
        self.signal_initialized.emit()  

from PySide6.QtCore import QThread, Signal

class MonitorLogFileWorker(QThread):
    """Worker thread for monitoring the OP25 log file without blocking the UI."""
    signal_tg_update = Signal(str)  # ✅ Signal to send back the TG number

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ir_on = True       
        self.speech_on = False      
        self.currentFile = FileObject()
        self.isMenuActive = False  

        if(self.speech_on):         # Work in Progress
            self.speech = SpeechEngine()
        
        if self.ir_on:              # Work in Progress
            self.start_ir_listener() 
            self.ir_handler = IRRemoteHandler(self)  
            self.start_ir_listener()  
        
        self.setupUi(self)

        # INITIAL STATUS ICONS
        self.lblSync.start_blink(900)
        self.lblSoundStatus.hide()      #TODO: Implement in future
        self.lblError.hide()            #TODO: Implement in future
        self.lblConnectionStatus.hide()

        self.lblChannelName_2.setText("Connecting...")
        self.lblSoundStatus.hide()
        
        self.op25 = OP25Controller()
        self.op25_worker = OP25InitWorker(self.op25)
        self.op25_worker.signal_initialized.connect(self.on_op25_initialized)  # Connect signal to slot
        self.op25_worker.start()


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
        """Updates the status bar with the latest talkgroup number."""
        self.lblChannelName_2.setText(f"{arg}")
        #self.lblChannelName_2.start_blink(500)
         

    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(693, 374)
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
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(QFont.Weight.Bold)  # ✅ Use enum instead of an integer
        self.lblZone.setFont(font)
        self.lblZone.setStyleSheet(u"background-color:white; border: none; margin-left: 3px;")

        self.statusBarLayout.addWidget(self.lblZone)

        self.lblChannelName_2 = BlinkingLabel(self.horizontalLayoutWidget)
        self.lblChannelName_2.setObjectName(u"lblChannelName_2")
        self.lblChannelName_2.setMaximumSize(QSize(16777215, 30))
        self.lblChannelName_2.setFont(font)
        self.lblChannelName_2.setStyleSheet(u"background-color:white; border: none;")

        self.statusBarLayout.addWidget(self.lblChannelName_2)

        self.lblSoundStatus = BlinkingLabel(self.horizontalLayoutWidget)
        self.lblSoundStatus.setObjectName(u"lblSoundStatus")
        self.lblSoundStatus.setMaximumSize(QSize(20, 30))
        font1 = QFont()
        font1.setFamily(u"FontAwesome")
        font1.setPointSize(12)
        self.lblSoundStatus.setFont(font1)
        self.lblSoundStatus.setStyleSheet(u"background-color:white; border: none;")
        self.lblSoundStatus.setAlignment(Qt.AlignCenter)

        self.statusBarLayout.addWidget(self.lblSoundStatus)

        self.lblError = BlinkingLabel(self.horizontalLayoutWidget)
        self.lblError.setObjectName(u"lblError")
        self.lblError.setMinimumSize(QSize(10, 0))
        self.lblError.setMaximumSize(QSize(20, 30))
        font2 = QFont()
        font2.setFamily(u"FontAwesome")
        self.lblError.setFont(font2)
        self.lblError.setStyleSheet(u"background-color:white;\n"
"color:orange;")
        self.lblError.setAlignment(Qt.AlignCenter)

        self.statusBarLayout.addWidget(self.lblError)

        self.lblChanelType = QLabel(self.horizontalLayoutWidget)
        self.lblChanelType.setObjectName(u"lblChanelType")
        self.lblChanelType.setMinimumSize(QSize(10, 0))
        self.lblChanelType.setMaximumSize(QSize(20, 30))
        self.lblChanelType.setFont(font2)
        self.lblChanelType.setStyleSheet(u"background-color:white")
        self.lblChanelType.setAlignment(Qt.AlignCenter)

        self.statusBarLayout.addWidget(self.lblChanelType)

        self.lblSync = BlinkingLabel(self.horizontalLayoutWidget)
        self.lblSync.setObjectName(u"lblSync")
        self.lblSync.setMinimumSize(QSize(10, 0))
        self.lblSync.setMaximumSize(QSize(20, 30))
        self.lblSync.setFont(font2)
        self.lblSync.setStyleSheet(u"background-color:white")
        self.lblSync.setAlignment(Qt.AlignCenter)

        self.statusBarLayout.addWidget(self.lblSync)

        self.lblConnectionStatus = BlinkingLabel(self.horizontalLayoutWidget)
        self.lblConnectionStatus.setObjectName(u"lblConnectionStatus")
        self.lblConnectionStatus.setMinimumSize(QSize(10, 0))
        self.lblConnectionStatus.setMaximumSize(QSize(20, 30))
        self.lblConnectionStatus.setFont(font2)
        self.lblConnectionStatus.setStyleSheet(u"background-color:white")
        self.lblConnectionStatus.setAlignment(Qt.AlignCenter)

        self.statusBarLayout.addWidget(self.lblConnectionStatus)


        self.onscreenDisplayLayout.addLayout(self.statusBarLayout)

        self.lcdNumber = QLCDNumber(self.horizontalLayoutWidget)
        self.lcdNumber.setObjectName(u"lcdNumber")
        self.lcdNumber.setMinimumSize(QSize(0, 161))
        self.lcdNumber.setMaximumSize(QSize(320, 161))
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
        font3 = QFont()
        font3.setFamily(u"FontAwesome")
        font3.setBold(True)
        font3.setWeight(QFont.Weight.Bold)  # ✅ Use enum instead of an integer
        font3.setKerning(True)
        self.btnGo.setFont(font3)
        self.btnGo.setStyleSheet(u"            QPushButton {\n"
"                background-color: green;\n"
"                color: white;\n"
"                font-size: 16px;\n"
"                font-weight: bold;\n"
"                border: 2px solid #666;\n"
"                padding: 8px;\n"
"            }\n"
"            QPushButton:pressed {\n"
"                background-color: #666;\n"
"            }")

        self.keypadLayout.addWidget(self.btnGo, 4, 2, 1, 1)

        self.btn0 = QPushButton(self.horizontalLayoutWidget)
        self.btn0.setObjectName(u"btn0")
        self.btn0.setStyleSheet(u"            QPushButton {\n"
"                background-color: #444;\n"
"                color: white;\n"
"                font-size: 16px;\n"
"                font-weight: bold;\n"
"                border: 2px solid #666;\n"
"                padding: 8px;\n"
"            }\n"
"            QPushButton:pressed {\n"
"                background-color: #666;\n"
"            }")

        self.keypadLayout.addWidget(self.btn0, 4, 1, 1, 1)

        self.btn3 = QPushButton(self.horizontalLayoutWidget)
        self.btn3.setObjectName(u"btn3")
        self.btn3.setStyleSheet(u"            QPushButton {\n"
"                background-color: #444;\n"
"                color: white;\n"
"                font-size: 16px;\n"
"                font-weight: bold;\n"
"                border: 2px solid #666;\n"
"                padding: 8px;\n"
"            }\n"
"            QPushButton:pressed {\n"
"                background-color: #666;\n"
"            }")

        self.keypadLayout.addWidget(self.btn3, 0, 2, 1, 1)

        self.btn5 = QPushButton(self.horizontalLayoutWidget)
        self.btn5.setObjectName(u"btn5")
        self.btn5.setStyleSheet(u"            QPushButton {\n"
"                background-color: #444;\n"
"                color: white;\n"
"                font-size: 16px;\n"
"                font-weight: bold;\n"
"                border: 2px solid #666;\n"
"                padding: 8px;\n"
"            }\n"
"            QPushButton:pressed {\n"
"                background-color: #666;\n"
"            }")

        self.keypadLayout.addWidget(self.btn5, 1, 1, 1, 1)

        self.btn8 = QPushButton(self.horizontalLayoutWidget)
        self.btn8.setObjectName(u"btn8")
        self.btn8.setStyleSheet(u"            QPushButton {\n"
"                background-color: #444;\n"
"                color: white;\n"
"                font-size: 16px;\n"
"                font-weight: bold;\n"
"                border: 2px solid #666;\n"
"                padding: 8px;\n"
"            }\n"
"            QPushButton:pressed {\n"
"                background-color: #666;\n"
"            }")

        self.keypadLayout.addWidget(self.btn8, 2, 1, 1, 1)

        self.btn9 = QPushButton(self.horizontalLayoutWidget)
        self.btn9.setObjectName(u"btn9")
        self.btn9.setStyleSheet(u"            QPushButton {\n"
"                background-color: #444;\n"
"                color: white;\n"
"                font-size: 16px;\n"
"                font-weight: bold;\n"
"                border: 2px solid #666;\n"
"                padding: 8px;\n"
"            }\n"
"            QPushButton:pressed {\n"
"                background-color: #666;\n"
"            }")

        self.keypadLayout.addWidget(self.btn9, 2, 2, 1, 1)

        self.btnDel = QPushButton(self.horizontalLayoutWidget)
        self.btnDel.setObjectName(u"btnDel")
        font4 = QFont()
        font4.setFamily(u"FontAwesome")
        font4.setBold(True)
        font4.setWeight(QFont.Weight.Bold)  # ✅ Use enum instead of an integer
        self.btnDel.setFont(font4)
        self.btnDel.setStyleSheet(u"            QPushButton {\n"
"                background-color: rgb(195, 0, 0);\n"
"                color: white;\n"
"                font-size: 16px;\n"
"                font-weight: bold;\n"
"                border: 2px solid #666;\n"
"                padding: 8px;\n"
"            }\n"
"            QPushButton:pressed {\n"
"                background-color: #666;\n"
"            }")

        self.keypadLayout.addWidget(self.btnDel, 4, 0, 1, 1)

        self.btn4 = QPushButton(self.horizontalLayoutWidget)
        self.btn4.setObjectName(u"btn4")
        self.btn4.setStyleSheet(u"            QPushButton {\n"
"                background-color: #444;\n"
"                color: white;\n"
"                font-size: 16px;\n"
"                font-weight: bold;\n"
"                border: 2px solid #666;\n"
"                padding: 8px;\n"
"            }\n"
"            QPushButton:pressed {\n"
"                background-color: #666;\n"
"            }")

        self.keypadLayout.addWidget(self.btn4, 1, 0, 1, 1)

        self.btn2 = QPushButton(self.horizontalLayoutWidget)
        self.btn2.setObjectName(u"btn2")
        self.btn2.setStyleSheet(u"            QPushButton {\n"
"                background-color: #444;\n"
"                color: white;\n"
"                font-size: 16px;\n"
"                font-weight: bold;\n"
"                border: 2px solid #666;\n"
"                padding: 8px;\n"
"            }\n"
"            QPushButton:pressed {\n"
"                background-color: #666;\n"
"            }")

        self.keypadLayout.addWidget(self.btn2, 0, 1, 1, 1)

        self.btn1 = QPushButton(self.horizontalLayoutWidget)
        self.btn1.setObjectName(u"btn1")
        self.btn1.setStyleSheet(u"            QPushButton {\n"
"                background-color: #444;\n"
"                color: white;\n"
"                font-size: 16px;\n"
"                font-weight: bold;\n"
"                border: 2px solid #666;\n"
"                padding: 8px;\n"
"            }\n"
"            QPushButton:pressed {\n"
"                background-color: #666;\n"
"            }")

        self.keypadLayout.addWidget(self.btn1, 0, 0, 1, 1)

        self.btn6 = QPushButton(self.horizontalLayoutWidget)
        self.btn6.setObjectName(u"btn6")
        self.btn6.setStyleSheet(u"            QPushButton {\n"
"                background-color: #444;\n"
"                color: white;\n"
"                font-size: 16px;\n"
"                font-weight: bold;\n"
"                border: 2px solid #666;\n"
"                padding: 8px;\n"
"            }\n"
"            QPushButton:pressed {\n"
"                background-color: #666;\n"
"            }")

        self.keypadLayout.addWidget(self.btn6, 1, 2, 1, 1)

        self.btn7 = QPushButton(self.horizontalLayoutWidget)
        self.btn7.setObjectName(u"btn7")
        self.btn7.setStyleSheet(u"            QPushButton {\n"
"                background-color: #444;\n"
"                color: white;\n"
"                font-size: 16px;\n"
"                font-weight: bold;\n"
"                border: 2px solid #666;\n"
"                padding: 8px;\n"
"            }\n"
"            QPushButton:pressed {\n"
"                background-color: #666;\n"
"            }")

        self.keypadLayout.addWidget(self.btn7, 2, 0, 1, 1)


        self.horizontalLayout_10.addLayout(self.keypadLayout)


        self.verticalLayout.addLayout(self.horizontalLayout_10)

        # -- FUNCTION BUTTON GRID LAYOUT (MENU, MUTE, EXIT)
        self.functionButtonLayout = QGridLayout()
        self.functionButtonLayout.setObjectName(u"functionButtonLayout")

        # -- FUNCTION BUTTON HORIZONTAL LAYOUT (ROW)
        self.functionButtonLayoutRow = QHBoxLayout()
        self.functionButtonLayoutRow.setObjectName(u"functionButtonLayoutRow")
        
        # -- #1: MENU BUTTON
        self.btnMenu = QPushButton(self.horizontalLayoutWidget)
        self.btnMenu.setObjectName(u"btnMenu")
        self.btnMenu.setFont(font4)

        self.functionButtonLayoutRow.addWidget(self.btnMenu)

        self.btnGroups = QPushButton(self.horizontalLayoutWidget)
        
        # -- #2: GROUPS BUTTON
        self.btnGroups.setObjectName(u"btnGroups")
        self.btnGroups.setFont(font4)
        self.functionButtonLayoutRow.addWidget(self.btnGroups)

        # -- #3: MUTE BUTTON
        self.btnMute = QPushButton(self.horizontalLayoutWidget)
        self.btnMute.setObjectName(u"btnMute")
        self.functionButtonLayoutRow.addWidget(self.btnMute)

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
        self.tg_list.setMaximumHeight(200)
        self.tg_list.setMaximumSize(QSize(320, 161))
        
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
        self.btnMenu.setText(QCoreApplication.translate("MainWindow", u"\uf0c9 MENU", None))
        self.btnMute.setText(QCoreApplication.translate("MainWindow", u"MUTE", None))
        self.btnExit_2.setText(QCoreApplication.translate("MainWindow", u"EXIT", None))
        self.btnZnDown.setText(QCoreApplication.translate("MainWindow", u"Zn \uf107", None))
        self.btnGroups.setText(QCoreApplication.translate("MainWindow", u"\uf009 ZONES", None))
        self.btnZnUp.setText(QCoreApplication.translate("MainWindow", u"Zn \uf106", None))
        self.btnChDown.setText(QCoreApplication.translate("MainWindow", u"Ch \uf106", None))
        self.btnChUp.setText(QCoreApplication.translate("MainWindow", u"Ch \uf106", None))

        self.btnMenu.clicked.connect(self.toggle_talkgroup_menu)  # ✅ Correct function name
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


        self.btnZnUp.clicked.connect(self.zone_up)   # CH ▲
        self.btnZnDown.clicked.connect(self.zone_down)   # CH ▼
        self.btnGroups.clicked.connect(self.toggle_talkgroup_menu)  # Open Groups Menu
    # retranslateUi

    def extract_tg_number(self, line):
        """Extracts the TG number from a voice update line."""
        match = re.search(r'voice update:.*tg\((\d+)\)', line)
        return match.group(1) if match else None

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

    def start_ir_listener(self):
        """Runs the IR listener in a separate thread to prevent blocking the UI."""
        import threading
        ir_thread = threading.Thread(target=self.ir_handler.listen, daemon=True)
        ir_thread.start()

    def keypad_input(self, digit):
        """Handles numeric button input for direct TGID entry with TV-style shifting."""
        current_text = str(int(self.lcdNumber.value())) if self.lcdNumber.value() else ""
        
        if len(current_text) >= 3:
            current_text = current_text[1:]  # Remove the leftmost digit (shift behavior)
        if self.speech_on:
                    self.speech.speak(f"{digit}")

        new_text = current_text + digit
        self.lcdNumber.display(new_text)  # Update LCD

    def toggle_mute(self):
        """Toggles mute status (Placeholder for future implementation)."""
        print("[DEBUG] Mute toggled")

    def confirm_tgid_input(self):
        """Applies the entered TGID, updates the zone, and changes the channel."""
        tgid = int(self.lcdNumber.intValue()) if self.lcdNumber.intValue() else None  # ✅ Use intValue() for QLCDNumber

        if not tgid:
            print("[ERROR] No valid TGID entered.")
            return

        # Find channel with matching TGID
        found_channel = None
        found_zone = None

        for zone_name in self.currentFile.zone_names:
            channels = self.currentFile.get_channels_by_zone(zone_name)
            for channel in channels:
                if "channel_number" in channel and channel["channel_number"] == tgid:  # ✅ Prevent KeyError
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
            self.speech.speak(f"Channel {tgid} in {found_zone}")  # ✅ Use found_zone instead of zone_name
    
    def clear_keypad_input(self):
        """Clears the TGID input on the LCD screen."""
        self.lcdNumber.display("")
   
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
            self.tg_list.show()  # ✅ Ensure the menu becomes visible
        else:
            print("[WARNING] No channels available in the current zone.")

    def update_display(self):
        """Updates the UI labels and LCD screen with the current zone and talkgroup info."""
        current_zone = self.currentFile.zone_names[self.currentFile.current_zone_index]
        self.lblZone.setText(current_zone)  

        current_channel = self.currentFile.get_channel_by_number(self.currentFile.current_tg_index)

        if current_channel:
            tg_name = current_channel["name"]
            tg_number = current_channel["channel_number"]

            self.lblChannelName_2.setText(tg_name)
            self.lcdNumber.display(tg_number)

            if current_channel["type"] == "scan":
                self.lblChanelType.setText("\uf002")  
            else:
                self.lblChanelType.setText("\uf0c0")  

        else:
            self.lblChannelName_2.setText("No Channel")
            self.lcdNumber.display(0)

        print("[DEBUG] UI Updated - No extra change_talkgroup() calls")

    def close_app(self):
        """Closes the application."""
        print("Closing application...")
        if(self.speech_on):
            self.speech.stop()  # Stop speech engine before exit
        self.op25.stop()
        self.close()

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
        self.change_talkgroup()  # Apply the new talkgroup or scan list

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
        self.change_talkgroup()  # Apply the new talkgroup or scan list

    def zone_up(self):
        """Moves to the next zone, loops back if at the last zone."""
        next_zone = self.currentFile.get_next_zone(self.currentFile.current_zone_index)
        if next_zone:
            self.currentFile.current_zone_index = self.currentFile.zone_names.index(next_zone)
            self.load_first_channel()  # Load first channel of the new zone

            # ✅ Only run if a channel was actually loaded
            if self.currentFile.current_tg_index is not None:
                self.update_display()
                current_zone = self.currentFile.zone_names[self.currentFile.current_zone_index]
                first_channel = self.currentFile.get_channel_by_number(self.currentFile.current_tg_index)
                if(self.speech_on): 
                    self.speech.speak(f"{current_zone} - {first_channel['name'] if first_channel else 'No Channels'}")

            self.change_talkgroup()

    def zone_down(self):
        """Moves to the previous zone, loops to the last if at the first."""
        prev_zone = self.currentFile.get_previous_zone(self.currentFile.current_zone_index)
        if prev_zone:
            self.currentFile.current_zone_index = self.currentFile.zone_names.index(prev_zone)
            self.load_first_channel()  # Load first channel of the new zone

            # ✅ Only run if a channel was actually loaded
            if self.currentFile.current_tg_index is not None:
                self.update_display()
                current_zone = self.currentFile.zone_names[self.currentFile.current_zone_index]
                first_channel = self.currentFile.get_channel_by_number(self.currentFile.current_tg_index)
                if(self.speech_on): 
                    self.speech.speak(f"{current_zone} - {first_channel['name'] if first_channel else 'No Channels'}")

            self.change_talkgroup()

    def load_first_channel(self):
        """Loads the first channel of the current zone and applies its talkgroup settings."""
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
        """Applies the correct talkgroup or scan list based on the current channel."""

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

        # Assuming update_display refreshes the UI to reflect current channel
        self.update_display() 
        
        # Speak the channel name if speech is enabled
        if self.speech_on:
            self.speech.speak(selected_channel["name"])

    def select_talkgroup(self, item):
        """Handles user selecting a talkgroup from the menu and applies it."""
        
        # Ensure current zone index is within bounds
        if self.currentFile.current_zone_index >= len(self.currentFile.zone_names):
            print("[ERROR] Current zone index out of bounds")
            return
        
        current_zone = self.currentFile.zone_names[self.currentFile.current_zone_index]
        talkgroup_name = item.text()

        # Attempt to find the selected channel from JSON using the current zone and talkgroup name
        selected_channel = next(
            (ch for ch in self.currentFile.get_channels_by_zone(current_zone) if ch["name"] == talkgroup_name),
            None
        )

        if not selected_channel:
            print("[ERROR] Selected talkgroup not found in JSON")
            return  # Exit function if selection is invalid

        # Update the currently selected talkgroup index
        self.currentFile.current_tg_index = selected_channel["channel_number"]

        # Update the display and change to the new talkgroup if the index is valid
        self.update_display()  # Assuming update_display refreshes the UI to reflect current channel
        self.change_talkgroup()  # Apply the new talkgroup settings

        # Hide the talkgroup menu after selection
        self.toggle_talkgroup_menu()  # Assuming this toggles visibility of the menu

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()  # ✅ Instantiating MainWindow directly
    mainWindow.show()
    sys.exit(app.exec())