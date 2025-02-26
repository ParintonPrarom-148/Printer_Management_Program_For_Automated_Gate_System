import sys #เทส
import json
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, QWidget, QToolButton, QMenu, QStackedWidget, QLabel
from PyQt6 import uic

class Ui_Monitoring(QWidget):
    def __init__(self):
        super().__init__()
        # โหลด UI ที่สร้างจาก Qt Designer
        uic.loadUi('Designer/monitoring.ui', self)  # เปลี่ยนให้เป็นพาธไฟล์ .ui ของคุณ
        self.show_primary_table()

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

        self.btnLogFilePrimary = self.findChild(QPushButton, 'btnLogFilePrimary')
        self.btnLogFilePrimary.clicked.connect(self.go_to_logfile_primary)

        self.btnLogFileSecondary = self.findChild(QPushButton, 'btnLogFileSecondary')
        self.btnLogFileSecondary.clicked.connect(self.go_to_logfile_secondary)

        # กำหนดให้เมนูแสดงเมื่อคลิก
        self.btnmenu.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        # หาปุ่ม btnShowPrimaryTable และเชื่อมโยงกับฟังก์ชัน load_json_data
        self.btnShowPrimaryTable = self.findChild(QPushButton, 'btnShowPrimaryTable')
        self.btnShowPrimaryTable.clicked.connect(self.show_primary_table)

        self.btnShowSecondaryTable = self.findChild(QPushButton, 'btnShowSecondaryTable')
        self.btnShowSecondaryTable.clicked.connect(self.show_secondary_table)

        # หาปุ่ม btnLogFilePrimary และ btnLogFileSecondary
        self.btnLogFilePrimary = self.findChild(QPushButton, 'btnLogFilePrimary')
        self.btnLogFileSecondary = self.findChild(QPushButton, 'btnLogFileSecondary')

        # สร้าง QStackedWidget สำหรับการแสดงหน้าจอ
        self.stackedWidget = self.findChild(QStackedWidget, 'stackedWidget')

        # หาค่าของ QLabel ที่ชื่อว่า Location
        self.labelLocation = self.findChild(QLabel, 'Location')  # หาชื่อของ QLabel ที่จะใช้แสดง Location

        # โหลดข้อมูลจากไฟล์ JSON และอัปเดต QLabel
        self.update_location_label()

    def update_location_label(self):
        # เส้นทางของไฟล์ JSON
        json_file_path = r"printer/config.JSON"

        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

                # ดึงค่าของ 'Location' จากข้อมูล JSON
                location = data.get('ApplicationSetup', [{}])[0].get('Location', 'ไม่พบข้อมูล')
                
                # แสดงค่า Location ใน QLabel
                self.labelLocation.setText(location)  # อัปเดตข้อความใน QLabel

        except FileNotFoundError:
            print(f"Error: The file at {json_file_path} was not found.")
        except json.JSONDecodeError:
            print("Error: The file could not be decoded as JSON.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def go_to_logfile_primary(self):
        self.close()
        json_file_path = r"Printer\Primary\LogFile\PrinterLogJson20241004150823.JSON"
        from logfile import Ui_LogFile
        self.new_window = Ui_LogFile()
        self.new_window.load_logfile_data(json_file_path)
        self.new_window.show()

    def go_to_logfile_secondary(self):
        self.close()
        json_file_path = r"Printer\Secondary\LogFile\PrinterLogJson20241004150823.JSON"
        from logfile import Ui_LogFile
        self.new_window = Ui_LogFile()
        self.new_window.load_logfile_data(json_file_path)
        self.new_window.show()

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
        self.close()
        from application import Ui_Application
        self.new_window = Ui_Application()
        self.new_window.show()

    def show_primary_table(self):
        self.load_table_primary()
        self.stackedWidget.setCurrentIndex(0)
        self.btnLogFilePrimary.show()
        self.btnLogFileSecondary.hide()

    def show_secondary_table(self):
        self.load_table_secondary()
        self.stackedWidget.setCurrentIndex(1)
        self.btnLogFilePrimary.hide()
        self.btnLogFileSecondary.show()

    def load_table_primary(self):
        json_file_path = r"Printer\Primary\LogFile\PrinterLogJson20241004150823.JSON"
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if 'PrinterLog' in data:
                    printer_log_data = data['PrinterLog']
                    self.tableLogPrimary.setRowCount(len(printer_log_data))
                    for row, entry in enumerate(printer_log_data):
                        self.tableLogPrimary.setItem(row, 0, QTableWidgetItem(entry['Time']))
                        self.tableLogPrimary.setItem(row, 1, QTableWidgetItem(entry['DocumentID']))
                        self.tableLogPrimary.setItem(row, 2, QTableWidgetItem(entry['DocumentStatus']))
                        self.tableLogPrimary.setItem(row, 3, QTableWidgetItem(entry['PrinterStatus']))
                        self.tableLogPrimary.setItem(row, 4, QTableWidgetItem(entry['PaperStatus']))
                        self.tableLogPrimary.setItem(row, 5, QTableWidgetItem(entry['Error']))
                else:
                    print("Error: 'PrinterLog' not found in the JSON data.")
        except FileNotFoundError:
            print(f"Error: The file at {json_file_path} was not found.")
        except json.JSONDecodeError:
            print("Error: The file could not be decoded as JSON.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def load_table_secondary(self):
        json_file_path = r"Printer\Secondary\LogFile\PrinterLogJson20241004150823.JSON"
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if 'PrinterLog' in data:
                    printer_log_data = data['PrinterLog']
                    self.tableLogSecondary.setRowCount(len(printer_log_data))
                    for row, entry in enumerate(printer_log_data):
                        self.tableLogSecondary.setItem(row, 0, QTableWidgetItem(entry['Time']))
                        self.tableLogSecondary.setItem(row, 1, QTableWidgetItem(entry['DocumentID']))
                        self.tableLogSecondary.setItem(row, 2, QTableWidgetItem(entry['DocumentStatus']))
                        self.tableLogSecondary.setItem(row, 3, QTableWidgetItem(entry['PrinterStatus']))
                        self.tableLogSecondary.setItem(row, 4, QTableWidgetItem(entry['PaperStatus']))
                        self.tableLogSecondary.setItem(row, 5, QTableWidgetItem(entry['Error']))
                else:
                    print("Error: 'PrinterLog' not found in the JSON data.")
        except FileNotFoundError:
            print(f"Error: The file at {json_file_path} was not found.")
        except json.JSONDecodeError:
            print("Error: The file could not be decoded as JSON.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Ui_Monitoring()
    window.show()
    sys.exit(app.exec())
