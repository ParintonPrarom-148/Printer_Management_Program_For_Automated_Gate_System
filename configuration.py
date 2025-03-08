from PyQt6.QtWidgets import QWidget, QToolButton, QMenu, QApplication, QLineEdit, QPushButton, QFileDialog,QComboBox
from PyQt6.QtCore import QDir,QProcess 
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


    def show_save_dialog(self):
        # Open a file dialog to select a folder and set the folder path to the QLineEdit
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            printer_name = self.textPrinterLogFileName.text()
            full_path_logfile = os.path.join(folder_path, printer_name)
            full_path_config = os.path.join(full_path_logfile, "config.json")
            self.textPrinterLogFileLocation.setText(full_path_logfile)
            self.textKioskLogFileLocation.setText(full_path_config)

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
                
                textLocationFilePrinter1 = self.findChild(QLineEdit, 'textLocationFilePrinter1')
                textLocationFilePrinter2 = self.findChild(QLineEdit, 'textLocationFilePrinter2')
                
                # ตั้งค่าจาก JSON สำหรับ QLineEdit
                textPrinterModel1.setText(printer_setup_1.get('PrinterModel', ''))
                textServerURL1.setText(printer_setup_1.get('ServerURL', ''))
                
                textPrinterModel2.setText(printer_setup_2.get('PrinterModel', ''))
                textServerURL2.setText(printer_setup_2.get('ServerURL', ''))

                textSetting1.setText(printer_setup_1.get('Setting', ''))
                textSetting2.setText(printer_setup_2.get('Setting', ''))
                
                textLocationFilePrinter1.setText(printer_setup_1.get('LocationFilePrinter', ''))
                textLocationFilePrinter2.setText(printer_setup_2.get('LocationFilePrinter', ''))

                # อ่านค่า PRINTER_LOGFILE_LOCATION จาก .env
                printer_logfile_location = os.getenv("PRINTER_LOGFILE_LOCATION")
                if not printer_logfile_location:
                    print("❌ ไม่มีการระบุ PRINTER_LOGFILE_LOCATION ใน .env")
                    return

                # สร้างโฟลเดอร์ตามค่า Setting (Primary หรือ Secondary)
                setting1 = printer_setup_1.get('Setting', '')
                setting2 = printer_setup_2.get('Setting', '')

                if setting1:
                    folder1 = os.path.join(printer_logfile_location, setting1)
                    os.makedirs(folder1, exist_ok=True)  # สร้างโฟลเดอร์ถ้าไม่มี
                    textLocationFilePrinter1.setText(folder1)

                if setting2:
                    folder2 = os.path.join(printer_logfile_location, setting2)
                    os.makedirs(folder2, exist_ok=True)  # สร้างโฟลเดอร์ถ้าไม่มี
                    textLocationFilePrinter2.setText(folder2)

                # เพิ่มข้อมูลใน ComboBox
                cbPrinterModel1 = self.findChild(QComboBox, 'cbPrinterModel1')
                cbPrinterModel2 = self.findChild(QComboBox, 'cbPrinterModel2')

                # ตั้งค่า placeholder text สำหรับ ComboBox
                cbPrinterModel1.setPlaceholderText("เลือกรุ่นเครื่องพิมพ์")
                cbPrinterModel2.setPlaceholderText("เลือกรุ่นเครื่องพิมพ์")

                # เพิ่มรายการเครื่องพิมพ์
                cbPrinterModel1.addItems(["VKP80III", "FTP-639"])
                cbPrinterModel2.addItems(["VKP80III", "FTP-639"])

                # เลือกค่าที่ตรงกับค่าที่ได้จาก JSON
                printer_model_1 = printer_setup_1.get('PrinterModel', '')
                printer_model_2 = printer_setup_2.get('PrinterModel', '')

                if printer_model_1:
                    cbPrinterModel1.setCurrentText(printer_model_1)
                if printer_model_2:
                    cbPrinterModel2.setCurrentText(printer_model_2)

                # เชื่อมต่อ signal สำหรับการเลือกใน ComboBox
                cbPrinterModel1.currentTextChanged.connect(lambda: self.update_printer_model(cbPrinterModel1, textPrinterModel1))
                cbPrinterModel2.currentTextChanged.connect(lambda: self.update_printer_model(cbPrinterModel2, textPrinterModel2))
            
            print("✅ โหลดข้อมูลจาก JSON สำเร็จ")

        except FileNotFoundError:
            print(f"❌ ไม่พบไฟล์ JSON ที่ {json_file_path}")
        except json.JSONDecodeError:
            print("❌ เกิดข้อผิดพลาดในการอ่านไฟล์ JSON")
        except Exception as e:
            print(f"❌ Error loading JSON: {e}")

    def update_printer_model(self, combo_box, text_edit):
        # อัปเดตค่าของ QLineEdit เมื่อเลือกจาก ComboBox
        selected_model = combo_box.currentText()
        text_edit.setText(selected_model)

    def save_data_to_json(self):
        try:
            load_dotenv()  # โหลดค่าจาก .env ก่อน
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

            textLocationFilePrinter1 = self.findChild(QLineEdit, 'textLocationFilePrinter1')
            textLocationFilePrinter2 = self.findChild(QLineEdit, 'textLocationFilePrinter2')

            # อ่านข้อมูลจาก QLineEdit
            printer_name1 = textPrinterModel1.text().strip() if textPrinterModel1 else ''
            server_url1 = textServerURL1.text().strip() if textServerURL1 else ''
            printer_name2 = textPrinterModel2.text().strip() if textPrinterModel2 else ''
            server_url2 = textServerURL2.text().strip() if textServerURL2 else ''

            setting1 = textSetting1.text().strip() if textSetting1 else ''
            setting2 = textSetting2.text().strip() if textSetting2 else ''

            location_file_printer1 = textLocationFilePrinter1.text().strip() if textLocationFilePrinter1 else ''
            location_file_printer2 = textLocationFilePrinter2.text().strip() if textLocationFilePrinter2 else ''

            # เปิดไฟล์ JSON และโหลดข้อมูล
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            # แก้ไขข้อมูล JSON
            data['PrinterSetup1'][0]['PrinterModel'] = printer_name1
            data['PrinterSetup1'][0]['ServerURL'] = server_url1
            data['PrinterSetup1'][0]['LocationFilePrinter'] = location_file_printer1
            data['PrinterSetup2'][0]['PrinterModel'] = printer_name2
            data['PrinterSetup2'][0]['ServerURL'] = server_url2
            data['PrinterSetup2'][0]['LocationFilePrinter'] = location_file_printer2

            # อัปเดตค่า Setting
            data['PrinterSetup1'][0]['Setting'] = setting1
            data['PrinterSetup2'][0]['Setting'] = setting2

            # บันทึก JSON กลับลงไฟล์
            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            
            

            print("✅ Data saved successfully in JSON and .env!")
            self. update_env_variables(printer_name1,printer_name2)

        except Exception as e:
            print(f"❌ Error saving data: {e}")
    def update_env_variables(self, printer_name1,printer_name2):
        load_dotenv(override=True)
        # ✅ บันทึกค่า printer_name1 และ printer_name2 ลงใน .env
        set_key(env_file, "LANE_print1", printer_name1)
        set_key(env_file, "LANE_print2", printer_name2)
        QProcess.startDetached(sys.executable, sys.argv)  # เปิดโปรแกรมใหม่
        sys.exit(0)  # ปิดโปรแกรมเก่า

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
