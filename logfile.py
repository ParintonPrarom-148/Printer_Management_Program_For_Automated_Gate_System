from PyQt6.QtWidgets import QWidget, QTextEdit,QPushButton
from PyQt6 import uic
import json
from datetime import datetime

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
        
        # อ่านข้อมูลจากไฟล์ JSON ที่ระบุ
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                if 'PrinterLog' in data:
                    printer_log_data = data['PrinterLog']
                    log_content = ""

                    # Loop ผ่านข้อมูล log ทั้งหมด
                    for entry in printer_log_data:
                        # แปลงเวลาจาก "2025-02-24 10:00" เป็น "7/1/2024 12:09:03 PM"
                        time = datetime.strptime(entry['Time'], '%Y-%m-%d %H:%M')
                        formatted_time = time.strftime('%m/%d/%Y %I:%M:%S %p')
                        
                        # สร้างข้อความในรูปแบบที่ต้องการ
                        log_content += f"{formatted_time} | {entry['Document ID']} | {entry['Document Status']} | {entry['Printer Status']} | {entry['Paper Status']} | {entry['Error']}\n"
                    
                    # แสดงข้อมูลที่ได้ใน textLogfile
                    self.textLogfile.setText(log_content)
                else:
                    print("Error: 'PrinterLog' not found in the JSON data.")
        except Exception as e:
            print(f"An error occurred: {e}")
        
    def on_monitoring_selected(self):
        self.close()  # ปิดหน้าจอปัจจุบัน
        from monitoring import Ui_Monitoring  # โหลด UI ของหน้าจอ Monitoring
        self.new_window = Ui_Monitoring()  # สร้างอินสแตนซ์ของหน้าจอ Monitoring
        self.new_window.show()  # แสดงหน้าจอใหม่
