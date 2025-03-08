from PyQt6.QtWidgets import QWidget, QTextEdit, QPushButton
from PyQt6 import uic
from datetime import datetime
import json

class Ui_LogFile(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('Designer/logfile.ui', self)  # โหลด UI ที่สร้างจาก Qt Designer
        self.textLogfile = self.findChild(QTextEdit, 'textLogfile')
        self.btnBack = self.findChild(QPushButton, 'btnBack')
        self.btnBack.clicked.connect(self.on_monitoring_selected)
        
        # ตรวจสอบว่า textLogfile ถูกโหลดเรียบร้อยหรือไม่
        if self.textLogfile is None:
            print("Error: textLogfile widget not found.")
        else:
            print("textLogfile widget loaded successfully.")

    def load_logfile_data(self, json_file_path):
        if self.textLogfile is None:
            print("Error: textLogfile widget is not available.")
            return  # ถ้า textLogfile ไม่ถูกโหลด ก็จะไม่ทำการแสดงข้อมูล
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                if not isinstance(data, list):  # ตรวจสอบว่า JSON ต้องเป็น List
                    print("Error: JSON ไฟล์ต้องเป็น List ของข้อมูล log")
                    return
                try:
                        data.sort(key=lambda x: datetime.strptime(x.get("timestamp", "1970-01-01 00:00:00.000"), "%Y-%m-%d %H:%M:%S.%f"), reverse=True)
                except ValueError:
                    return

                log_content = ""

                # หัวตาราง (Header)
                header = (f"{'timestamp'.ljust(25)} | {'senderIp'.ljust(15)} | {'printerId'.ljust(12)} | "
                        f"{'printerStatus'.ljust(15)} | {'onlineStatus'.ljust(10)} | {'paperEndStatus'.ljust(12)} | "
                        f"{'paperJamStatus'.ljust(12)}\n")
                log_content += header
                log_content += "-" * len(header) + "\n"  # ขีดเส้นแบ่ง Header

                # Loop ผ่านข้อมูล log
                for entry in data:  # ใช้ JSON ที่เป็น List โดยตรง
                    time_str = entry.get('timestamp', 'No Time')
                    sender_ip = entry.get('senderIp', 'No IP')
                    printer_id = entry.get('printerId', 'No PrinterID')
                    printer_status = entry.get('printerStatus', 'Unknown')
                    online_status = entry.get('onlineStatus', 'Unknown')
                    paper_end_status = entry.get('paperEndStatus', 'Unknown')
                    paper_jam_status = entry.get('paperJamStatus', 'Unknown')

                    # จัดรูปแบบข้อมูลให้อ่านง่ายขึ้น
                    log_content += (f"{time_str.ljust(25)} | {sender_ip.ljust(15)} | {printer_id.ljust(12)} | "
                                    f"{printer_status.ljust(15)} | {online_status.ljust(10)} | {paper_end_status.ljust(12)} | "
                                    f"{paper_jam_status.ljust(12)}\n")

                # แสดงข้อมูลใน textLogfile
                self.textLogfile.setText(log_content)
        
        except FileNotFoundError:
            print(f"❌ ไม่พบไฟล์ JSON ที่ {json_file_path}")
        except json.JSONDecodeError:
            print("❌ เกิดข้อผิดพลาดในการอ่านไฟล์ JSON (ไฟล์อาจไม่ใช่ JSON ที่ถูกต้อง)")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {e}")

        
    def on_monitoring_selected(self):
        self.close()  # ปิดหน้าจอปัจจุบัน
        from monitoring import Ui_Monitoring  # โหลด UI ของหน้าจอ Monitoring
        self.new_window = Ui_Monitoring()  # สร้างอินสแตนซ์ของหน้าจอ Monitoring
        self.new_window.show()  # แสดงหน้าจอใหม่
