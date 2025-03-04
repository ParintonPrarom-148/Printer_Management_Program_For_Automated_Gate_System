import sys
import os
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QMessageBox
from PyQt6.QtCore import QTimer

# เพิ่ม path ของ `printerStatusFclTP.py` และ `printerStatusVKP80iii.py`
printer_status_path = os.path.join(os.getcwd(), "python_printer_status")
sys.path.append(printer_status_path)

# นำเข้าโมดูลสถานะเครื่องพิมพ์
from printerStatusFclTP import printerStatus2
from printerStatusVKP80iii import printerStatus1

class PrinterStatusUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Printer Status Monitor")
        self.setGeometry(100, 100, 400, 200)

        work_dir = os.getcwd()
        self.primary_printer = printerStatus1(work_dir)
        self.secondary_printer = printerStatus2(work_dir)

        self.current_printer = self.primary_printer
        self.is_using_secondary = False

        self.status_label = QLabel("Loading...", self)
        self.status_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)

    def update_status(self):
        primary_status = self.primary_printer.get_status()
        secondary_status = self.secondary_printer.get_status()

        if primary_status["printerStatus"] == "unavailable":
            if not self.is_using_secondary:
                QMessageBox.warning(self, "แจ้งเตือน", "เครื่องหลักมีปัญหากำลังพิมพ์งานที่เครื่องสำรอง")
                self.current_printer = self.secondary_printer
                self.is_using_secondary = True
        
        if primary_status["printerStatus"] == "unavailable" and secondary_status["printerStatus"] == "unavailable":
            QMessageBox.critical(self, "แจ้งเตือน", "เครื่องหลักเเละเครื่องสำรองมีปัญหา...")
        
        if self.is_using_secondary and primary_status["printerStatus"] == "available":
            QMessageBox.information(self, "แจ้งเตือน", "เครื่องหลักกลับมาใช้งานได้แล้ว กำลังสลับกลับไปที่เครื่องหลัก")
            self.current_printer = self.primary_printer
            self.is_using_secondary = False
        
        display_text = (
            f"Online Status: {self.current_printer.get_status()['onlineStatus']}\n"
            f"Printer Status: {self.current_printer.get_status()['printerStatus']}\n"
            f"Paper Jam: {self.current_printer.get_status()['paperJamStatus']}\n"
            f"Paper End: {self.current_printer.get_status()['paperEndStatus']}"
        )
        self.status_label.setText(display_text)

    def closeEvent(self, event):
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PrinterStatusUI()
    window.show()
    sys.exit(app.exec())