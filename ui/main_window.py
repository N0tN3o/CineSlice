import os
import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QLineEdit, QFileDialog, 
                               QComboBox, QSpinBox, QProgressBar, QMessageBox, QGroupBox, QStyle)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from core.worker import ExtractionWorker
from core.probe import get_video_info

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CineSlice · Precision Frame Extractor")
        self.setFixedSize(600, 500)
        
        # Set window icon
        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        icon_path = os.path.join(base_path, "icon.ico")
        self.setWindowIcon(QIcon(icon_path))
        
        # State
        self.video_info = None
        self.worker = None

        # UI Setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        self.setup_ui()

    def setup_ui(self):
        # --- 1. File Selection ---
        file_group = QGroupBox("Input Video")
        file_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select a video file...")
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.path_input)
        file_layout.addWidget(self.browse_btn)
        file_group.setLayout(file_layout)
        self.layout.addWidget(file_group)

        # --- 2. Output Directory ---
        out_group = QGroupBox("Output Directory")
        out_layout = QHBoxLayout()
        self.out_input = QLineEdit()
        self.out_browse_btn = QPushButton("Select Folder")
        self.out_browse_btn.clicked.connect(self.browse_folder)
        out_layout.addWidget(self.out_input)
        out_layout.addWidget(self.out_browse_btn)
        out_group.setLayout(out_layout)
        self.layout.addWidget(out_group)

        # --- 3. Settings ---
        settings_group = QGroupBox("Extraction Settings")
        settings_layout = QHBoxLayout()
        
        # Format
        settings_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["png", "jpg", "bmp"])
        settings_layout.addWidget(self.format_combo)
        
        # Nth Frame
        settings_layout.addWidget(QLabel("Extract every:"))
        self.nth_spin = QSpinBox()
        self.nth_spin.setRange(1, 1000)
        self.nth_spin.setValue(1)
        self.nth_spin.setSuffix(" frame")
        self.nth_spin.valueChanged.connect(self.update_estimates)
        settings_layout.addWidget(self.nth_spin)
        
        settings_group.setLayout(settings_layout)
        self.layout.addWidget(settings_group)

        # --- 4. Info Panel ---
        self.info_label = QLabel("Waiting for file...")
        self.info_label.setStyleSheet("color: #666; font-style: italic;")
        self.layout.addWidget(self.info_label)

        # --- 5. Progress ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        self.layout.addWidget(self.status_label)

        # --- 6. Actions ---
        btn_layout = QHBoxLayout()
        self.extract_btn = QPushButton("Start Extraction")
        self.extract_btn.setMinimumHeight(40)
        self.extract_btn.clicked.connect(self.start_extraction)
        self.extract_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self.cancel_extraction)
        self.cancel_btn.setEnabled(False)

        btn_layout.addWidget(self.extract_btn)
        btn_layout.addWidget(self.cancel_btn)
        self.layout.addLayout(btn_layout)

    def browse_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open Video", "", "Video Files (*.mp4 *.mov *.avi *.mkv)")
        if fname:
            self.path_input.setText(fname)
            # Default output to same folder
            self.out_input.setText(os.path.dirname(fname))
            self.analyze_video(fname)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.out_input.setText(folder)

    def analyze_video(self, path):
        self.status_label.setText("Analyzing video...")
        self.extract_btn.setEnabled(False)
        # In a real app, run this in a thread too, but it's fast enough for now
        self.video_info = get_video_info(path)
        
        if self.video_info:
            self.update_estimates()
            self.extract_btn.setEnabled(True)
            self.status_label.setText("Ready")
        else:
            self.status_label.setText("Error reading video metadata")

    def update_estimates(self):
        if not self.video_info:
            return
            
        total_frames = self.video_info['frames']
        nth = self.nth_spin.value()
        extracted_count = int(total_frames / nth)
        
        # Rough estimate: JPG ~300KB, PNG ~2MB (very rough)
        fmt = self.format_combo.currentText()
        size_per_frame_mb = 0.3 if fmt == 'jpg' else 1.5
        total_size_mb = extracted_count * size_per_frame_mb
        
        info_text = (
            f"Duration: {self.video_info['duration']:.2f}s | "
            f"FPS: {self.video_info['fps']:.2f} | "
            f"Total Frames: {total_frames}\n"
            f"Will extract approx {extracted_count} images (~{total_size_mb:.1f} MB unzipped)"
        )
        self.info_label.setText(info_text)

    def start_extraction(self):
        settings = {
            'input_path': self.path_input.text(),
            'output_dir': self.out_input.text(),
            'format': self.format_combo.currentText(),
            'nth_frame': self.nth_spin.value(),
            'total_frames_est': self.video_info['frames'] if self.video_info else 1000
        }

        self.worker = ExtractionWorker(settings)
        self.worker.progress_updated.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.log_message.connect(lambda msg: print(f"[LOG] {msg}")) # Simple console logging
        
        self.toggle_ui(extracting=True)
        self.worker.start()

    def cancel_extraction(self):
        if self.worker:
            self.status_label.setText("Cancelling... Please wait for ZIP.")
            self.worker.cancel()
            self.cancel_btn.setEnabled(False) # Prevent double click

    def on_progress(self, percent, message):
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)

    def on_finished(self, success, message):
        self.toggle_ui(extracting=False)
        self.progress_bar.setValue(100 if success else 0)
        self.status_label.setText("Done" if success else "Failed")
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Result")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Information if success else QMessageBox.Critical)
        msg_box.setWindowIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning))
        msg_box.exec()

    def toggle_ui(self, extracting):
        self.extract_btn.setEnabled(not extracting)
        self.cancel_btn.setEnabled(extracting)
        self.browse_btn.setEnabled(not extracting)
        self.out_browse_btn.setEnabled(not extracting)
        self.nth_spin.setEnabled(not extracting)
