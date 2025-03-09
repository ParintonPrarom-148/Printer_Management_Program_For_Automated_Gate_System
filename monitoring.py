import sys
import os
import json
from dotenv import load_dotenv  # นำเข้า dotenv
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, QWidget, QToolButton, QMenu, QStackedWidget, QLabel, QMessageBox
from PyQt6.QtCore import QTimer
from datetime import datetime

# กำหนดเส้นทางไฟล์ .ui โดยใช้ __file__ เพื่อให้ทำงานได้จากไฟล์ executable
ui_file = os.path.join(os.path.dirname(__file__), 'Designer', 'monitoring.ui')

# กำหนดเส้นทางไปยังโฟลเดอร์ที่เก็บข้อมูลสถานะเครื่องพิมพ์
printer_status_path = os.path.join(os.path.dirname(__file__), "python_printer_status")

# ใช้ pkg_resources เพื่อโหลดโมดูลจากไฟล์ในไฟล์ executable
if getattr(sys, 'frozen', False):
    # หากโปรแกรมรันจาก executable
    sys.path.append(printer_status_path)
else:
    # หากโปรแกรมรันจาก source code
    sys.path.append(os.path.join(os.getcwd(), "python_printer_status"))

# นำเข้าโมดูลสถานะเครื่องพิมพ์
from printerStatusFclTP import printerStatus2  
from printerStatusVKP80iii import printerStatus1  

