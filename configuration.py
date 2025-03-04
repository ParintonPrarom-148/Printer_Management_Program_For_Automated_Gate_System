from PyQt6.QtWidgets import QWidget, QToolButton, QMenu, QApplication, QLineEdit, QPushButton
from PyQt6 import uic
import sys
import json
import os
from dotenv import load_dotenv, set_key
env_file = ".env"

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

        # เชื่อมต่อปุ่ม Switch Setting
        self.btnSwitchSetting = self.findChild(QPushButton, 'btnSwitchSetting')
        if self.btnSwitchSetting:
            self.btnSwitchSetting.clicked.connect(self.switch_printer_settings)

    def load_data_from_json(self):
        
        try:
            json_file_path = os.getenv("KIOSK_LOGFILE_LOCATION")

            if not json_file_path:
                print("❌ ไม่มีการระบุ path สำหรับไฟล์ config.json ใน .env")
                return
            
            # เปิดไฟล์ JSON และโหลดข้อมูล
            with open(json_file_path, 'r') as file:
                data = json.load(file)

                # ดึงข้อมูลจาก PrinterSetup1 และ PrinterSetup2
                printer_setup_1 = data.get('PrinterSetup1', [])[0] if data.get('PrinterSetup1') else {}
                printer_setup_2 = data.get('PrinterSetup2', [])[0] if data.get('PrinterSetup2') else {}

                # ตั้งค่าให้กับ QLineEdit
                textPrinterModel1 = self.findChild(QLineEdit, 'textPrinterModel1')
                textServerURL1 = self.findChild(QLineEdit, 'textServerURL1')
                textPrinterModel2 = self.findChild(QLineEdit, 'textPrinterModel2')
                textServerURL2 = self.findChild(QLineEdit, 'textServerURL2')

                textSetting1 = self.findChild(QLineEdit, 'textSetting1')
                textSetting2 = self.findChild(QLineEdit, 'textSetting2')

                # ตั้งค่า text field ด้วยข้อมูลจาก JSON
                if textPrinterModel1:
                    textPrinterModel1.setText(printer_setup_1.get('PrinterModel', ''))
                if textServerURL1:
                    textServerURL1.setText(printer_setup_1.get('ServerURL', ''))
                if textPrinterModel2:
                    textPrinterModel2.setText(printer_setup_2.get('PrinterModel', ''))
                if textServerURL2:
                    textServerURL2.setText(printer_setup_2.get('ServerURL', ''))

                # ตั้งค่า "Setting" ลงใน QLineEdit
                if textSetting1:
                    textSetting1.setText(printer_setup_1.get('Setting', ''))
                if textSetting2:
                    textSetting2.setText(printer_setup_2.get('Setting', ''))

                # ตั้งค่า LocationFilePrinter ลงใน QLineEdit ใหม่
                textLocationFilePrinter1 = self.findChild(QLineEdit, 'textLocationFilePrinter1')
                textLocationFilePrinter2 = self.findChild(QLineEdit, 'textLocationFilePrinter2')

                if textLocationFilePrinter1:
                    textLocationFilePrinter1.setText(printer_setup_1.get('LocationFilePrinter', ''))
                if textLocationFilePrinter2:
                    textLocationFilePrinter2.setText(printer_setup_2.get('LocationFilePrinter', ''))
            
            print("✅ โหลดข้อมูลจาก JSON สำเร็จ")

        except FileNotFoundError:
            print(f"❌ ไม่พบไฟล์ JSON ที่ {json_file_path}")
        except json.JSONDecodeError:
            print("❌ เกิดข้อผิดพลาดในการอ่านไฟล์ JSON")
        except Exception as e:
            print(f"❌ Error loading JSON: {e}")

    def save_data_to_json(self):
        try:
            load_dotenv()  # Ensure .env is loaded first
            json_file_path = os.getenv("KIOSK_LOGFILE_LOCATION")
            if not json_file_path:
                print("❌ ไม่พบ path สำหรับ KIOSK_LOGFILE_LOCATION ใน .env")
                return

            # ดึงข้อมูลจาก QLineEdit
            textPrinterModel1 = self.findChild(QLineEdit, 'textPrinterModel1')
            textServerURL1 = self.findChild(QLineEdit, 'textServerURL1')
            textPrinterModel2 = self.findChild(QLineEdit, 'textPrinterModel2')
            textServerURL2 = self.findChild(QLineEdit, 'textServerURL2')

            textSetting1 = self.findChild(QLineEdit, 'textSetting1')
            textSetting2 = self.findChild(QLineEdit, 'textSetting2')

            # ดึงข้อมูล LocationFilePrinter
            textLocationFilePrinter1 = self.findChild(QLineEdit, 'textLocationFilePrinter1')
            textLocationFilePrinter2 = self.findChild(QLineEdit, 'textLocationFilePrinter2')

            # อ่านข้อมูลจาก QLineEdit
            printer_name1 = textPrinterModel1.text() if textPrinterModel1 else ''
            server_url1 = textServerURL1.text() if textServerURL1 else ''
            printer_name2 = textPrinterModel2.text() if textPrinterModel2 else ''
            server_url2 = textServerURL2.text() if textServerURL2 else ''

            setting1 = textSetting1.text() if textSetting1 else ''
            setting2 = textSetting2.text() if textSetting2 else ''

            location_file_printer1 = textLocationFilePrinter1.text() if textLocationFilePrinter1 else ''
            location_file_printer2 = textLocationFilePrinter2.text() if textLocationFilePrinter2 else ''

            # เปิดไฟล์ JSON และโหลดข้อมูล
            with open(json_file_path, 'r') as file:
                data = json.load(file)

            # แก้ไขข้อมูลที่ดึงมา
            data['PrinterSetup1'][0]['PrinterModel'] = printer_name1
            data['PrinterSetup1'][0]['ServerURL'] = server_url1
            data['PrinterSetup1'][0]['LocationFilePrinter'] = location_file_printer1
            data['PrinterSetup2'][0]['PrinterModel'] = printer_name2
            data['PrinterSetup2'][0]['ServerURL'] = server_url2
            data['PrinterSetup2'][0]['LocationFilePrinter'] = location_file_printer2

            # อัปเดตค่า Setting
            data['PrinterSetup1'][0]['Setting'] = setting1
            data['PrinterSetup2'][0]['Setting'] = setting2

            # บันทึกข้อมูลลงในไฟล์ JSON
            with open(json_file_path, 'w') as file:
                json.dump(data, file, indent=4)

            print("Data saved successfully.")

        except Exception as e:
            print(f"Error saving data: {e}")

    def switch_printer_settings(self):
        try:
            load_dotenv()
            json_file_path = os.getenv("KIOSK_LOGFILE_LOCATION")
            if not json_file_path:
                print("❌ ไม่พบ path สำหรับ KIOSK_LOGFILE_LOCATION ใน .env")
                return

            # เปิดไฟล์ JSON และโหลดข้อมูล
            with open(json_file_path, 'r') as file:
                data = json.load(file)

            # ดึงข้อมูลจาก PrinterSetup1 และ PrinterSetup2
            printer_setup_1 = data.get('PrinterSetup1', [None])[0]
            printer_setup_2 = data.get('PrinterSetup2', [None])[0]

            if not printer_setup_1 or not printer_setup_2:
                print("❌ ข้อมูล PrinterSetup1 หรือ PrinterSetup2 ไม่ถูกต้อง")
                return

            # สลับข้อมูลในฟิลด์ "Setting" ระหว่าง PrinterSetup1 และ PrinterSetup2
            printer_setup_1_setting = printer_setup_1.get('Setting', '')
            printer_setup_2_setting = printer_setup_2.get('Setting', '')

            # สลับค่าของ "Setting"
            data['PrinterSetup1'][0]['Setting'] = printer_setup_2_setting
            data['PrinterSetup2'][0]['Setting'] = printer_setup_1_setting

            # บันทึกการเปลี่ยนแปลงลงในไฟล์ JSON
            with open(json_file_path, 'w') as file:
                json.dump(data, file, indent=4)

            print("Printer settings swapped successfully.")

            # โหลดข้อมูลใหม่หลังการสลับ
            self.load_data_from_json()

        except Exception as e:
            print(f"Error swapping printer settings: {e}")

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
