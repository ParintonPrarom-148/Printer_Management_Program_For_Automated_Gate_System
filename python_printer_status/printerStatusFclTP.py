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
        hostname=socket.gethostname()
        self.IPAddr=socket.gethostbyname(hostname)

        self.current_status = {
                "printerId": os.getenv("LANE_print2"),
                "printerStatus": "unavailable",
                "senderIp": self.IPAddr,
                "onlineStatus": "offline",
                "paperEndStatus": "None",
                "paperJamStatus": "None",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            }
        self.previuos_status = {}
        self.dll_path = os.path.join(work_dir, "FTPCtrl_x64.dll")

        schedule.every(int(os.getenv("POST_PRINTER_STATUS_SECOND_INTERVAL"))).seconds.do(self.post)
        Thread(target=self.check_status, args=()).start()

    def check_status(self):
        while True:
            schedule.run_pending()
            try:
                self.current_status["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                hDll = ctypes.WinDLL(self.dll_path)
                # Define the function prototypes
                # pFclTP_Search_USB = ctypes.WINFUNCTYPE(ctypes.c_ulong)
                # pFclTP_GetVendorCommand = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p)

                if hDll != 0:
                    # Get address of export function
                    # fnFclTP_Search_USB = ctypes.cast(ctypes.windll.kernel32.GetProcAddress(hDll, b"FclTP_Search_USB"), pFclTP_Search_USB)
                    # fnFclTP_GetVendorCommand = ctypes.cast(ctypes.windll.kernel32.GetProcAddress(hDll, b"FclTP_GetVendorCommand"), pFclTP_GetVendorCommand)
                    FclTP_Search_USB = hDll.FclTP_Search_USB
                    FclTP_GetVendorCommand = hDll.FclTP_GetVendorCommand

                    if FclTP_Search_USB() == 1: # USB port driver detection
                        VendorCmd = VENDOR_COMMAND()
                        VendorCmd.bRequest = 1
                        VendorCmd.wValueH = 0
                        VendorCmd.wValueL = 0
                        VendorCmd.wIndexH = 0
                        VendorCmd.wIndexL = 0
                        VendorCmd.wLengthH = 0
                        VendorCmd.wLengthL = 4 # Receiving data is 4 bytes
                        VendorCmd.unitLength = ctypes.sizeof(VendorCmd)

                        RcvData = RECEIVE_DATA()
                        RcvData.unitLength = ctypes.sizeof(RcvData)
                        # logger.info("{} {} {} {}".format(RcvData.Data[0], RcvData.Data[1], RcvData.Data[2], RcvData.Data[3]))
                        
                        if FclTP_GetVendorCommand(ctypes.byref(VendorCmd), ctypes.byref(RcvData)) == 1: # Execute vendor request
                            self.current_status["printerStatus"]= "available"
                            self.current_status["onlineStatus"] = "online"  
                            print(f"✅ Printer Status: 0x{RcvData.Data[0]:02X} 0x{RcvData.Data[1]:02X} 0x{RcvData.Data[2]:02X} 0x{RcvData.Data[3]:02X}")
                            if RcvData.Data[1] == 0x28:
                                # paper jam
                                self.current_status["printerStatus"]= "unavailable"
                                self.current_status["paperEndStatus"]= "normal"
                                self.current_status["paperJamStatus"] = "paper jam"
                            elif RcvData.Data[2] == 0x01:
                                # paper near end
                                self.current_status["paperEndStatus"] = "paper near-end"
                                self.current_status["paperJamStatus"] = "normal"
                            elif RcvData.Data[2] == 0x04 or RcvData.Data[2] == 0x05:
                                # paper out
                                self.current_status["printerStatus"]= "unavailable"
                                self.current_status["paperEndStatus"] = "paper out"
                                self.current_status["paperJamStatus"] = "normal"
                            elif RcvData.Data[1] == 0x04:
                                # platen open
                                self.current_status["printerStatus"]= "unavailable"
                                self.current_status["paperEndStatus"]= "None"
                                self.current_status["paperJamStatus"]= "None"
                            else:
                                
                                self.current_status["paperEndStatus"]= "normal"
                                self.current_status["paperJamStatus"]= "normal"
                    else:
                        self.current_status["onlineStatus"]= "offline"
                        self.current_status["printerStatus"]= "unavailable"
                        self.current_status["paperEndStatus"]= "None"
                        self.current_status["paperJamStatus"]= "None"
                    self.savejsonstatus()
                    # Unload DLL
                    # ctypes.windll.kernel32.FreeLibrary(hDll)
                    hDll = None


                else:
                    raise FileNotFoundError("File FTPCtrl.dll not founded.")

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
        # print("self.current_status2",self.current_status)
        return self.current_status
    
    def savejsonstatus(self):
        # แปลงข้อมูล JSON เป็น String
        json_data = json.dumps(self.current_status, indent=4, ensure_ascii=False)
        file_path = "logstatusprint/printer_status2.json"
        # บันทึกลงไฟล์
        with open(file_path, "w", encoding="utf-8") as json_file:
            json_file.write(json_data)
# 1st byte: 18 - offline
# 2nd byte: 28 - cutter error/ hardware error --> paper jam
