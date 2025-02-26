from PyQt6.QtWidgets import QWidget, QToolButton, QMenu, QApplication, QLineEdit, QPushButton
from PyQt6 import uic
import sys
import json

class Ui_Configuration(QWidget):
    def __init__(self):
        super().__init__()

        # โหลด UI ที่สร้างจาก Qt Designer
        uic.loadUi('Designer/configuration.ui', self)

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

        # ดึงข้อมูลจากไฟล์ JSON
        self.load_data_from_json()

        # เชื่อมต่อปุ่ม Save
        self.btnSaveConfigurationSetup = self.findChild(QPushButton, 'btnSaveConfigurationSetup')
        if self.btnSaveConfigurationSetup:
            self.btnSaveConfigurationSetup.clicked.connect(self.save_data_to_json)

    def load_data_from_json(self):
        # เปิดไฟล์ JSON และโหลดข้อมูล
        try:
            with open('Printer/config.json', 'r') as file:
                data = json.load(file)
                
                # ดึงข้อมูลจาก PrinterSetup1 และ PrinterSetup2
                printer_setup_1 = data.get('PrinterSetup1', [])[0] if data.get('PrinterSetup1') else {}
                printer_setup_2 = data.get('PrinterSetup2', [])[0] if data.get('PrinterSetup2') else {}

                # ตั้งค่าให้กับ QLineEdit
                textPrinterName1 = self.findChild(QLineEdit, 'textPrinterName1')
                textServerURL1 = self.findChild(QLineEdit, 'textServerURL1')
                textPrinterName2 = self.findChild(QLineEdit, 'textPrinterName2')
                textServerURL2 = self.findChild(QLineEdit, 'textServerURL2')

                # ตั้งค่า text field ด้วยข้อมูลจาก JSON
                if textPrinterName1:
                    textPrinterName1.setText(printer_setup_1.get('PrinterName', ''))
                if textServerURL1:
                    textServerURL1.setText(printer_setup_1.get('ServerURL', ''))
                if textPrinterName2:
                    textPrinterName2.setText(printer_setup_2.get('PrinterName', ''))
                if textServerURL2:
                    textServerURL2.setText(printer_setup_2.get('ServerURL', ''))

        except Exception as e:
            print(f"Error loading JSON: {e}")

    def save_data_to_json(self):
        try:
            # ดึงข้อมูลจาก QLineEdit
            textPrinterName1 = self.findChild(QLineEdit, 'textPrinterName1')
            textServerURL1 = self.findChild(QLineEdit, 'textServerURL1')
            textPrinterName2 = self.findChild(QLineEdit, 'textPrinterName2')
            textServerURL2 = self.findChild(QLineEdit, 'textServerURL2')

            # อ่านข้อมูลจาก QLineEdit
            printer_name1 = textPrinterName1.text() if textPrinterName1 else ''
            server_url1 = textServerURL1.text() if textServerURL1 else ''
            printer_name2 = textPrinterName2.text() if textPrinterName2 else ''
            server_url2 = textServerURL2.text() if textServerURL2 else ''

            # เปิดไฟล์ JSON และโหลดข้อมูล
            with open('Printer/config.json', 'r') as file:
                data = json.load(file)

            # แก้ไขข้อมูลที่ดึงมา
            data['PrinterSetup1'][0]['PrinterName'] = printer_name1
            data['PrinterSetup1'][0]['ServerURL'] = server_url1
            data['PrinterSetup2'][0]['PrinterName'] = printer_name2
            data['PrinterSetup2'][0]['ServerURL'] = server_url2

            # บันทึกข้อมูลลงในไฟล์ JSON
            with open('Printer/config.json', 'w') as file:
                json.dump(data, file, indent=4)

            print("Data saved successfully.")

        except Exception as e:
            print(f"Error saving data: {e}")

    def on_monitoring_selected(self):
        self.close()  # ปิดหน้าจอปัจจุบัน
        from monitoring import Ui_Monitoring  # โหลด UI ของหน้าจอ Monitoring
        self.new_window = Ui_Monitoring()  # สร้างอินสแตนซ์ของหน้าจอ Monitoring
        self.new_window.show()  # แสดงหน้าจอใหม่

    def on_configuration_selected(self):
         # เปิดหน้าจอ Configuration.py
        self.close()  # ปิดหน้าจอปัจจุบัน
        from configuration import Ui_Configuration  # โหลด UI ของหน้าจอ Configuration
        self.new_window = Ui_Configuration()  # สร้างอินสแตนซ์ของหน้าจอ Configuration
        self.new_window.show()  # แสดงหน้าจอใหม่

    def on_application_selected(self):
        self.close()  # ปิดหน้าจอปัจจุบัน
        from application import Ui_Application  # โหลด UI ของหน้าจอ Application
        self.new_window = Ui_Application()  # สร้างอินสแตนซ์ของหน้าจอ Application
        self.new_window.show()  # แสดงหน้าจอใหม่
