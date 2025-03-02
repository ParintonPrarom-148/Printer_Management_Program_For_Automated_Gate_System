from PyQt6.QtWidgets import QWidget, QTextEdit, QPushButton
from PyQt6 import uic
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
        
        # อ่านข้อมูลจากไฟล์ JSON ที่ระบุ
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                if 'PrinterLog' in data:
                    printer_log_data = data['PrinterLog']
                    log_content = ""

                    column_widths = [24, 16, 15, 10, 15, 12, 12, 12]  # กำหนดความกว้างของแต่ละคอลัมน์
                    columns = ["Time", "PrinterID", "PrinterModel", "DocumentID", "DocumentStatus", "PrinterStatus", "PaperStatus", "Error"]

                    # สร้าง Header โดยใช้ f-string และความกว้างที่กำหนด
                    header = " | ".join(f"{col:<{w}}" for col, w in zip(columns, column_widths))

                    # สร้างเส้นคั่นที่มีความยาวเท่ากับ Header
                    separator = "-" * len(header)

                    # เพิ่ม Header และเส้นคั่นลงใน log_content
                    log_content += header + "\n"
                    log_content += separator + "\n"

                    # Loop ผ่านข้อมูล log ทั้งหมด
                    for entry in printer_log_data:
                        # ดึงข้อมูลจาก JSON ทุกตัวแปร และใช้ค่าเริ่มต้นหากไม่มีข้อมูล
                        time_str = entry.get('Time', 'No Time')
                        printer_id = entry.get('PrinterID', 'No PrinterID')
                        printer_model = entry.get('PrinterModel', 'No PrinterModel')
                        document_id = entry.get('DocumentID', 'No DocumentID')
                        document_status = entry.get('DocumentStatus', 'No DocumentStatus')
                        printer_status = entry.get('PrinterStatus', 'No PrinterStatus')
                        paper_status = entry.get('PaperStatus', 'No PaperStatus')
                        error = entry.get('Error', 'No Error')

                        # ใช้ column_widths เดียวกับ Header เพื่อให้ตรงกัน
                        log_content += " | ".join(f"{val:<{w}}" for val, w in zip(
                        [time_str, printer_id, printer_model, document_id, document_status, printer_status, paper_status, error], column_widths)) + "\n"
                    
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
