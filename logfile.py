from PyQt6.QtWidgets import QWidget, QTextEdit, QPushButton
from PyQt6 import uic
from PyQt6.QtCore import QTimer
from datetime import datetime
import json
import os
# กำหนดเส้นทางไฟล์ .ui โดยใช้ __file__ เพื่อให้ทำงานได้จากไฟล์ executable
ui_file = os.path.join(os.path.dirname(__file__), 'Designer', 'logfile.ui')

class Ui_LogFile(QWidget):
    def __init__(self, json_file_path):
        super().__init__()
        # โหลด UI
        uic.loadUi(ui_file, self)

        # เชื่อมต่อ Widget กับ UI
        self.textLogfile = self.findChild(QTextEdit, 'textLogfile')
        self.btnBack = self.findChild(QPushButton, 'btnBack')
        self.btnBack.clicked.connect(self.on_monitoring_selected)

        # เก็บ path ของไฟล์ JSON ที่จะโหลด
        self.json_file_path = json_file_path

        # ตั้งค่า Timer ให้รีเฟรชข้อมูลทุกๆ 3 วินาที
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_logfile_data)
        self.timer.start(3000)  # 3000 มิลลิวินาที = 3 วินาที

        # โหลดข้อมูลครั้งแรกเมื่อเปิดหน้าจอ
        self.load_logfile_data()

    def load_logfile_data(self):
        if self.textLogfile is None:
            print("Error: textLogfile widget ไม่สามารถเข้าถึงได้")
            return  # ถ้า textLogfile ไม่ถูกโหลด ก็จะไม่ทำการแสดงข้อมูล
        
        if not os.path.exists(self.json_file_path):
            print(f"❌ ไม่พบไฟล์ JSON: {self.json_file_path}")
            return

        try:
            # เปิดไฟล์ JSON และโหลดข้อมูล
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                # ตรวจสอบว่า JSON เป็น List ของข้อมูล
                if not isinstance(data, list):  
                    print("Error: JSON ไฟล์ต้องเป็น List ของข้อมูล log")
                    return

                # เรียงข้อมูล log ตามเวลา (จากใหม่สุดไปเก่าสุด)
                try:
                    data.sort(key=lambda x: datetime.strptime(x.get("timestamp", "1970-01-01 00:00:00.000"), "%Y-%m-%d %H:%M:%S.%f"), reverse=True)
                except ValueError:
                    return

                log_content = ""

                # หัวตาราง (Header) สำหรับแสดงข้อมูล log
                header = (f"{'timestamp'.ljust(25)} | {'location'.ljust(15)} | {'senderIp'.ljust(15)} | {'printerId'.ljust(12)} | "
                        f"{'printerStatus'.ljust(15)} | {'onlineStatus'.ljust(10)} | {'paperEndStatus'.ljust(12)} | "
                        f"{'paperJamStatus'.ljust(12)}\n")
                log_content += header
                log_content += "-" * len(header) + "\n"  # ขีดเส้นแบ่ง Header

                # Loop ผ่านข้อมูล log และแสดงข้อมูลในรูปแบบที่อ่านง่าย
                for entry in data:
                    time_str = entry.get('timestamp', 'No Time')
                    location = entry.get('location', 'No Location')
                    sender_ip = entry.get('senderIp', 'No IP')
                    printer_id = entry.get('printerId', 'No PrinterID')
                    printer_status = entry.get('printerStatus', 'Unknown')
                    online_status = entry.get('onlineStatus', 'Unknown')
                    paper_end_status = entry.get('paperEndStatus', 'Unknown')
                    paper_jam_status = entry.get('paperJamStatus', 'Unknown')

                    log_content += (f"{time_str.ljust(25)} | {location.ljust(15)} | {sender_ip.ljust(15)} | {printer_id.ljust(12)} | "
                                    f"{printer_status.ljust(15)} | {online_status.ljust(10)} | {paper_end_status.ljust(12)} | "
                                    f"{paper_jam_status.ljust(12)}\n")

                # แสดงข้อมูล log ใน QTextEdit
                self.textLogfile.setText(log_content)

        except json.JSONDecodeError:
            print("❌ เกิดข้อผิดพลาดในการอ่านไฟล์ JSON (ไฟล์อาจไม่ใช่ JSON ที่ถูกต้อง)")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {e}")

    # ฟังก์ชันเมื่อกดปุ่ม "กลับ" เพื่อไปที่หน้าจอ Monitoring
    def on_monitoring_selected(self):
        self.close()  # ปิดหน้าจอ LogFile
        from monitoring import Ui_Monitoring  # โหลดหน้าจอ Monitoring
        self.new_window = Ui_Monitoring()  # สร้างอินสแตนซ์ของหน้าจอ Monitoring
        self.new_window.show()  # แสดงหน้าจอใหม่
