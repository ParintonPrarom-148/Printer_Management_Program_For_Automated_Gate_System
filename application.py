# นำเข้าโมดูลที่จำเป็น
from dotenv import load_dotenv, set_key, dotenv_values  # ใช้สำหรับการจัดการตัวแปรสภาพแวดล้อม
from PyQt6.QtWidgets import QWidget, QToolButton, QMenu, QLineEdit, QPushButton, QApplication, QFileDialog  # ส่วนประกอบ UI ของ PyQt6
from PyQt6 import uic  # สำหรับโหลด UI ที่สร้างด้วย Qt Designer
from PyQt6.QtCore import QProcess  # สำหรับการจัดการกับกระบวนการภายนอก (ไม่ใช้ในส่วนนี้)
import json  # ใช้สำหรับอ่าน/เขียนไฟล์ JSON
import sys  # สำหรับการดำเนินการระบบ เช่น การโหลดโปรแกรมใหม่
import os  # สำหรับการทำงานกับไฟล์และโฟลเดอร์
# กำหนดเส้นทางไฟล์ .ui โดยใช้ __file__ เพื่อให้ทำงานได้จากไฟล์ executable
ui_file = os.path.join(os.path.dirname(__file__), 'Designer', 'application.ui')
env_file = ".env"  # เส้นทางไฟล์สภาพแวดล้อม

