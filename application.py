# Import necessary modules
from dotenv import load_dotenv, set_key, dotenv_values  # Used for environment variables management
from PyQt6.QtWidgets import QWidget, QToolButton, QMenu, QLineEdit, QPushButton, QApplication, QFileDialog  # PyQt6 UI components
from PyQt6 import uic  # For loading UI created by Qt Designer
from PyQt6.QtCore import QProcess  # For handling external processes (not used in this snippet)
import json  # To handle JSON file reading/writing
import sys  # For system operations like reloading the program
import os  # For file and folder operations

env_file = ".env"  # Path to the environment file

class Ui_Application(QWidget):  # Define the main UI class
    def __init__(self):
        super().__init__()  # Initialize the QWidget (parent class)

        # Load UI created by Qt Designer
        uic.loadUi('Designer/application.ui', self)
        load_dotenv()  # Load the .env file to access environment variables
        self.load_config()  # Load configuration settings

        # Link QToolButton named 'btnmenu' and create the dropdown menu
        self.btnmenu = self.findChild(QToolButton, 'btnmenu')
        self.create_menu()  # Create menu items

        # Link QLineEdit and QPushButton elements for user interaction
        self.setup_ui_elements()

    def create_menu(self):
        # Create a QMenu with options for dropdown
        menu = QMenu(self)
        menu.addAction('Monitoring', self.on_monitoring_selected)  # Action for monitoring
        menu.addAction('Configuration Setup', self.on_configuration_selected)  # Action for configuration setup
        menu.addAction('Application Setup', self.on_application_selected)  # Action for application setup
        self.btnmenu.setMenu(menu)  # Attach the menu to the button
        self.btnmenu.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)  # Popup mode for dropdown

    def setup_ui_elements(self):
        # Initialize QLineEdit fields for user input
        self.textLocation = self.findChild(QLineEdit, 'textLocation')
        self.textGateLane = self.findChild(QLineEdit, 'textGateLane')
        self.textTerminal = self.findChild(QLineEdit, 'textTerminal')
        self.textKioskIP = self.findChild(QLineEdit, 'textKioskIP')
        self.textSetTimeSendLog = self.findChild(QLineEdit, 'textSetTimeSendLog')
        self.textKioskLogFileLocation = self.findChild(QLineEdit, 'textKioskLogFileLocation')
        self.textURLWebService = self.findChild(QLineEdit, 'textURLWebService')
        self.textPrinterLogFileName = self.findChild(QLineEdit, 'textPrinterLogFileName')
        self.textPrinterLogFileLocation = self.findChild(QLineEdit, 'textPrinterLogFileLocation')
        self.textRemark = self.findChild(QLineEdit, 'textRemark')

        # Initialize buttons and connect them to functions
        self.btnSelectPrinterLogfileLocation = self.findChild(QPushButton, 'btnSelectPrinterLogfileLocation')
        self.btnClearEnv = self.findChild(QPushButton, 'btnClearEnv')
        self.btnSaveApplicationSetup = self.findChild(QPushButton, 'btnSaveApplicationSetup')

        # Connect buttons to respective methods
        self.btnClearEnv.clicked.connect(self.clear_env)
        self.btnSelectPrinterLogfileLocation.clicked.connect(self.show_save_dialog)
        self.btnSaveApplicationSetup.clicked.connect(self.save_data_to_json)

    def load_config(self):
        try:
            # Load configuration from a JSON file based on the path from .env
            json_file_path = os.getenv("KIOSK_LOGFILE_LOCATION")

            if not json_file_path:
                print("ไม่พบค่าของ KIOSK_LOGFILE_LOCATION ในไฟล์ .env")
                return

            # Open the JSON file and load data
            with open(json_file_path, 'r') as file:
                data = json.load(file)

            app_setup = data.get("ApplicationSetup", [{}])[0]

            # Set the loaded configuration data into QLineEdit widgets
            self.textLocation.setText(app_setup.get("Location", ""))
            self.textGateLane.setText(app_setup.get("GateLane", ""))
            self.textTerminal.setText(app_setup.get("Terminal", ""))
            self.textKioskIP.setText(app_setup.get("KioskIP", ""))
            self.textSetTimeSendLog.setText(app_setup.get("SetTimeSendLog", ""))
            self.textKioskLogFileLocation.setText(app_setup.get("KioskLocationLogFile", ""))
            self.textURLWebService.setText(app_setup.get("URLWebService", ""))
            self.textPrinterLogFileName.setText(app_setup.get("PrinterLogFileName", ""))
            self.textPrinterLogFileLocation.setText(app_setup.get("PrinterLogFileLocation", ""))
            self.textRemark.setText(app_setup.get("Remark", ""))

            # Check if folder for PrinterLogFileLocation exists and create it if needed
            printer_log_file_location = app_setup.get("PRINTER_LOGFILE_LOCATION", "")
            if printer_log_file_location:
                self.check_and_create_folder(printer_log_file_location)

        except Exception as e:
            print(f"❌ Error loading config: {e}")

    def check_and_create_folder(self, folder_path):
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)  # Create the folder if it doesn't exist
            print(f"โฟลเดอร์ถูกสร้าง: {folder_path}")
        else:
            print(f"โฟลเดอร์มีอยู่แล้ว: {folder_path}")

    def show_save_dialog(self):
        # Open a file dialog to select a folder and set the folder path to the QLineEdit
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            printer_name = self.textPrinterLogFileName.text()
            full_path_logfile = os.path.join(folder_path, printer_name)
            full_path_config = os.path.join(full_path_logfile, "config.json")
            self.textPrinterLogFileLocation.setText(full_path_logfile)
            self.textKioskLogFileLocation.setText(full_path_config)

    def save_data_to_json(self):
        try:
            # Collect all the data from QLineEdit fields
            location = self.textLocation.text()
            gate_lane = self.textGateLane.text()
            terminal = self.textTerminal.text()
            kiosk_ip = self.textKioskIP.text()
            set_time_send_log = self.textSetTimeSendLog.text()
            kiosk_location_log_file = self.textKioskLogFileLocation.text()
            url_web_service = self.textURLWebService.text()
            printer_log_file_name = self.textPrinterLogFileName.text()
            printer_log_file_location = self.textPrinterLogFileLocation.text()
            remark = self.textRemark.text()

            # Ensure the printer log folder exists
            self.ensure_printer_log_folder(printer_log_file_location)

            # Check if the path for config.json is set correctly
            if not kiosk_location_log_file:
                print("❌ ไม่มีการระบุ path สำหรับไฟล์ config.json ใน .env")
                return

            json_file_path = kiosk_location_log_file

            # If the JSON file doesn't exist, create a new one
            if not os.path.exists(json_file_path):
                print(f"⚠️ ไม่พบไฟล์ {json_file_path} กำลังสร้างไฟล์ใหม่...")
                self.create_initial_json(json_file_path)

            # Read the JSON file and update data
            with open(json_file_path, 'r') as file:
                data = json.load(file)

            app_setup = data.get("ApplicationSetup", [{}])[0]
            app_setup.update({
                "Location": location,
                "GateLane": gate_lane,
                "Terminal": terminal,
                "KioskIP": kiosk_ip,
                "SetTimeSendLog": set_time_send_log,
                "KioskLocationLogFile": kiosk_location_log_file,
                "URLWebService": url_web_service,
                "PrinterLogFileName": printer_log_file_name,
                "PrinterLogFileLocation": printer_log_file_location,
                "Remark": remark
            })

            # Save the updated data back to the JSON file
            with open(json_file_path, 'w') as file:
                json.dump(data, file, indent=4)

            print("✅ Data saved successfully.")
            self.update_env_variables(printer_log_file_location, kiosk_location_log_file, url_web_service, set_time_send_log)

        except Exception as e:
            print(f"❌ Error saving data: {e}")

    def ensure_printer_log_folder(self, printer_log_location):
        if printer_log_location and not os.path.exists(printer_log_location):
            os.makedirs(printer_log_location, exist_ok=True)
            print(f"📂 สร้างโฟลเดอร์ printer_log: {printer_log_location}")

    def create_initial_json(self, json_file_path):
        # Create an initial JSON file with default printer settings
        data = {
            "ApplicationSetup": [{}],
            "PrinterSetup1": [
                {"PrinterModel": "", "Setting": "Primary", "LocationFilePrinter": ""}
            ],
            "PrinterSetup2": [
                {"PrinterModel": "", "Setting": "Secondary", "LocationFilePrinter": ""}
            ]
        }

        with open(json_file_path, 'w') as file:
            json.dump(data, file, indent=4)

    def update_env_variables(self, printer_log_file_location, kiosk_location_log_file, url_web_service, set_time_send_log):
        load_dotenv(override=True)
        # Update .env file with new settings
        set_key(env_file, "PRINTER_LOGFILE_LOCATION", os.path.normpath(printer_log_file_location))
        set_key(env_file, "KIOSK_LOGFILE_LOCATION", os.path.normpath(kiosk_location_log_file))
        set_key(env_file, "SERVER_URL", url_web_service)
        set_key(env_file, "POST_PRINTER_STATUS_SECOND_INTERVAL", set_time_send_log)
        QProcess.startDetached(sys.executable, sys.argv)  # เปิดโปรแกรมใหม่
        sys.exit(0)  # ปิดโปรแกรมเก่า

    def clear_env(self):
        # Clear environment variables except for USERNAME and PASSWORD
        env_variables = dotenv_values('.env')

        # Remove unwanted environment variables
        for key in list(env_variables.keys()):
            if key not in ['USERNAME', 'PASSWORD', 'PRINTER_LOGFILE_LOCATION', 'KIOSK_LOGFILE_LOCATION']:
                set_key('.env', key, '')  # Clear the key value

        print("✔️ ข้อมูลใน .env ถูกลบเรียบร้อยแล้ว (ยกเว้น USERNAME และ PASSWORD)")

    def on_monitoring_selected(self):
        # Switch to the monitoring window
        self.close()
        from monitoring import Ui_Monitoring
        self.new_window = Ui_Monitoring()
        self.new_window.show()

    def on_configuration_selected(self):
        # Switch to the configuration window
        self.close()
        from configuration import Ui_Configuration
        self.new_window = Ui_Configuration()
        self.new_window.show()

    def on_application_selected(self):
        # Switch to the application setup window
        self.close()  # Close current window
        from application import Ui_Application  # Import application setup UI
        self.new_window = Ui_Application()  # Create new window instance
        self.new_window.show()  # Show the new window
