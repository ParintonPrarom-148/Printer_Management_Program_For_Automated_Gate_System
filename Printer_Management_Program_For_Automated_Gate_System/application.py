from PyQt6.QtWidgets import QWidget, QToolButton, QMenu, QLineEdit, QPushButton, QApplication
from PyQt6 import uic
import json
import sys

class Ui_Application(QWidget):
    def __init__(self):
        super().__init__()
        # โหลด UI ที่สร้างจาก Qt Designer
        uic.loadUi('Designer/application.ui', self)

        # เชื่อม QToolButton ที่ชื่อ btnmenu
        self.btnmenu = self.findChild(QToolButton, 'btnmenu')

        # สร้าง QMenu สำหรับ dropdown
        menu = QMenu(self)

        # เพิ่มเมนูโดยตรง (ไม่ใช้ QAction)
        menu.addAction('Monitoring', self.on_monitoring_selected)
        menu.addAction('Configuration Setup', self.on_configuration_selected)
        menu.addAction('Application Setup', self.on_application_selected)

        # เชื่อมเมนูกับ QToolButton
        self.btnmenu.setMenu(menu)

        # กำหนดให้เมนูแสดงเมื่อคลิก
        self.btnmenu.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        # เชื่อม QLineEdit ด้วย findChild
        self.textLocation = self.findChild(QLineEdit, 'textLocation')
        self.textGateLane = self.findChild(QLineEdit, 'textGateLane')
        self.textTerminal = self.findChild(QLineEdit, 'textTerminal')
        self.textKioskIP = self.findChild(QLineEdit, 'textKioskIP')
        self.textSetTimeSendLog = self.findChild(QLineEdit, 'textSetTimeSendLog')
        self.textKioskLocationLogFile = self.findChild(QLineEdit, 'textKioskLocationLogFile')
        self.textURLWebService = self.findChild(QLineEdit, 'textURLWebService')
        self.textPrinterLogFileName = self.findChild(QLineEdit, 'textPrinterLogFileName')
        self.textRemark = self.findChild(QLineEdit, 'textRemark')
        
        # อ่านไฟล์ JSON
        json_file_path = 'Printer/config.json'  # ปรับพาธให้ตรงกับไฟล์ของคุณ
        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)

            # ดึงข้อมูลจากส่วน ApplicationSetup
            app_setup = data.get("ApplicationSetup", [])[0]  # แค่ดึงตัวแรกใน list

            # กำหนดค่าให้กับ QLineEdit ตามข้อมูลใน JSON
            self.textLocation.setText(app_setup.get("Location", ""))
            self.textGateLane.setText(app_setup.get("GateLane", ""))
            self.textTerminal.setText(app_setup.get("Terminal", ""))
            self.textKioskIP.setText(app_setup.get("KioskIP", ""))
            self.textSetTimeSendLog.setText(app_setup.get("SetTimeSendLog", ""))
            self.textKioskLocationLogFile.setText(app_setup.get("KioskLocationLogFile", ""))
            self.textURLWebService.setText(app_setup.get("URLWebService", ""))
            self.textPrinterLogFileName.setText(app_setup.get("PrinterLogFileName", ""))
            self.textRemark.setText(app_setup.get("Remark", ""))

        except FileNotFoundError:
            print("ไม่พบไฟล์ config.json")
        except json.JSONDecodeError:
            print("เกิดข้อผิดพลาดในการอ่านไฟล์ JSON")

        # เชื่อมต่อปุ่ม Save
        self.btnSaveApplicationSetup = self.findChild(QPushButton, 'btnSaveApplicationSetup')
        if self.btnSaveApplicationSetup:
            self.btnSaveApplicationSetup.clicked.connect(self.save_data_to_json)

    def save_data_to_json(self):
        try:
            # ดึงข้อมูลจาก QLineEdit
            location = self.textLocation.text()
            gate_lane = self.textGateLane.text()
            terminal = self.textTerminal.text()
            kiosk_ip = self.textKioskIP.text()
            set_time_send_log = self.textSetTimeSendLog.text()
            kiosk_location_log_file = self.textKioskLocationLogFile.text()
            url_web_service = self.textURLWebService.text()
            printer_log_file_name = self.textPrinterLogFileName.text()
            remark = self.textRemark.text()

            # อ่านไฟล์ JSON
            json_file_path = 'Printer/config.json'  # ปรับพาธให้ตรงกับไฟล์ของคุณ
            with open(json_file_path, 'r') as file:
                data = json.load(file)

            # แก้ไขข้อมูล ApplicationSetup
            app_setup = data.get("ApplicationSetup", [])[0]  # ดึงข้อมูลตัวแรกใน list
            app_setup["Location"] = location
            app_setup["GateLane"] = gate_lane
            app_setup["Terminal"] = terminal
            app_setup["KioskIP"] = kiosk_ip
            app_setup["SetTimeSendLog"] = set_time_send_log
            app_setup["KioskLocationLogFile"] = kiosk_location_log_file
            app_setup["URLWebService"] = url_web_service
            app_setup["PrinterLogFileName"] = printer_log_file_name
            app_setup["Remark"] = remark

            # บันทึกข้อมูลกลับไปที่ไฟล์ JSON
            with open(json_file_path, 'w') as file:
                json.dump(data, file, indent=4)

            print("Data saved successfully.")

        except Exception as e:
            print(f"Error saving data: {e}")

    def on_monitoring_selected(self):
        self.close()
        from monitoring import Ui_Monitoring
        self.new_window = Ui_Monitoring()
        self.new_window.show()

    def on_configuration_selected(self):
        self.close()
        from configuration import Ui_Configuration
        self.new_window = Ui_Configuration()
        self.new_window.show()

    def on_application_selected(self):
        self.close()  # ปิดหน้าจอปัจจุบัน
        from application import Ui_Application  # โหลด UI ของหน้าจอ Application
        self.new_window = Ui_Application()  # สร้างอินสแตนซ์ของหน้าจอ Application
        self.new_window.show()  # แสดงหน้าจอใหม่
