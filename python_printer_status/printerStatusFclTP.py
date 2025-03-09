import ctypes
import os
import socket
from datetime import datetime
import logging
from threading import Thread
import time
import schedule
import requests
import json
import asyncio
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class VENDOR_COMMAND(ctypes.Structure):
    _fields_ = [("unitLength", ctypes.c_ushort),
                ("bRequest", ctypes.c_ubyte),
                ("wValueH", ctypes.c_ubyte),
                ("wValueL", ctypes.c_ubyte),
                ("wIndexH", ctypes.c_ubyte),
                ("wIndexL", ctypes.c_ubyte),
                ("wLengthH", ctypes.c_ubyte),
                ("wLengthL", ctypes.c_ubyte)]

class RECEIVE_DATA(ctypes.Structure):
    _fields_ = [("unitLength", ctypes.c_ushort),
                ("DataValid", ctypes.c_bool),
                ("DataLength", ctypes.c_ulong),
                ("Data", ctypes.c_ubyte * 256)]

class printerStatus2:
    def __init__(self, work_dir):
        self.running = True  # ใช้ควบคุม Thread
        hostname = socket.gethostname()
        self.IPAddr = socket.gethostbyname(hostname)
        self.current_status = {
            "location": os.getenv("LOCATION"),
            "printerId": os.getenv("LANE_print2"),
            "printerStatus": "unavailable",
            "senderIp": self.IPAddr,
            "onlineStatus": "offline",
            "paperEndStatus": "None",
            "paperJamStatus": "None",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        }
        self.previuos_status = {}
        self.dll_path = os.path.join(work_dir, "python_printer_status", "FTPCtrl_x64.dll")


        # ตรวจสอบค่าตัวแปรสภาพแวดล้อมที่จำเป็น
        self.check_environment_variables()

        schedule.every(int(os.getenv("POST_PRINTER_STATUS_SECOND_INTERVAL"))).seconds.do(self.post)
        # สร้าง Thread และตั้งค่า daemon=True เพื่อให้ปิดเมื่อโปรแกรมหลักปิด
        self.thread = Thread(target=self.check_status, daemon=True)
        self.thread.start()

    def check_environment_variables(self):
        required_vars = ["LANE_print2", "POST_PRINTER_STATUS_SECOND_INTERVAL", "SERVER_URL", "USERNAME", "PASSWORD"]
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                logger.error(f"Environment variable {var} is not set.")
                raise ValueError(f"{var} environment variable is not set.")

    def check_status(self):
        while self.running:  # ใช้ self.running แทน while True
            schedule.run_pending()
            try:
                self.current_status["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

                try:
                    hDll = ctypes.WinDLL(self.dll_path)  
                except OSError as e:
                    logger.exception(f"Failed to load DLL: {e}")
                    self.current_status["printerStatus"] = "unavailable"
                    self.current_status["onlineStatus"] = "offline"
                    self.savejsonstatus()
                    remove_timestamp = {i:self.current_status[i] for i in self.current_status if i!='timestamp'}
                    if self.previuos_status != remove_timestamp:
                        self.previuos_status = remove_timestamp
                        self.post()
                    time.sleep(1)
                    continue

                if hDll:
                    self.check_printer_status(hDll)
                else:
                    logger.error("DLL is not loaded successfully.")
                    self.current_status["printerStatus"] = "unavailable"
                    self.current_status["onlineStatus"] = "offline"
                    self.savejsonstatus()
                    remove_timestamp = {i:self.current_status[i] for i in self.current_status if i!='timestamp'}
                    if self.previuos_status != remove_timestamp:
                        self.previuos_status = remove_timestamp
                        self.post()
                time.sleep(1)
                time.sleep(1)
            except Exception as e:
                logger.exception(f"Error in check_status: {e}")
                time.sleep(1)

    def check_printer_status(self, hDll):
        try:
            FclTP_Search_USB = hDll.FclTP_Search_USB
            FclTP_GetVendorCommand = hDll.FclTP_GetVendorCommand

            if FclTP_Search_USB() == 1:  # USB port driver detection
                VendorCmd = VENDOR_COMMAND()
                VendorCmd.bRequest = 1
                VendorCmd.wValueH = 0
                VendorCmd.wValueL = 0
                VendorCmd.wIndexH = 0
                VendorCmd.wIndexL = 0
                VendorCmd.wLengthH = 0
                VendorCmd.wLengthL = 4  # Receiving data is 4 bytes
                VendorCmd.unitLength = ctypes.sizeof(VendorCmd)

                RcvData = RECEIVE_DATA()
                RcvData.unitLength = ctypes.sizeof(RcvData)

                if FclTP_GetVendorCommand(ctypes.byref(VendorCmd), ctypes.byref(RcvData)) == 1:  # Execute vendor request
                    self.process_printer_data(RcvData)
                else:
                    self.set_unavailable_printer_status()
            else:
                self.set_unavailable_printer_status()

        except Exception as e:
            logger.exception(f"Error in check_printer_status: {e}")
            self.set_unavailable_printer_status()

    def process_printer_data(self, RcvData):
        self.current_status["printerStatus"] = "available"
        self.current_status["onlineStatus"] = "online"

        print(f"✅ Printer Status: 0x{RcvData.Data[0]:02X} 0x{RcvData.Data[1]:02X} 0x{RcvData.Data[2]:02X} 0x{RcvData.Data[3]:02X}")

        if RcvData.Data[1] == 0x28:  # paper jam
            self.current_status["printerStatus"] = "unavailable"
            self.current_status["paperEndStatus"] = "normal"
            self.current_status["paperJamStatus"] = "paper jam"
        elif RcvData.Data[2] == 0x01:  # paper near end
            self.current_status["paperEndStatus"] = "paper near-end"
            self.current_status["paperJamStatus"] = "normal"
        elif RcvData.Data[2] == 0x04 or RcvData.Data[2] == 0x05:  # paper out
            self.current_status["printerStatus"] = "unavailable"
            self.current_status["paperEndStatus"] = "paper out"
            self.current_status["paperJamStatus"] = "normal"
        elif RcvData.Data[1] == 0x04:  # platen open
            self.current_status["printerStatus"] = "unavailable"
            self.current_status["paperEndStatus"] = "None"
            self.current_status["paperJamStatus"] = "None"
        else:
            self.current_status["paperEndStatus"] = "normal"
            self.current_status["paperJamStatus"] = "normal"

        self.savejsonstatus()

    def set_unavailable_printer_status(self):
        self.current_status["onlineStatus"] = "offline"
        self.current_status["printerStatus"] = "unavailable"
        self.current_status["paperEndStatus"] = "None"
        self.current_status["paperJamStatus"] = "None"
        self.savejsonstatus()

    def post(self):
        try:
            logger.debug(f"Posting to status server: {self.current_status}")
            response = requests.post(
                os.getenv("SERVER_URL"),
                json=self.current_status,
                auth=(os.getenv("USERNAME"), os.getenv("PASSWORD"))
            )
            response.raise_for_status()  # ตรวจสอบสถานะการตอบกลับ
            logger.debug(response.json())
        except requests.exceptions.RequestException as e:
            logger.exception(f"Posting to status server failed: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")

    def get_status(self):
        return self.current_status

    def savejsonstatus(self):
        # โหลดค่าที่อยู่ของ Printer โดยตรงในฟังก์ชันนี้
        config_path = os.path.abspath(os.getenv('KIOSK_LOGFILE_LOCATION'))  # ถ้าไม่พบค่าใช้ค่า default
        target_model = "FTP-639"

        with open(config_path, "r", encoding="utf-8") as config_file:
            config_data = json.load(config_file)

        # ค้นหา PrinterSetup ที่มี PrinterModel ตรงกับ target_model
        printer_location = "Printer/DefaultPrinter"
        for key in config_data:
            if key.startswith("PrinterSetup"):
                for printer in config_data[key]:
                    if printer.get("PrinterModel") == target_model:
                        printer_location = printer.get("LocationFilePrinter", printer_location)

        # แปลงข้อมูล JSON เป็น String
        json_data = json.dumps(self.current_status, indent=4, ensure_ascii=False)

        # สร้าง timestamp สำหรับชื่อโฟลเดอร์ (แค่วันที่เท่านั้น)
        timestampfolder = datetime.now().strftime("%Y%m%d")  # ใช้แค่ปี-เดือน-วัน
        # สร้าง timestamp สำหรับชื่อไฟล์ (แค่ปี-เดือน-วัน-ชั่วโมง)
        timestampfile = datetime.now().strftime("%Y%m%d%H")  # ใช้แค่ปี-เดือน-วัน-ชั่วโมง

        # สร้าง path ให้ถูกต้อง
        folder_path = os.path.join(printer_location, "Status", timestampfolder)  # ใช้ path ตามที่ต้องการ
        file_path = os.path.join(folder_path, f"PrinterStatusJson{timestampfile}.json")


        # ตรวจสอบว่าโฟลเดอร์ "Status" และ "timestampfolder" มีอยู่หรือไม่ ถ้าไม่ให้สร้าง
        try:
            os.makedirs(folder_path, exist_ok=True)  # สร้างโฟลเดอร์หากไม่มี
            print("Folder created successfully.")
        except Exception as e:
            print(f"Error creating folder: {e}")
            return  # หยุดทำงานถ้าสร้างโฟลเดอร์ไม่ได้

        # บันทึกข้อมูลลงในไฟล์
        try:
            # เช็กว่ามีไฟล์ที่ตรงกับ timestamp ของชั่วโมงนั้นๆ อยู่หรือไม่
            if os.path.exists(file_path):
                # ถ้ามีไฟล์แล้ว ให้เปิดไฟล์และเพิ่มข้อมูลเข้าไป
                with open(file_path, "r+", encoding="utf-8") as json_file:
                    existing_data = json.load(json_file)
                    # เพิ่มข้อมูลใหม่เข้าไปในไฟล์
                    existing_data.append(self.current_status)
                    # กลับไปเขียนไฟล์ด้วยข้อมูลใหม่
                    json_file.seek(0)
                    json.dump(existing_data, json_file, indent=4, ensure_ascii=False)
                print("Data added to existing file.")
            else:
                # ถ้าไม่มีไฟล์ ให้สร้างไฟล์ใหม่
                with open(file_path, "w", encoding="utf-8") as json_file:
                    # บันทึกข้อมูลใหม่ในไฟล์
                    json.dump([self.current_status], json_file, indent=4, ensure_ascii=False)
                print("New file created and data saved.")
        except Exception as e:
            print(f"Error saving file: {e}")
    def stop(self):
        self.running = False
