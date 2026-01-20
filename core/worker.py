import os
import shutil
import subprocess
import re
import zipfile
import time
from PySide6.QtCore import QThread, Signal
from .probe import get_ffmpeg_path

class ExtractionWorker(QThread):
    # Signals to update UI
    progress_updated = Signal(int, str)  # progress %, status text
    finished = Signal(bool, str)         # success?, message
    log_message = Signal(str)            # For debug logs

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.is_cancelled = False
        self.process = None

    def run(self):
        input_path = self.settings['input_path']
        output_dir = self.settings['output_dir']
        img_format = self.settings['format']
        nth_frame = self.settings['nth_frame']
        
        # 1. Create Temp Directory
        temp_dir = os.path.join(output_dir, "temp_extraction")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

        try:
            self.log_message.emit("Starting FFmpeg process...")
            
            # 2. Build FFmpeg Command
            cmd = [
                get_ffmpeg_path("ffmpeg"),
                "-i", input_path,
                "-vf", f"select=not(mod(n\,{nth_frame}))",
                "-vsync", "vfr",
                "-q:v", "2",  # High quality for JPG
                os.path.join(temp_dir, f"frame_%06d.{img_format}")
            ]

            # Windows-specific: Hide console
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                startupinfo=startupinfo
            )

            # 3. Monitor Progress
            # FFmpeg writes stats to stderr
            total_frames = self.settings.get('total_frames_est', 1000)
            
            while True:
                if self.is_cancelled:
                    self.process.terminate()
                    break

                output = self.process.stderr.readline()
                if output == '' and self.process.poll() is not None:
                    break
                
                if output:
                    # Regex to find "frame= 123"
                    match = re.search(r"frame=\s*(\d+)", output)
                    if match:
                        current_frame = int(match.group(1))
                        # Scale progress based on Nth frame extraction
                        # (If extracting every 10th frame, total output frames is total/10)
                        expected_output_frames = total_frames / nth_frame
                        percent = min(100, int((current_frame / expected_output_frames) * 100))
                        self.progress_updated.emit(percent, f"Extracting frame {current_frame}...")

            # 4. Handle Completion or Cancellation
            zip_name = f"frames_{os.path.basename(input_path)}.zip"
            zip_path = os.path.join(output_dir, zip_name)

            if self.is_cancelled:
                self.log_message.emit("User cancelled. Zipping partial results...")
                self.progress_updated.emit(99, "Zipping partial results...")
            else:
                self.log_message.emit("Extraction complete. Zipping...")
                self.progress_updated.emit(100, "Archiving frames...")

            # 5. Zip the frames
            self.create_zip(temp_dir, zip_path)

            # 6. Cleanup
            shutil.rmtree(temp_dir)

            if self.is_cancelled:
                self.finished.emit(True, f"Cancelled. \nSaved partial ZIP to: {zip_path}")
            else:
                self.finished.emit(True, f"Success! \nSaved to: {zip_path}")

        except Exception as e:
            self.log_message.emit(f"Critical Error: {str(e)}")
            self.finished.emit(False, str(e))

    def create_zip(self, source_dir, output_path):
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), file)

    def cancel(self):
        self.is_cancelled = True