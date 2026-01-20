import sys
import traceback
import logging
import os
from datetime import datetime
from PySide6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow

# Setup logging with date/time-bound filename (timestamp = app start time)
logs_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(logs_folder, exist_ok=True)
log_filename = os.path.join(logs_folder, f"session_started_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(filename=log_filename, level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("Error:", tb)
    logging.error("Uncaught exception:\n" + tb)
    
    app = QApplication.instance()
    if app:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("An unexpected error occurred.")
        msg.setInformativeText("The application needs to close. A log file has been saved.")
        msg.setDetailedText(tb)
        msg.exec()
        app.quit()

sys.excepthook = excepthook

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())