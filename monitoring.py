import sys
import os
import json
from dotenv import load_dotenv  # นำเข้า dotenv
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, QWidget, QToolButton, QMenu, QStackedWidget, QLabel, QMessageBox
from PyQt6.QtCore import QTimer
# เพิ่ม path ของ `printerStatusFclTP.py`
printer_status_path = os.path.join(os.getcwd(), "python_printer_status")
sys.path.append(printer_status_path)
from printerStatusFclTP import printerStatus2  # นำเข้า printerStatus2
from printerStatusVKP80iii import printerStatus1  # นำเข้า printerStatus1

class Ui_Monitoring(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('Designer/monitoring.ui', self)  # โหลด UI
        self.init_ui()
        load_dotenv(override=True)
        work_dir = os.getcwd()
        self.primary_printer = printerStatus1(work_dir)
        self.secondary_printer = printerStatus2(work_dir)
        self.check_config_file()
    def check_config_file(self):
        printer_logfile_location = os.getenv("PRINTER_LOGFILE_LOCATION", "")
        config_file_path = os.path.join(printer_logfile_location, "config.json")
        print(f"ไฟล์ JSON path ที่ได้: {config_file_path}")
        if not os.path.exists(config_file_path):
            self.show_warning()
            return
        else:
            print("พบไฟล์ config.json")
            self.current_printer = self.primary_printer
            self.is_using_secondary = False
            self.init_ui()
            self.json_data = self.load_json_data()
            self.current_selected_printer = "Primary"
            self.init_timer()
            #self.update_location_label()
            #self.show_primary_table()
             
            

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

        if primary_status["printerStatus"] == "unavailable":
            if not self.is_using_secondary:
                QMessageBox.warning(self, "แจ้งเตือน", "เครื่องหลักมีปัญหากำลังพิมพ์งานที่เครื่องสำรอง")
                self.current_printer = self.secondary_printer
                self.is_using_secondary = True
                # ดึงข้อมูลจาก printer status
            status = self.current_printer.get_status()
            # แสดง Printer Status และ Online Status ที่ printer_status_label2
            printer_status_text2 = f"FTP-639PS {status['printerStatus']}\n"
            self.PrinterStatus.setText(printer_status_text2)
            online_status_text2 = f"FTP-639OS {status['onlineStatus']}\n"
            self.OnlineStatus.setText(online_status_text2)

            # แสดง Paper End Status และ Paper Jam Status ที่ paper_status_label2
            paper_end_status_text2 = f"FTP-639ES {status['paperEndStatus']}\n"
            self.PaperEndStatus.setText(paper_end_status_text2)
            paper_jam_status_text2 = f"FTP-639JS {status['paperJamStatus']}\n"
            self.PaperJamStatus.setText(paper_jam_status_text2)
        
        if primary_status["printerStatus"] == "unavailable" and secondary_status["printerStatus"] == "unavailable":
            QMessageBox.critical(self, "แจ้งเตือน", "เครื่องหลักเเละเครื่องสำรองมีปัญหา...")
            # ดึงข้อมูลจาก printer status
            status = self.current_printer.get_status()
            # แสดง Printer Status และ Online Status ที่ printer_status_label2
            printer_status_text2 = f"FTP-639PS {status['printerStatus']}\n"
            self.PrinterStatus.setText(printer_status_text2)
            online_status_text2 = f"FTP-639OS {status['onlineStatus']}\n"
            self.OnlineStatus.setText(online_status_text2)

            # แสดง Paper End Status และ Paper Jam Status ที่ paper_status_label2
            paper_end_status_text2 = f"FTP-639ES {status['paperEndStatus']}\n"
            self.PaperEndStatus.setText(paper_end_status_text2)
            paper_jam_status_text2 = f"FTP-639JS {status['paperJamStatus']}\n"
            self.PaperJamStatus.setText(paper_jam_status_text2)
        
        if self.is_using_secondary and primary_status["printerStatus"] == "available":
            QMessageBox.information(self, "แจ้งเตือน", "เครื่องหลักกลับมาใช้งานได้แล้ว กำลังสลับกลับไปที่เครื่องหลัก")
            self.current_printer = self.primary_printer
            self.is_using_secondary = False
        
           # ดึงข้อมูลจาก printer status
            status = self.current_printer.get_status()
            # แสดง Printer Status และ Online Status ที่ printer_status_label2
            printer_status_text2 = f"FTP-639PS {status['printerStatus']}\n"
            self.PrinterStatus.setText(printer_status_text2)
            online_status_text2 = f"FTP-639OS {status['onlineStatus']}\n"
            self.OnlineStatus.setText(online_status_text2)

            # แสดง Paper End Status และ Paper Jam Status ที่ paper_status_label2
            paper_end_status_text2 = f"FTP-639ES {status['paperEndStatus']}\n"
            self.PaperEndStatus.setText(paper_end_status_text2)
            paper_jam_status_text2 = f"FTP-639JS {status['paperJamStatus']}\n"
            self.PaperJamStatus.setText(paper_jam_status_text2)

    def update_all_printer_status(self):
        """ อัปเดตสถานะเฉพาะเครื่องที่ถูกเลือก """
        if self.current_selected_printer == "Primary":
            self.update_printer_and_paper_status("Primary")
        elif self.current_selected_printer == "Secondary":
            self.update_printer_and_paper_status("Secondary")


    # 📂 เปิด LogFile
    def go_to_logfile(self, setting):
        self.close()
        location_file = self.get_printer_info(setting, 'LocationFilePrinter')
        if location_file:
            log_file = os.path.join(location_file, 'LogFile', 'PrinterLogJson20241004150823.JSON')
            from logfile import Ui_LogFile
            self.new_window = Ui_LogFile()
            self.new_window.load_logfile_data(log_file)
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
        self.update_printer_and_paper_status('Primary')
        self.stackedWidget.setCurrentIndex(0)
        self.btnLogFilePrimary.show()
        self.btnLogFileSecondary.hide()

    def show_secondary_table(self):
        self.current_selected_printer = "Secondary"  # บันทึกว่าเลือก Secondary
        self.load_table('Secondary')
        self.update_printer_model_label('Secondary')
        self.update_printer_and_paper_status('Secondary')
        self.stackedWidget.setCurrentIndex(1)
        self.btnLogFilePrimary.hide()
        self.btnLogFileSecondary.show()


    # 📊 โหลดตารางจาก JSON
    def load_table(self, setting):
        location_file = self.get_printer_info(setting, 'LocationFilePrinter')
        if location_file:
            json_file_path = os.path.join(location_file, 'LogFile', 'PrinterLogJson20241004150823.JSON')
            try:
                with open(json_file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    printer_log = data.get('PrinterLog', [])
                    table = self.tableLogPrimary if setting == 'Primary' else self.tableLogSecondary
                    table.setRowCount(len(printer_log))

                    for row, entry in enumerate(printer_log):
                        for col, key in enumerate(['Time', 'DocumentID', 'DocumentStatus', 'PrinterStatus', 'PaperStatus', 'Error']):
                            table.setItem(row, col, QTableWidgetItem(entry.get(key, '')))
            except Exception as e:
                print(f"Error loading table: {e}")

    def closeEvent(self, event):
        """ หยุดการทำงานของ Thread ก่อนปิดโปรแกรม """
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Ui_Monitoring()
    window.show()
    sys.exit(app.exec())
