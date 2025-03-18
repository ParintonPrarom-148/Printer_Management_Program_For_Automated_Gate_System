import sys
import os
import json
import shutil
import threading
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
import uvicorn
import subprocess
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QMenu, QToolButton, QMessageBox, QPushButton, QStackedWidget,QTableWidgetItem
from PyQt6.QtCore import QTimer
from datetime import datetime
from urllib.parse import urlparse
import logging
import requests

# กำหนดเส้นทางไฟล์ .ui และไฟล์ Python
ui_file = os.path.join(os.path.dirname(__file__), 'Designer', 'monitoring.ui')
printer_status_path = os.path.join(os.path.dirname(__file__), "python_printer_status")
logger = logging.getLogger(__name__)
if getattr(sys, 'frozen', False):
    sys.path.append(printer_status_path)
else:
    sys.path.append(os.path.join(os.getcwd(), "python_printer_status"))

from printerStatusFclTP import printerStatus2  
from printerStatusVKP80iii import printerStatus1  

# FastAPI setup
app = FastAPI()

PDF_SAVE_PATH = "received_pdfs/"


class Ui_Monitoring(QWidget):
    def __init__(self):
        super().__init__()# โหลด UI
        self.config_loaded = False  # กำหนดค่าเริ่มต้นก่อน
        self.save_path = PDF_SAVE_PATH
        os.makedirs(self.save_path, exist_ok=True)
        uic.loadUi(ui_file, self)
        load_dotenv(override=True)  # โหลดไฟล์ .env
        self.init_ui()  # เริ่มต้น UI
        self.config_loaded = self.check_config_file()  # อัปเดตค่าใหม่
    def check_config_file(self):
        """ตรวจสอบและโหลดข้อมูลจากไฟล์ config.json"""
        printer_logfile_location = os.getenv("PRINTER_LOGFILE_LOCATION", "")
        config_file_path = os.path.join(printer_logfile_location, "config.json")
        print(f"ไฟล์ JSON path ที่ได้: {config_file_path}")

        if not os.path.exists(config_file_path):
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาตั้งค่าของโปรแกรมในหน้า Application Setup ก่อนครับ")
            return False

        try:
            with open(config_file_path, "r", encoding="utf-8") as file:
                self.json_data = json.load(file)
        except json.JSONDecodeError:
            QMessageBox.warning(self, "ข้อผิดพลาด", "ไฟล์ config.json ไม่ถูกต้อง")
            return False

        printer_setup1 = self.json_data.get("PrinterSetup1", [{}])[0]
        printer_setup2 = self.json_data.get("PrinterSetup2", [{}])[0]
        self.primary_model = printer_setup1.get("PrinterModel", "")
        self.secondary_model = printer_setup2.get("PrinterModel", "")

        if not self.primary_model or not self.secondary_model:
            QMessageBox.warning(self, "ข้อผิดพลาด", "กรุณาตั้งค่าชื่อรุ่นของเครื่องพิมพ์ทั้ง 2 เครื่องในหน้า Configuration Setup ก่อนครับ")
            return False

        if self.primary_model == "VKP80III" and self.secondary_model == "VKP80III":
            self.primary_printer = printerStatus1(os.getcwd())
            self.secondary_printer = printerStatus1(os.getcwd())
        elif self.primary_model == "VKP80III" and self.secondary_model == "FTP-639":
            self.primary_printer = printerStatus1(os.getcwd())
            self.secondary_printer = printerStatus2(os.getcwd())
        else:
            self.primary_printer = printerStatus2(os.getcwd())
            self.secondary_printer = printerStatus1(os.getcwd())

        self.current_selected_printer = "Primary"
        self.current_printer = self.primary_printer
        self.is_using_secondary = False
        self.init_timer()
        self.update_location_label()
        self.show_primary_table()
        return True


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
        self.table_timer.start(1000)

    def update_printer_model_label(self, setting):
        """อัปเดตรุ่นของเครื่องพิมพ์"""
        model = self.get_printer_info(setting, 'PrinterModel')
        self.PrinterModel.setText(model if model else "Printer Model: Not Found")

    def update_location_label(self):
        """อัปเดตตำแหน่งจาก JSON"""
        try:
            self.location = self.json_data.get('ApplicationSetup', [{}])[0].get('Location', 'ไม่พบข้อมูล')
            self.Location.setText(self.location)
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
        self.primary_status = self.primary_printer.get_status()
        self.secondary_status = self.secondary_printer.get_status()

        if self.primary_status["printerStatus"] == "unavailable" and self.secondary_status["printerStatus"] == "unavailable":
            self.lb_information.setText("⛔ Both primary and secondary printers are unavailable...")
            return
        if self.primary_status["printerStatus"] == "available" and not self.is_using_secondary:
            self.lb_information.setText("✅ Using the primary printer")
            self.is_using_secondary = False

        if self.secondary_status["printerStatus"] == "available" and self.is_using_secondary:
            self.lb_information.setText("✅ Using the secondary printer")

        if self.primary_status["printerStatus"] == "unavailable" and not self.is_using_secondary:
            self.lb_information.setText("⚠️ Primary printer is unavailable, switching to the secondary printer")
            self.current_printer = self.secondary_printer
            self.is_using_secondary = True

        if self.primary_status["printerStatus"] == "available" and self.is_using_secondary:
            self.lb_information.setText("✅ Primary printer is back online, switching back to the primary printer")
            self.current_printer = self.primary_printer
            self.is_using_secondary = False

        
        
    def show_status(self,setting):
        if setting == "Primary":
            status = self.primary_printer.get_status()
        else:
            status = self.secondary_printer.get_status()
        self.PrinterStatus.setText(f"{status['printerStatus']}\n")
        self.OnlineStatus.setText(f"{status['onlineStatus']}\n")
        self.PaperEndStatus.setText(f"{status['paperEndStatus']}\n")
        self.PaperJamStatus.setText(f"{status['paperJamStatus']}\n")
         


    def go_to_logfile(self, setting):
        """เปิดไฟล์ LogFile"""
        location_file = self.get_printer_info(setting, 'LocationFilePrinter')
        if location_file:
            current_time_folder = datetime.now().strftime("%Y%m%d")
            current_time_file = datetime.now().strftime("%Y%m%d%H")
            json_file_name = f"PrinterLogfileJson{current_time_file}.JSON"
            json_file_path = os.path.join(location_file, 'Logfile', current_time_folder, json_file_name)

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
        self.show()
        
    def on_configuration_selected(self):
        """เปลี่ยนไปหน้าการตั้งค่าคอนฟิก"""
        from configuration import Ui_Configuration
        self.new_window = Ui_Configuration()
        self.new_window.show()

    def on_application_selected(self):
        """เปลี่ยนไปหน้าการตั้งค่าแอปพลิเคชัน"""
        from application import Ui_Application
        self.new_window = Ui_Application()
        self.new_window.show()

    def show_primary_table(self):
        """แสดงตารางเครื่องพิมพ์หลัก"""
        self.current_selected_printer = "Primary"
        self.load_table('Primary')
        self.show_status('Primary')
        self.update_printer_model_label('Primary')
        self.stackedWidget.setCurrentIndex(0)
        self.btnLogFilePrimary.show()
        self.btnLogFileSecondary.hide()

    def show_secondary_table(self):
        """แสดงตารางเครื่องพิมพ์สำรอง"""
        self.current_selected_printer = "Secondary"
        self.load_table('Secondary')
        self.show_status('Secondary')
        self.update_printer_model_label('Secondary')
        self.stackedWidget.setCurrentIndex(1)
        self.btnLogFilePrimary.hide()
        self.btnLogFileSecondary.show()

    def load_table(self, setting):
        """โหลดข้อมูลจากไฟล์ JSON และแสดงใน QTableWidget"""
        location_file = self.get_printer_info(setting, 'LocationFilePrinter')
        if location_file:
            current_time_folder = datetime.now().strftime("%Y%m%d")
            current_time_file = datetime.now().strftime("%Y%m%d%H")
            json_file_name = f"PrinterLogfileJson{current_time_file}.JSON"
            json_file_path = os.path.join(location_file, 'Logfile', current_time_folder, json_file_name)

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
                    columns = ['Timestamp', 'Document', 'DocumentStatus', 'PrinterStatus', 'OnlineStatus','PaperEndStatus','PaperJamStatus','Error']
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
    
    def get_sumatra_path(self):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS  # หา path ใน PyInstaller EXE
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))  # หา path ใน Python ปกติ
        
        return os.path.join(base_path, "sumatra", "SumatraPDF.exe")

    def print_pdf(self, pdf_path):
        try:
            sumatra_path = self.get_sumatra_path()
            printer_name = self.get_available_printer()
            if printer_name == "No available printer found":
                raise Exception("No available printer found.")

            command = f'"{sumatra_path}" -print-to "{printer_name}" "{pdf_path}"'
            subprocess.run(command, shell=True, check=True)
            print_status = "Successful"
        except Exception as e:
            print_status = "Failed"

        # บันทึก JSON Log หลังจากพิมพ์เสร็จ
        self.savejsonlogfile(pdf_path, print_status, printer_name)

        # 🔥 ลบไฟล์ PDF หลังพิมพ์เสร็จ
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                print(f"Deleted file: {pdf_path}")  # Debug log
            else:
                print(f"File not found: {pdf_path}")  # Debug log
        except Exception as e:
            print(f"Error deleting file {pdf_path}: {e}")

        return print_status


    def get_available_printer(self):
        """ตรวจสอบสถานะเครื่องพิมพ์และเลือกเครื่องที่สามารถใช้งานได้"""

        if self.primary_status.get("printerStatus") == "available":
            self.current_printerStatus =self.primary_status.get("printerStatus")
            self.current_onlineStatus =self.primary_status.get("onlineStatus")
            self.current_paperEndStatus =self.primary_status.get("paperEndStatus")
            self.current_paperJamStatus =self.primary_status.get("paperJamStatus")
            return self.primary_model
        elif self.secondary_status.get("printerStatus") == "available":
            self.current_printerStatus =self.secondary_status.get("printerStatus")
            self.current_onlineStatus =self.secondary_status.get("onlineStatus")
            self.current_paperEndStatus =self.secondary_status.get("paperEndStatus")
            self.current_paperJamStatus ="paper jam"
            return self.secondary_model
        self.current_printerStatus = "unavailable"
        self.current_onlineStatus = "offline"
        self.current_paperEndStatus = "None"
        self.current_paperJamStatus = "None"
        return "Both printers are unavailable!"

    async def upload_pdf(self, file: UploadFile = File(...)):
        file_path = os.path.join(self.save_path, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print_result = self.print_pdf(file_path)
        return {"filename": file.filename, "status": print_result}

    def savejsonlogfile(self, document_name, print_status, printer_name):
        try:
            config_path = os.path.abspath(os.getenv('KIOSK_LOGFILE_LOCATION'))
            print(f"Config Path: {config_path}")

            if not os.path.exists(config_path):
                print("Config file does not exist.")
                return

            target_model = printer_name
            print(f"Target Printer Model: {target_model}")

            with open(config_path, "r", encoding="utf-8") as config_file:
                config_data = json.load(config_file)

            # ดึงค่า Location จาก ApplicationSetup
            location = "Unknown"
            if "ApplicationSetup" in config_data and isinstance(config_data["ApplicationSetup"], list):
                if config_data["ApplicationSetup"]:
                    location = config_data["ApplicationSetup"][0].get("Location", "Unknown")

            # หา path สำหรับบันทึก log
            printer_locations = []
            found_printer = False

            for key in config_data:
                if key.startswith("PrinterSetup"):
                    for printer in config_data[key]:
                        if printer.get("PrinterModel") == target_model:
                            printer_locations = [printer.get("LocationFilePrinter")]
                            found_printer = True
                            break  # ออกจาก loop เพราะเจอ printer ที่ตรงกันแล้ว

            # ถ้าไม่พบ target_model ให้ใช้ LocationFilePrinter ของทั้ง Primary และ Secondary
            if not found_printer:
                for key in ["PrinterSetup1", "PrinterSetup2"]:
                    if key in config_data:
                        for printer in config_data[key]:
                            if "LocationFilePrinter" in printer:
                                printer_locations.append(printer["LocationFilePrinter"])

            print(f"Resolved Printer Locations: {printer_locations}")
            print(f"Location from config: {location}")

            # บันทึก log ในทุก path ที่หาได้
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            timestamp_folder = datetime.now().strftime("%Y%m%d")
            timestamp_file = datetime.now().strftime("%Y%m%d%H")
            if self.current_onlineStatus == "offline": 
                error = "Printer is offline"
            elif self.current_paperEndStatus == "paper end":
                error = "Printer is out of paper"
            elif self.current_paperJamStatus == "paper jam":
                error = "Printer has a paper jam"
            else:
                error = "-"

            log_entry = {
                "Timestamp": timestamp,
                "Location": location, 
                "PrinterModel": target_model,
                "Document": os.path.basename(document_name),
                "DocumentStatus": print_status,
                "PrinterStatus": self.current_printerStatus,
                "OnlineStatus": self.current_onlineStatus,
                "PaperEndStatus": self.current_paperEndStatus,
                "PaperJamStatus": self.current_paperJamStatus,
                "Error": error
            }

            for printer_location in printer_locations:
                folder_path = os.path.join(printer_location, "Logfile", timestamp_folder)
                file_path = os.path.join(folder_path, f"PrinterLogfileJson{timestamp_file}.json")

                os.makedirs(folder_path, exist_ok=True)
                print(f"Folder Path Created: {folder_path}")
                print(f"Log File Path: {file_path}")

                # เขียนข้อมูลลงไฟล์ JSON
                if os.path.exists(file_path):
                    with open(file_path, "r+", encoding="utf-8") as json_file:
                        try:
                            existing_data = json.load(json_file)
                        except json.JSONDecodeError as e:
                            print(f"Error decoding JSON file: {e}")
                            existing_data = []

                        existing_data.append(log_entry)
                        json_file.seek(0)
                        json.dump(existing_data, json_file, indent=4, ensure_ascii=False)
                else:
                    with open(file_path, "w", encoding="utf-8") as json_file:
                        json.dump([log_entry], json_file, indent=4, ensure_ascii=False)

                print(f"Log saved successfully at {file_path}")
            if print_status == "Failed":
                # เมื่อบันทึก log เสร็จแล้ว ให้ทำการ POST ไปยังเซิร์ฟเวอร์
                self.post(log_entry)

        except Exception as e:
            print(f"Error: {e}")

    def post(self, log_entry):
        try:
            server_url = os.getenv("SERVER_URL")  # ใช้ค่า default ถ้าไม่มีใน env
            full_url = f"{server_url}/Logfile"  # เพิ่ม 'Logfile' ต่อท้าย

            logger.debug(f"Posting log to server: {log_entry}")

            response = requests.post(
                full_url,
                json=log_entry,  # ใช้ log_entry ที่ได้จากการบันทึกไฟล์
                auth=(os.getenv("USERNAME"), os.getenv("PASSWORD"))
            )

            response.raise_for_status()  # ตรวจสอบ response ว่ามี error หรือไม่
            logger.debug(response.json())

        except requests.exceptions.RequestException as e:
            logger.exception(f"Posting to status server failed: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")


# FastAPI Endpoint
app_qt = QApplication([])

pdf_printer = Ui_Monitoring()
@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    
    return await pdf_printer.upload_pdf(file)

def run_fastapi():
    """ฟังก์ชันที่รัน FastAPI เฉพาะเมื่อ config ถูกต้อง"""
    kiosk_url = os.getenv("KIOSK_URL", "http://0.0.0.0:8000")
    parsed_url = urlparse(kiosk_url)
    host = parsed_url.hostname or "0.0.0.0"
    port = parsed_url.port or 8000
    uvicorn.run(app, host=host, port=port)

def main():
    """เริ่มต้น PyQt6 UI"""
    app = QApplication(sys.argv)
    window = Ui_Monitoring()
    if window.config_loaded:
        fastapi_thread = threading. Thread(target=run_fastapi, daemon=True)
        fastapi_thread.start()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