class Ui_Monitoring(QWidget):
    def __init__(self):
        super().__init__()# โหลด UI
        uic.loadUi(ui_file, self)
        load_dotenv(override=True)  # โหลดไฟล์ .env
        self.init_ui()  # เริ่มต้น UI
        self.check_config_file()  # ตรวจสอบไฟล์ config

    def check_config_file(self):
        """ตรวจสอบและโหลดข้อมูลจากไฟล์ config.json"""
        printer_logfile_location = os.getenv("PRINTER_LOGFILE_LOCATION", "")
        config_file_path = os.path.join(printer_logfile_location, "config.json")
        print(f"ไฟล์ JSON path ที่ได้: {config_file_path}")

        if not os.path.exists(config_file_path):
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาตั้งค่าโปรแกรมที่หน้า Application Setup ก่อนครับ")
            return

        # อ่านข้อมูลจากไฟล์ config.json
        with open(config_file_path, "r", encoding="utf-8") as file:
            try:
                self.json_data = json.load(file)
            except json.JSONDecodeError:
                QMessageBox.warning(self, "ข้อผิดพลาด", "ไฟล์ config.json ไม่ถูกต้อง")
                return

        # ดึงค่ารายละเอียดเครื่องพิมพ์หลักและสำรอง
        printer_setup1 = self.json_data.get("PrinterSetup1", [{}])[0]
        printer_setup2 = self.json_data.get("PrinterSetup2", [{}])[0]

        primary_model = printer_setup1.get("PrinterModel", "")
        secondary_model = printer_setup2.get("PrinterModel", "")

        # ตรวจสอบว่าเครื่องพิมพ์ทั้งสองเครื่องมีข้อมูลหรือไม่
        if not primary_model or not secondary_model:
            self.show_warning("กรุณากรอกข้อมูลชื่อรุ่นเครื่องพิมพ์ทั้ง 2 เครื่องก่อนครับ")
            return

        # ตรวจสอบว่าเครื่องพิมพ์หลักและสำรองเป็นรุ่น VKP80III หรือไม่
        if primary_model == "VKP80III" and secondary_model == "VKP80III":
            print("ใช้ VKP80III ทั้งคู่")
            self.primary_printer = printerStatus1(os.getcwd())
            self.secondary_printer = printerStatus1(os.getcwd())
        else:
            print("ใช้เครื่องพิมพ์หลักเป็น VKP80III และสำรองเป็น FTP-639")
            self.primary_printer = printerStatus1(os.getcwd())
            self.secondary_printer = printerStatus2(os.getcwd())

        # เริ่มต้นการตั้งค่าต่างๆ
        self.current_selected_printer = "Primary"
        self.current_printer = self.primary_printer
        self.is_using_secondary = False
        self.init_timer()
        self.update_location_label()

    def show_warning(self, message):
        """แสดงข้อความเตือนในกรณีที่มีข้อผิดพลาด"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("แจ้งเตือน")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def load_json_data(self):
        """โหลดข้อมูลจากไฟล์ config.json"""
        printer_location_logfile = os.getenv('PRINTER_LOGFILE_LOCATION')
        json_file_path = os.path.join(printer_location_logfile, 'config.JSON')
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading JSON: {e}")
            return {}

    def init_ui(self):
        """กำหนด UI และเชื่อมโยงปุ่มต่าง ๆ"""
        self.btnmenu = self.findChild(QToolButton, 'btnmenu')
        self.PaperJamStatus = self.findChild(QLabel, 'PaperJamStatus')
        self.OnlineStatus = self.findChild(QLabel, 'OnlineStatus')
        self.PrinterStatus = self.findChild(QLabel, 'PrinterStatus')
        self.PaperEndStatus = self.findChild(QLabel, 'PaperEndStatus')
        self.Location = self.findChild(QLabel, 'Location')
        self.PrinterModel = self.findChild(QLabel, 'PrinterModel')
        self.lb_information = self.findChild(QLabel, 'lb_information')
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

    def init_timer(self):
        """ตั้งค่า Timer สำหรับการอัปเดตสถานะ"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)

        self.table_timer = QTimer(self)
        self.table_timer.timeout.connect(self.update_table)
        self.table_timer.start(3000)

    def update_printer_model_label(self, setting):
        """อัปเดตรุ่นของเครื่องพิมพ์"""
        model = self.get_printer_info(setting, 'PrinterModel')
        self.PrinterModel.setText(model if model else "Printer Model: Not Found")

    def update_location_label(self):
        """อัปเดตตำแหน่งจาก JSON"""
        try:
            location = self.json_data.get('ApplicationSetup', [{}])[0].get('Location', 'ไม่พบข้อมูล')
            self.Location.setText(location)
        except Exception as e:
            print(f"Error updating location: {e}")

    def get_printer_info(self, setting, key):
        """ดึงข้อมูลของเครื่องพิมพ์จาก JSON"""
        for setup_key in ['PrinterSetup1', 'PrinterSetup2']:
            for setup in self.json_data.get(setup_key, []):
                if setup.get('Setting') == setting:
                    return setup.get(key, '')
        return None

    def update_status(self):
        """อัปเดตสถานะของเครื่องพิมพ์"""
        primary_status = self.primary_printer.get_status()
        secondary_status = self.secondary_printer.get_status()

        if primary_status["printerStatus"] == "unavailable" and secondary_status["printerStatus"] == "unavailable":
            self.lb_information.setText("⛔ เครื่องหลักเเละเครื่องสำรองมีปัญหา...")
            return

        if secondary_status["printerStatus"] == "available" and self.is_using_secondary:
            self.lb_information.setText("✅ กำลังใช้เครื่องสำรอง")

        if primary_status["printerStatus"] == "unavailable" and not self.is_using_secondary:
            self.lb_information.setText("⚠️ เครื่องหลักมีปัญหากำลังพิมพ์งานที่เครื่องสำรอง")
            self.current_printer = self.secondary_printer
            self.is_using_secondary = True
            self.load_table('Secondary')
            self.update_printer_model_label('Secondary')

        if self.is_using_secondary and primary_status["printerStatus"] == "available":
            self.lb_information.setText("✅ เครื่องหลักกลับมาใช้งานได้แล้ว กำลังสลับกลับไปที่เครื่องหลัก")
            self.current_printer = self.primary_printer
            self.is_using_secondary = False
            self.load_table('Primary')
            self.update_printer_model_label('Primary')

        status = self.current_printer.get_status()

        self.PrinterStatus.setText(f"{status['printerStatus']}\n")
        self.OnlineStatus.setText(f"{status['onlineStatus']}\n")
        self.PaperEndStatus.setText(f"{status['paperEndStatus']}\n")
        self.PaperJamStatus.setText(f"{status['paperJamStatus']}\n")

    def go_to_logfile(self, setting):
        """เปิดไฟล์ LogFile"""
        self.close()
        location_file = self.get_printer_info(setting, 'LocationFilePrinter')
        if location_file:
            current_time_folder = datetime.now().strftime("%Y%m%d")
            current_time_file = datetime.now().strftime("%Y%m%d%H")
            json_file_name = f"PrinterStatusJson{current_time_file}.JSON"
            json_file_path = os.path.join(location_file, 'Status', current_time_folder, json_file_name)

            from logfile import Ui_LogFile
            self.new_window = Ui_LogFile(json_file_path)
            self.new_window.show()

    def go_to_logfile_primary(self):
        """ไปยัง LogFile ของเครื่องพิมพ์หลัก"""
        self.go_to_logfile('Primary')

    def go_to_logfile_secondary(self):
        """ไปยัง LogFile ของเครื่องพิมพ์สำรอง"""
        self.go_to_logfile('Secondary')

    def on_monitoring_selected(self):
        """เปลี่ยนไปหน้าการตรวจสอบ"""
        self.hide()
        from monitoring import Ui_Monitoring
        self.new_window = Ui_Monitoring()
        self.new_window.show()

    def on_configuration_selected(self):
        """เปลี่ยนไปหน้าการตั้งค่าคอนฟิก"""
        self.hide()
        from configuration import Ui_Configuration
        self.new_window = Ui_Configuration()
        self.new_window.show()

    def on_application_selected(self):
        """เปลี่ยนไปหน้าการตั้งค่าแอปพลิเคชัน"""
        self.hide()
        from application import Ui_Application
        self.new_window = Ui_Application()
        self.new_window.show()

    def show_primary_table(self):
        """แสดงตารางเครื่องพิมพ์หลัก"""
        self.current_selected_printer = "Primary"
        self.load_table('Primary')
        self.stackedWidget.setCurrentIndex(0)
        self.btnLogFilePrimary.show()
        self.btnLogFileSecondary.hide()

    def show_secondary_table(self):
        """แสดงตารางเครื่องพิมพ์สำรอง"""
        self.current_selected_printer = "Secondary"
        self.load_table('Secondary')
        self.stackedWidget.setCurrentIndex(1)
        self.btnLogFilePrimary.hide()
        self.btnLogFileSecondary.show()

    def load_table(self, setting):
        """โหลดข้อมูลจากไฟล์ JSON และแสดงใน QTableWidget"""
        location_file = self.get_printer_info(setting, 'LocationFilePrinter')
        if location_file:
            current_time_folder = datetime.now().strftime("%Y%m%d")
            current_time_file = datetime.now().strftime("%Y%m%d%H")
            json_file_name = f"PrinterStatusJson{current_time_file}.JSON"
            json_file_path = os.path.join(location_file, 'Status', current_time_folder, json_file_name)

            try:
                with open(json_file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    if not isinstance(data, list):
                        return
                    
                    # เรียงลำดับข้อมูลจากล่าสุด -> เก่าสุด
                    try:
                        data.sort(key=lambda x: datetime.strptime(x.get("timestamp", "1970-01-01 00:00:00.000"), "%Y-%m-%d %H:%M:%S.%f"), reverse=True)
                    except ValueError:
                        return

                    # เลือก table ที่จะใช้ (Primary หรือ Secondary)
                    table = self.tableLogPrimary if setting == 'Primary' else self.tableLogSecondary

                    # กำหนดคอลัมน์ที่ต้องการแสดง
                    columns = ['timestamp', 'senderIp', 'printerId', 'printerStatus', 'onlineStatus', 'paperEndStatus', 'paperJamStatus']
                    table.setRowCount(len(data))
                    table.setColumnCount(len(columns))
                    table.setHorizontalHeaderLabels(columns)

                    for row, entry in enumerate(data):
                        for col, key in enumerate(columns):
                            value = entry.get(key, 'N/A')
                            table.setItem(row, col, QTableWidgetItem(str(value)))

                    table.resizeColumnsToContents()  # ปรับขนาดคอลัมน์ให้พอดี

            except FileNotFoundError:
                print(f"Error: The file at {json_file_path} was not found.")
            except json.JSONDecodeError:
                print("Error: The file could not be decoded as JSON.")
            except Exception as e:
                print(f"An error occurred: {e}")

    def update_table(self):
        """โหลดข้อมูลใหม่ทุกๆ 3 วินาที"""
        if self.current_selected_printer == "Primary":
            self.load_table('Primary')
        else:
            self.load_table('Secondary')

    def closeEvent(self, event):
        """หยุดการทำงานของ Thread ก่อนปิดโปรแกรม"""
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Ui_Monitoring()
    window.show()
    sys.exit(app.exec())
