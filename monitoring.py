import sys
import os
import json
from dotenv import load_dotenv  # นำเข้า dotenv
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, QWidget, QToolButton, QMenu, QStackedWidget, QLabel, QMessageBox
from PyQt6.QtCore import QTimer
from datetime import datetime
# เพิ่ม path ของ `printerStatusFclTP.py`
printer_status_path = os.path.join(os.getcwd(), "python_printer_status")
sys.path.append(printer_status_path)
from printerStatusFclTP import printerStatus2  # นำเข้า printerStatus2
from printerStatusVKP80iii import printerStatus1  # นำเข้า printerStatus1

class Ui_Monitoring(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('Designer/monitoring.ui', self)  # โหลด UI
        load_dotenv(override=True)
        self.init_ui()
        self.check_config_file()
    def check_config_file(self):
        printer_logfile_location = os.getenv("PRINTER_LOGFILE_LOCATION", "")
        config_file_path = os.path.join(printer_logfile_location, "config.json")
        print(f"ไฟล์ JSON path ที่ได้: {config_file_path}")

        if not os.path.exists(config_file_path):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("แจ้งเตือน")
            msg.setText("กรุณาตั้งค่าโปรแกรมที่หน้า Application Setup ก่อนครับ")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()  # แสดงกล่องแจ้งเตือน
            return

        print("พบไฟล์ config.json")

        # โหลด JSON
        with open(config_file_path, "r", encoding="utf-8") as file:
            try:
                self.json_data = json.load(file)
            except json.JSONDecodeError:
                QMessageBox.warning(None, "ข้อผิดพลาด", "ไฟล์ config.json ไม่ถูกต้อง")
                return

        # ตรวจสอบว่า PrinterModel มีค่าหรือไม่
        printer_setup1 = self.json_data.get("PrinterSetup1", [{}])[0]
        printer_setup2 = self.json_data.get("PrinterSetup2", [{}])[0]

        if not printer_setup1.get("PrinterModel") or not printer_setup2.get("PrinterModel"):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("แจ้งเตือน")
            msg.setText("กรุณากรอกข้อมูลชื่อรุ่นเครื่องพิมพ์ทั้ง 2 เครื่องก่อนครับ")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()  # แสดงกล่องแจ้งเตือน
            return

        # กำหนดค่าเครื่องพิมพ์
        work_dir = os.getcwd()
        self.primary_printer = printerStatus1(work_dir)
        self.secondary_printer = printerStatus2(work_dir)
        
        self.current_printer = self.primary_printer
        self.is_using_secondary = False
        self.init_ui()
        self.current_selected_printer = "Primary"
        self.init_timer()
        self.update_location_label()

    def show_warning(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("แจ้งเตือน")
        msg.setText("กรุณาตั้งค่าโปรแกรมที่หน้า Application Setup ก่อนครับ")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()  # แสดงกล่องแจ้งเตือน
    # 🛠 โหลดข้อมูล JSON
    def load_json_data(self):
        # ดึงค่าจาก .env โดยใช้ชื่อ KIOSK_LOCATION_LOGFILE
        printer_location_logfile = os.getenv('PRINTER_LOGFILE_LOCATION')  # ค่า default ถ้าไม่พบตัวแปรใน .env
        json_file_path = os.path.join(printer_location_logfile, 'config.JSON')  # รวม path
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading JSON: {e}")
            return {}

    # 🔧 กำหนด UI และเชื่อมโยงปุ่มต่าง ๆ
    def init_ui(self):
        self.btnmenu = self.findChild(QToolButton, 'btnmenu')
        self.PaperJamStatus = self.findChild(QLabel, 'PaperJamStatus')
        self.OnlineStatus = self.findChild(QLabel, 'OnlineStatus')
        self.PrinterStatus = self.findChild(QLabel, 'PrinterStatus')
        self.PaperEndStatus = self.findChild(QLabel, 'PaperEndStatus')
        self.Location = self.findChild(QLabel, 'Location')
        self.PrinterModel = self.findChild(QLabel, 'PrinterModel')
        self.stackedWidget = self.findChild(QStackedWidget, 'stackedWidget')

        self.btnShowPrimaryTable = self.findChild(QPushButton, 'btnShowPrimaryTable')
        self.btnShowPrimaryTable.clicked.connect(self.show_primary_table)
        self.btnShowSecondaryTable = self.findChild(QPushButton, 'btnShowSecondaryTable')
        self.btnShowSecondaryTable.clicked.connect(self.show_secondary_table)

        self.btnLogFilePrimary = self.findChild(QPushButton, 'btnLogFilePrimary')
        self.btnLogFilePrimary.clicked.connect(self.go_to_logfile_primary)
        self.btnLogFileSecondary = self.findChild(QPushButton, 'btnLogFileSecondary')
        self.btnLogFileSecondary.clicked.connect(self.go_to_logfile_secondary)

        # ตั้งค่าเมนู
        menu = QMenu(self)
        menu.addAction('Monitoring', self.on_monitoring_selected)
        menu.addAction('Configuration Setup', self.on_configuration_selected)
        menu.addAction('Application Setup', self.on_application_selected)
        self.btnmenu.setMenu(menu)
        self.btnmenu.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

    # ⏳ ตั้งค่า Timer
    def init_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)  # อัปเดตทุก 1 วินาที

    # 🌍 อัปเดตตำแหน่ง Location จาก JSON
    def update_location_label(self):
        try:
            location = self.json_data.get('ApplicationSetup', [{}])[0].get('Location', 'ไม่พบข้อมูล')
            self.Location.setText(location)
        except Exception as e:
            print(f"Error updating location: {e}")

    # 🖨️ อัปเดตรุ่นเครื่องพิมพ์
    def update_printer_model_label(self, setting):
        model = self.get_printer_info(setting, 'PrinterModel')
        self.PrinterModel.setText(model if model else "Printer Model: Not Found")

    # 📋 โหลดข้อมูลปริ้นเตอร์
    def get_printer_info(self, setting, key):
        for setup_key in ['PrinterSetup1', 'PrinterSetup2']:
            for setup in self.json_data.get(setup_key, []):
                if setup.get('Setting') == setting:
                    return setup.get(key, '')
        return None
    def get_printer_and_paper_status(self, setting):
        for setup_key in ['PrinterSetup1', 'PrinterSetup2']:
            printer_setup = self.json_data.get(setup_key, [])
            for setup in printer_setup:
                if setup.get('Setting') == setting:
                    return setup.get('PrinterModel', '')
        return None

   # 🔄 อัปเดตสถานะ Printer & Paper
    def update_status(self):
        primary_status = self.primary_printer.get_status()
        secondary_status = self.secondary_printer.get_status()

        # ตรวจสอบว่าทั้งสองเครื่องใช้งานไม่ได้
        if primary_status["printerStatus"] == "unavailable" and secondary_status["printerStatus"] == "unavailable":
            self.lb_information.setText("⛔ เครื่องหลักเเละเครื่องสำรองมีปัญหา...")
        else:
            # ถ้าเครื่องสำรองกลับมาใช้งานได้ ให้ล้างข้อความแจ้งเตือน
            if secondary_status["printerStatus"] == "available" and self.is_using_secondary:
                self.lb_information.setText("✅ กำลังใช้เครื่องสำรอง")

        # ถ้าเครื่องหลักใช้งานไม่ได้ และยังไม่ได้เปลี่ยนไปใช้เครื่องสำรอง
        if primary_status["printerStatus"] == "unavailable" and not self.is_using_secondary:
            self.lb_information.setText("⚠️ เครื่องหลักมีปัญหากำลังพิมพ์งานที่เครื่องสำรอง")
            self.current_printer = self.secondary_printer
            self.is_using_secondary = True
            self.load_table('Secondary')

        # ถ้าเครื่องหลักกลับมาใช้งานได้ และกำลังใช้เครื่องสำรอง → สลับกลับไปที่เครื่องหลัก
        if self.is_using_secondary and primary_status["printerStatus"] == "available":
            self.lb_information.setText("✅ เครื่องหลักกลับมาใช้งานได้แล้ว กำลังสลับกลับไปที่เครื่องหลัก")
            self.current_printer = self.primary_printer
            self.is_using_secondary = False
            self.load_table('Primary')

        # ดึงข้อมูลจาก printer status
        status = self.current_printer.get_status()

        # อัปเดต QLabel ต่างๆ
        self.PrinterStatus.setText(f"{status['printerStatus']}\n")
        self.OnlineStatus.setText(f"{status['onlineStatus']}\n")
        self.PaperEndStatus.setText(f"{status['paperEndStatus']}\n")
        self.PaperJamStatus.setText(f"{status['paperJamStatus']}\n")

    # 📂 เปิด LogFile
    def go_to_logfile(self, setting):
        self.close()
        location_file = self.get_printer_info(setting, 'LocationFilePrinter')
        if location_file:
            current_time_folder = datetime.now().strftime("%Y%m%d")
            current_time_file = datetime.now().strftime("%Y%m%d%H")
            json_file_name = f"PrinterStatusJson{current_time_file}.JSON"
            json_file_path = os.path.join(location_file, 'Status', current_time_folder, json_file_name)
            from logfile import Ui_LogFile
            self.new_window = Ui_LogFile()
            self.new_window.load_logfile_data(json_file_path)
            self.new_window.show()

    def go_to_logfile_primary(self):
        self.go_to_logfile('Primary')

    def go_to_logfile_secondary(self):
        self.go_to_logfile('Secondary')

    # 🖥️ เปลี่ยนหน้า UI
    def on_monitoring_selected(self):
        self.hide()
        from monitoring import Ui_Monitoring
        self.new_window = Ui_Monitoring()
        self.new_window.show()

    def on_configuration_selected(self):
        self.hide()
        from configuration import Ui_Configuration
        self.new_window = Ui_Configuration()
        self.new_window.show()

    def on_application_selected(self):
        self.hide()
        from application import Ui_Application
        self.new_window = Ui_Application()
        self.new_window.show()

    def show_primary_table(self):
        self.current_selected_printer = "Primary"  # บันทึกว่าเลือก Primary
        self.load_table('Primary')
        self.update_printer_model_label('Primary')

        self.stackedWidget.setCurrentIndex(0)
        self.btnLogFilePrimary.show()
        self.btnLogFileSecondary.hide()

    def show_secondary_table(self):
        self.current_selected_printer = "Secondary"  # บันทึกว่าเลือก Secondary
        self.load_table('Secondary')
        self.update_printer_model_label('Secondary')

        self.stackedWidget.setCurrentIndex(1)
        self.btnLogFilePrimary.hide()
        self.btnLogFileSecondary.show()

    # 📊 โหลดข้อมูลจาก JSON และแสดงใน QTableWidget
    def load_table(self, setting):
        location_file = self.get_printer_info(setting, 'LocationFilePrinter')
        if location_file:
            # ดึงเวลาปัจจุบันในรูปแบบ YYYYMMDDHH
            current_time_folder = datetime.now().strftime("%Y%m%d")
            current_time_file = datetime.now().strftime("%Y%m%d%H")
            json_file_name = f"PrinterStatusJson{current_time_file}.JSON"
            json_file_path = os.path.join(location_file, 'Status', current_time_folder, json_file_name)

            try:
                with open(json_file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)

                    if not isinstance(data, list):
                        return
                    
                    # เรียงลำดับจากล่าสุด -> เก่าสุด
                    try:
                        data.sort(key=lambda x: datetime.strptime(x.get("timestamp", "1970-01-01 00:00:00.000"), "%Y-%m-%d %H:%M:%S.%f"), reverse=True)
                    except ValueError:
                        return

                    # ใช้ table ที่เหมาะสมกับ setting ('Primary' หรือ 'Secondary')
                    table = self.tableLogPrimary if setting == 'Primary' else self.tableLogSecondary

                    # คอลัมน์ที่ต้องการแสดง
                    columns = ['timestamp', 'senderIp', 'printerId', 'printerStatus', 'onlineStatus', 'paperEndStatus', 'paperJamStatus']

                    table.setRowCount(len(data))
                    table.setColumnCount(len(columns))
                    table.setHorizontalHeaderLabels(columns)

                    for row, entry in enumerate(data):
                        for col, key in enumerate(columns):
                            value = entry.get(key, 'N/A')
                            table.setItem(row, col, QTableWidgetItem(str(value)))

                    table.resizeColumnsToContents()  # ปรับขนาดอัตโนมัติ

            except FileNotFoundError:
                print(f"Error: The file at {json_file_path} was not found.")
            except json.JSONDecodeError:
                print("Error: The file could not be decoded as JSON.")
            except Exception as e:
                print(f"An error occurred: {e}")


    def closeEvent(self, event):
        """ หยุดการทำงานของ Thread ก่อนปิดโปรแกรม """
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Ui_Monitoring()
    window.show()
    sys.exit(app.exec())
