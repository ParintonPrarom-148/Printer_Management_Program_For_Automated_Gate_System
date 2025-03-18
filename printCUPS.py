import sys
import subprocess
import json
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel
from datetime import datetime
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

class PrintPDFApp(QWidget):
    def __init__(self):
        super().__init__()
        
        load_dotenv(override=True)  # โหลดไฟล์ .env
        
        self.setWindowTitle("Print PDF via CUPS")
        self.setGeometry(100, 100, 400, 200)

        self.layout = QVBoxLayout()

        self.label = QLabel("Select a PDF file to print")
        self.layout.addWidget(self.label)

        self.select_button = QPushButton("Browse")
        self.select_button.clicked.connect(self.select_file)
        self.layout.addWidget(self.select_button)

        self.print_button = QPushButton("Print")
        self.print_button.clicked.connect(self.print_file)
        self.layout.addWidget(self.print_button)

        self.status_button = QPushButton("Check Printer Status")
        self.status_button.clicked.connect(self.check_printer_status)
        self.layout.addWidget(self.status_button)

        self.setLayout(self.layout)
        self.selected_file = ""

        # Initialize the printer status variables
        self.current_printerStatus = ""
        self.current_onlineStatus = ""
        self.current_paperEndStatus = ""
        self.current_paperJamStatus = ""

        self.init_timer()

    def init_timer(self):
        """ตั้งค่า Timer สำหรับการอัปเดตสถานะ"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)

    def update_status(self):
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
        self.current_printer = self.primary_printer

    def select_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select PDF File", "", "PDF Files (*.pdf)")
        if file_path:
            self.selected_file = file_path
            self.label.setText(f"Selected: {file_path}")

    def check_printer_status(self):
        # เช็คสถานะเครื่องพิมพ์หลัก (VKP80III) และเครื่องพิมพ์สำรอง (FTP-639)
        primary_status = self.primary_printer.get_status()
        secondary_status = self.secondary_printer.get_status()

        status_message = ""

        if primary_status["printerStatus"] == "available":
            status_message += f"Primary Printer (VKP80III) is Available\n"
        else:
            status_message += f"Primary Printer (VKP80III) is Unavailable\n"

        if secondary_status["printerStatus"] == "available":
            status_message += f"Secondary Printer (FTP-639) is Available\n"
        else:
            status_message += f"Secondary Printer (FTP-639) is Unavailable\n"

        self.label.setText(status_message)

    def print_file(self):
        if not self.selected_file:
            self.label.setText("Please select a file first!")
            return

        # ตรวจสอบสถานะของเครื่องพิมพ์ก่อนพิมพ์
        primary_status = self.primary_printer.get_status()
        secondary_status = self.secondary_printer.get_status()

        printer_name = self.primary_model  # เครื่องหลัก
        wsl_path = "/mnt/" + self.selected_file.replace(":", "").replace("\\", "/").lower()

        # ตรวจสอบสถานะเครื่องพิมพ์หลักก่อน
        if primary_status["printerStatus"] == "unavailable":
            # ถ้าเครื่องหลัก (VKP80III) ออฟไลน์ ให้พิมพ์ไปยังเครื่องสำรอง (FTP-639)
            if secondary_status["printerStatus"] == "available":
                printer_name = self.secondary_model
                self.current_printerStatus = secondary_status.get("printerStatus")
                self.current_onlineStatus = secondary_status.get("onlineStatus")
                self.current_paperEndStatus = secondary_status.get("paperEndStatus")
                self.current_paperJamStatus = secondary_status.get("paperJamStatus")
            else:
                self.label.setText("Both printers are unavailable! ❌")
                printer_name = "Both printers are unavailable!"
                status = "Failed"  # เพิ่มสถานะเป็น Failed เมื่อเครื่องพิมพ์ทั้งสองมีปัญหา
                self.current_printerStatus = "unavailable"
                self.current_onlineStatus = "offline"
                self.current_paperEndStatus = "None"
                self.current_paperJamStatus = "None"
                self.save_print_job(printer_name, status)
                return
        else:
            # ถ้าเครื่องหลัก (VKP80III) ใช้งานได้ ให้พิมพ์ไปที่เครื่องหลัก
            printer_name = self.primary_model
            self.current_printerStatus = primary_status.get("printerStatus")
            self.current_onlineStatus = primary_status.get("onlineStatus")
            self.current_paperEndStatus = primary_status.get("paperEndStatus")
            self.current_paperJamStatus = primary_status.get("paperJamStatus")

        try:
            # พิมพ์ไฟล์ผ่าน CUPS
            subprocess.run(["wsl", "lp", "-d", printer_name, wsl_path], check=True)

            # เก็บสถานะการพิมพ์เป็น Successful
            status = "Successful"
            self.label.setText(f"Printing to {printer_name}... ✅")
            self.save_print_job(printer_name, status)

        except subprocess.CalledProcessError as e:
            # ถ้ามีข้อผิดพลาด เก็บสถานะการพิมพ์เป็น Failed
            status = "Failed"
            self.label.setText(f"Print Failed ❌: {e}")
            self.save_print_job(printer_name, status)

    def save_print_job(self, printer_name, status):
        # เก็บเวลาเมื่อพิมพ์
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
       
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            timestamp_folder = datetime.now().strftime("%Y%m%d")
            timestamp_file = datetime.now().strftime("%Y%m%d%H")
            # ตัดเอาแค่ชื่อไฟล์
            filename = os.path.basename(self.selected_file)
            if self.current_onlineStatus == "offline": 
                error = "Printer are offline"
            elif self.current_paperEndStatus == "paper end":
                error = "Printer NO PAPER"
            elif self.current_paperJamStatus == "paper jam":
                error = "Printer Paperjam"
            else:
                error = "-"
            # ข้อมูลที่ต้องการบันทึก
            log_entry = {
                "Timestamp": timestamp,
                "Location": location, 
                "PrinterModel": printer_name,
                "Document": filename,
                "DocumentStatus": status,
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
            if status == "Failed":
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PrintPDFApp()
    window.show()
    sys.exit(app.exec())