class Ui_Application(QWidget):  # กำหนดคลาส UI หลัก
    def __init__(self):
        super().__init__()  # เริ่มต้น QWidget (คลาสแม่)

        uic.loadUi(ui_file, self)
        load_dotenv()  # โหลดไฟล์ .env เพื่อเข้าถึงตัวแปรสภาพแวดล้อม
        self.load_config()  # โหลดการตั้งค่าจากคอนฟิก

        # ลิงก์ QToolButton ที่ชื่อ 'btnmenu' และสร้างเมนูดรอปดาวน์
        self.btnmenu = self.findChild(QToolButton, 'btnmenu')
        self.create_menu()  # สร้างรายการในเมนู
        set_key(env_file, "USERNAME",("Pluem"))
        set_key(env_file, "PASSWORD",("1234"))
        # ลิงก์ QLineEdit และ QPushButton สำหรับการโต้ตอบของผู้ใช้
        self.setup_ui_elements()

    def create_menu(self):
        # สร้าง QMenu พร้อมตัวเลือกในเมนูดรอปดาวน์
        menu = QMenu(self)
        menu.addAction('Monitoring', self.on_monitoring_selected)  # ตัวเลือกสำหรับการตรวจสอบ
        menu.addAction('Configuration Setup', self.on_configuration_selected)  # ตัวเลือกสำหรับการตั้งค่าคอนฟิก
        menu.addAction('Application Setup', self.on_application_selected)  # ตัวเลือกสำหรับการตั้งค่าแอปพลิเคชัน
        self.btnmenu.setMenu(menu)  # แนบเมนูเข้ากับปุ่ม
        self.btnmenu.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)  # โหมดป๊อปอัพสำหรับดรอปดาวน์

    def setup_ui_elements(self):
        # เริ่มต้น QLineEdit สำหรับรับข้อมูลจากผู้ใช้
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

        # เริ่มต้นปุ่มและเชื่อมต่อกับฟังก์ชันที่เกี่ยวข้อง
        self.btnSelectPrinterLogfileLocation = self.findChild(QPushButton, 'btnSelectPrinterLogfileLocation')
        self.btnClearEnv = self.findChild(QPushButton, 'btnClearEnv')
        self.btnSaveApplicationSetup = self.findChild(QPushButton, 'btnSaveApplicationSetup')

        # เชื่อมต่อปุ่มกับฟังก์ชันที่เกี่ยวข้อง
        self.btnSelectPrinterLogfileLocation.clicked.connect(self.show_save_dialog)
        self.btnSaveApplicationSetup.clicked.connect(self.save_data_to_json)

    def load_config(self):
        try:
            # โหลดคอนฟิกจากไฟล์ JSON ตามเส้นทางจาก .env
            json_file_path = os.getenv("KIOSK_LOGFILE_LOCATION")

            if not json_file_path:
                print("ไม่พบค่าของ KIOSK_LOGFILE_LOCATION ในไฟล์ .env")
                return

            # เปิดไฟล์ JSON และโหลดข้อมูล
            with open(json_file_path, 'r') as file:
                data = json.load(file)

            app_setup = data.get("ApplicationSetup", [{}])[0]

            # ตั้งค่าข้อมูลที่โหลดมาใส่ใน QLineEdit
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

            # ตรวจสอบว่าโฟลเดอร์สำหรับ PrinterLogFileLocation มีอยู่หรือไม่และสร้างถ้าจำเป็น
            printer_log_file_location = app_setup.get("PRINTER_LOGFILE_LOCATION", "")
            if printer_log_file_location:
                self.check_and_create_folder(printer_log_file_location)

        except Exception as e:
            print(f"❌ Error loading config: {e}")

    def check_and_create_folder(self, folder_path):
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)  # สร้างโฟลเดอร์ถ้ายังไม่มี
            print(f"โฟลเดอร์ถูกสร้าง: {folder_path}")
        else:
            print(f"โฟลเดอร์มีอยู่แล้ว: {folder_path}")

    def show_save_dialog(self):
        # เปิดหน้าต่างไฟล์เพื่อเลือกโฟลเดอร์และตั้งเส้นทางโฟลเดอร์ใน QLineEdit
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            printer_name = self.textPrinterLogFileName.text()
            full_path_logfile = os.path.join(folder_path, printer_name)
            full_path_config = os.path.join(full_path_logfile, "config.json")
            self.textPrinterLogFileLocation.setText(full_path_logfile)
            self.textKioskLogFileLocation.setText(full_path_config)

    def save_data_to_json(self):
        try:
            # รวบรวมข้อมูลจาก QLineEdit
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

            # ตรวจสอบให้แน่ใจว่าโฟลเดอร์สำหรับ printer_log_location มีอยู่
            self.ensure_printer_log_folder(printer_log_file_location)

            # ตรวจสอบว่าได้ตั้งค่า path สำหรับ config.json อย่างถูกต้องหรือไม่
            if not kiosk_location_log_file:
                print("❌ ไม่มีการระบุ path สำหรับไฟล์ config.json ใน .env")
                return

            json_file_path = kiosk_location_log_file

            # หากไฟล์ JSON ไม่มีอยู่ ให้สร้างใหม่
            if not os.path.exists(json_file_path):
                print(f"⚠️ ไม่พบไฟล์ {json_file_path} กำลังสร้างไฟล์ใหม่...")
                self.create_initial_json(json_file_path)

            # อ่านไฟล์ JSON และอัพเดตข้อมูล
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

            # บันทึกข้อมูลที่อัพเดตกลับไปยังไฟล์ JSON
            with open(json_file_path, 'w') as file:
                json.dump(data, file, indent=4)

            print("✅ Data saved successfully.")
            self.update_env_variables(location, printer_log_file_location, kiosk_location_log_file, url_web_service, set_time_send_log,kiosk_ip)

        except Exception as e:
            print(f"❌ Error saving data: {e}")

    def ensure_printer_log_folder(self, printer_log_location):
        if printer_log_location and not os.path.exists(printer_log_location):
            os.makedirs(printer_log_location, exist_ok=True)
            print(f"📂 สร้างโฟลเดอร์ printer_log: {printer_log_location}")

    def create_initial_json(self, json_file_path):
        # สร้างไฟล์ JSON เริ่มต้นด้วยการตั้งค่าปริ้นเตอร์เริ่มต้น
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

    def update_env_variables(self, location, printer_log_file_location, kiosk_location_log_file, url_web_service, set_time_send_log,kiosk_ip):
        load_dotenv(override=True)
        # อัพเดตไฟล์ .env ด้วยการตั้งค่าใหม่
        set_key(env_file, "LOCATION", location)
        set_key(env_file, "PRINTER_LOGFILE_LOCATION", os.path.normpath(printer_log_file_location))
        set_key(env_file, "KIOSK_LOGFILE_LOCATION", os.path.normpath(kiosk_location_log_file))
        set_key(env_file, "SERVER_URL", url_web_service)
        set_key(env_file, "KIOSK_URL", kiosk_ip)
        set_key(env_file, "POST_PRINTER_STATUS_SECOND_INTERVAL", set_time_send_log)
        QProcess.startDetached(sys.executable, sys.argv)  # เปิดโปรแกรมใหม่
        sys.exit(0)  # ปิดโปรแกรมเก่า

    def on_monitoring_selected(self):
        # สลับไปที่หน้าต่างการตรวจสอบ
        self.close()

    def on_configuration_selected(self):
        # สลับไปที่หน้าต่างการตั้งค่าคอนฟิก
        self.close()
        from configuration import Ui_Configuration
        self.new_window = Ui_Configuration()
        self.new_window.show()

    def on_application_selected(self):
        # สลับไปที่หน้าต่างการตั้งค่าแอปพลิเคชัน
        self.close()  # ปิดหน้าต่างปัจจุบัน
        from application import Ui_Application  # นำเข้า UI ของการตั้งค่าแอปพลิเคชัน
        self.new_window = Ui_Application()  # สร้างอินสแตนซ์ของหน้าต่างใหม่
        self.new_window.show()  # แสดงหน้าต่างใหม่
