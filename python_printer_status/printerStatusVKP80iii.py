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
from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger(__name__)

class PrinterStruct(ctypes.Structure):
    _fields_ = [
        ("cPrinterName", ctypes.c_wchar * 1024), 
        ("bPrinterOnline", ctypes.c_bool),  
        ("bDefaultPrinter", ctypes.c_bool),  
        ("reserved", ctypes.c_ubyte * 10240) 
    ]

class PrinterStatusStruct(ctypes.Structure):
    _fields_ = [
        ("stsNOPAPER", ctypes.c_bool),
        ("stsNEARENDPAP", ctypes.c_bool),
        ("stsTICKETOUT", ctypes.c_bool),
        ("stsNOHEAD", ctypes.c_bool),
        ("stsNOCOVER", ctypes.c_bool),
        ("stsSPOOLING", ctypes.c_bool),
        ("stsPAPERROLLING", ctypes.c_bool),
        ("stsLFPRESSED", ctypes.c_bool),
        ("stsFFPRESSED", ctypes.c_bool),
        ("stsOVERTEMP", ctypes.c_bool),
        ("stsHLVOLT", ctypes.c_bool),
        ("stsPAPERJAM", ctypes.c_bool),
        ("stsCUTERROR", ctypes.c_bool),
        ("stsRAMERROR", ctypes.c_bool),
        ("stsEEPROMERROR", ctypes.c_bool),
        ("reserved", ctypes.c_byte * 10240)  
    ]

class printerStatus1:
    
    def __init__(self, work_dir):
        self.running = True  # ใช้ควบคุม Thread
        hostname=socket.gethostname()
        self.IPAddr=socket.gethostbyname(hostname)

        self.current_status = {
                "printerId": os.getenv("LANE_print1"),
                "printerStatus": "unavailable",
                "senderIp": self.IPAddr,
                "onlineStatus": "offline",
                "paperEndStatus": "None",
                "paperJamStatus": "None",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            }
        
        self.previuos_status = {}
        # ปรับเส้นทางของ dll_path ให้ถูกต้อง
        self.dll_path = os.path.join(work_dir, "python_printer_status", "CuCustomWndAPI.dll")


        schedule.every(int(os.getenv("POST_PRINTER_STATUS_SECOND_INTERVAL"))).seconds.do(self.post)
        # สร้าง Thread และตั้งค่า daemon=True เพื่อให้ปิดเมื่อโปรแกรมหลักปิด
        self.thread = Thread(target=self.check_status, daemon=True)
        self.thread.start()

    def enumusbdevice(self):

        hDll = ctypes.WinDLL(self.dll_path)
        hDll.EnumUSBDevices.argtypes = [ctypes.POINTER(PrinterStruct), ctypes.POINTER(ctypes.c_uint32)]
        hDll.EnumUSBDevices.restype = ctypes.c_int
        num_devices = ctypes.c_uint32(0)
        result = hDll.EnumUSBDevices(None, ctypes.byref(num_devices))
        if result != 0 or num_devices.value == 0:
            return False

        devices_array = (PrinterStruct * num_devices.value)()
        result = hDll.EnumUSBDevices(devices_array, ctypes.byref(num_devices))
        if result != 0:
            return False
        
        return devices_array
    def openprinterUSBEx(self):
        hDll = ctypes.WinDLL(self.dll_path)
        hDll.OpenPrinterUSBEx.argtypes = [ctypes.POINTER(PrinterStruct), ctypes.POINTER(ctypes.c_long)]
        hDll.OpenPrinterUSBEx.restype = ctypes.c_long
        index_device = 0
        device_id = ctypes.c_long()  
        devices_array=self.enumusbdevice()
        if devices_array == False :
            return False
        
        result = hDll.OpenPrinterUSBEx(ctypes.byref(devices_array[index_device]), ctypes.byref(device_id))
        if result != 0:
            return False
        
        return device_id
    
    def check_status(self):
        openusbstatus =True
        device_id = None
        get_onlineStatus="offline"
        get_printer_status="unavailable"
        get_paperEndStatus="None"
        get_paperJamStatus="None"
       
        while True and self.running:
            schedule.run_pending()
            try:
                normal_status =True
                self.current_status["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                hDll = ctypes.WinDLL(self.dll_path)
                if hDll != 0:
                    result = hDll.InitLibrary()
                    hDll.GetPrinterFullStatus.argtypes = [
                        ctypes.c_long,
                        ctypes.POINTER(ctypes.c_ubyte),
                        ctypes.POINTER(PrinterStatusStruct)
                    ]
                    
                    hDll.GetPrinterFullStatus.restype = ctypes.c_int
                    if openusbstatus == True :
                        if device_id != None :
                            Result = hDll.CloseDevice(device_id)
                        device_id = self.openprinterUSBEx()

                    if device_id!= False:
                        get_printer_status = "available"
                        get_onlineStatus = "online"
                        get_paperJamStatus = "Normal"
                        openusbstatus =False
                        status_buffer = (ctypes.c_ubyte * 4)()
                        printer_status = PrinterStatusStruct()
                        try:
                            result = hDll.GetPrinterFullStatus(device_id, status_buffer, ctypes.byref(printer_status))
                        except :
                            openusbstatus = True
                        if result != 0:
                            get_printer_status = "unavailable"
                            openusbstatus = True
                        # print(f"✅ Printer Status: 0x{status_buffer[0]:02X} 0x{status_buffer[1]:02X} 0x{status_buffer[2]:02X} 0x{status_buffer[3]:02X}")
                        status_list = []

                        # **BYTE 1 (status_buffer[0])**
                        if status_buffer[0] & 0x01:  # 0x01 -> NO PAPER
                            get_printer_status = "unavailable"
                            get_paperEndStatus = "paper end"
                            status_list.append("NO PAPER")
                        elif status_buffer[0] & 0x04:  # 0x04 -> NEAR PAPER END
                            get_printer_status = "available"
                            get_paperEndStatus = "paper near end"
                            status_list.append("NEAR PAPER END")
                        # if status_buffer[0] & 0x20:  # 0x20 -> TICKET OUT
                        #     status_list.append("TICKET OUT")

                        # **BYTE 2 (status_buffer[1])**
                        elif status_buffer[1] & 0x01:  # 0x01 -> HEAD UP
                            get_printer_status = "unavailable"
                            status_list.append("HEAD UP")
                        elif status_buffer[1] & 0x02:  # 0x02 -> COVER OPEN
                            get_printer_status = "unavailable"
                            status_list.append("COVER OPEN")
                        # if status_buffer[1] & 0x04:  # 0x04 -> SPOOLING
                        #     status_list.append("SPOOLING")
                        # if status_buffer[1] & 0x08:  # 0x08 -> PAPER ROLLING
                        #     status_list.append("PAPER ROLLING")
                        # if status_buffer[1] & 0x10:  # 0x10 -> LF PRESSED
                        #     status_list.append("LF PRESSED")
                        # if status_buffer[1] & 0x20:  # 0x20 -> FF PRESSED
                        #     status_list.append("FF PRESSED")

                        # **BYTE 3 (status_buffer[2])**
                        # if status_buffer[2] & 0x01:  # 0x01 -> OVER TEMPERATURE
                        #     status_list.append("OVER TEMPERATURE")
                        # if status_buffer[2] & 0x02:  # 0x02 -> OVER VOLTAGE
                        #     status_list.append("OVER VOLTAGE")
                        elif status_buffer[2] & 0x04:  # 0x04 -> PAPER JAM
                            get_printer_status = "unavailable"
                            get_paperJamStatus ="paper jam"
                            status_list.append("PAPER JAM")

                        # **BYTE 4 (status_buffer[3])**
                        # if status_buffer[3] & 0x01:  # 0x01 -> CUTTER ERROR
                        #     status_list.append("CUTTER ERROR")
                        # if status_buffer[3] & 0x02:  # 0x02 -> RAM ERROR
                        #     status_list.append("RAM ERROR")
                        # if status_buffer[3] & 0x04:  # 0x04 -> EEPROM ERROR
                        #     status_list.append("EEPROM ERROR")
                           
                        # status_buffer_text = "; ".join(status_list) if status_list else "Nothing to report."

                 
                    else :
                       get_printer_status = "unavailable"
                       get_onlineStatus = "offline"
                       get_paperEndStatus="None"
                       get_paperJamStatus="None"
                       logger.exception("Printer VKP80III not found") 

                    # self.current_status["onlineStatus"] = get_onlineStatus
                    # self.current_status["printerStatus"]= get_printer_status
                    # self.current_status["paperEndStatus"]= get_paperEndStatus
                    # self.current_status["paperJamStatus"] = get_paperJamStatus
                    # self.savejsonstatus()   
                else:
                    raise FileNotFoundError("File CuCustomWndAPI.dll not founded.")
                self.current_status["onlineStatus"] = get_onlineStatus
                self.current_status["printerStatus"]= get_printer_status
                self.current_status["paperEndStatus"]= get_paperEndStatus
                self.current_status["paperJamStatus"] = get_paperJamStatus
                self.savejsonstatus()  
                remove_timestamp = {i:self.current_status[i] for i in self.current_status if i!='timestamp'}
                if self.previuos_status != remove_timestamp:
                    self.post()
                    self.previuos_status = remove_timestamp
                time.sleep(1)
            except Exception:
                logger.exception("Check printer status error")
                time.sleep(1)
           
    def post(self):
        try:
            logger.debug("Posting to status server: {}".format(self.current_status))
            response = requests.post(os.getenv("SERVER_URL"), json=self.current_status, auth=(os.getenv("USERNAME"), os.getenv("PASSWORD")))
            
            # print("json respone ", response,",  logger ", logger,", self.current_status :",self.current_status)
            logger.debug(response.json())
        except Exception:
            logger.exception("Posting to status server eror")

    def get_status(self):
        return self.current_status

    def savejsonstatus(self):
        # โหลดค่าที่อยู่ของ Printer โดยตรงในฟังก์ชันนี้
        config_path = os.path.abspath(os.getenv('KIOSK_LOGFILE_LOCATION'))  # ถ้าไม่พบค่าใช้ค่า default
        target_model = "VKP80III"

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
        # สร้าง timestamp สำหรับชื่อไฟล์ (แค่ชั่วโมง)
        timestampfile = datetime.now().strftime("%Y%m%d%H")  # ใช้แค่ปี-เดือน-วัน-ชั่วโมง

        # สร้าง path ให้ถูกต้อง
        folder_path = os.path.join(printer_location, "Status", timestampfolder)  # ใช้ path ตามที่ต้องการ
        file_path = os.path.join(folder_path, f"PrinterStatusJson{timestampfile}.json")

        # Debug ดู path ว่าถูกต้องไหม
        print(f"Folder Path: {folder_path}")
        print(f"File Path: {file_path}")

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






# 1st byte: 18 - offline
# 2nd byte: 28 - cutter error/ hardware error --> paper jam
