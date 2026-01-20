# CineSlice 🎬

**CineSlice** is a professional-grade video frame extraction tool built with Python and PySide6. It allows users to extract high-quality still images from video files with precision control, offering a clean, modern interface and robust error handling.

<p align="center">
  <img src="icon.ico" width="128" height="128" alt="CineSlice Logo">
</p>

## 🚀 Features

* **Precision Extraction:** Extract every Nth frame (e.g., "1 frame every second").
* **Smart Estimation:** Real-time estimates for final frame count and storage size.
* **Lossless Engine:** Powered by FFmpeg for bit-perfect image retrieval.
* **Robust Architecture:** * Runs extraction in a background `QThread` to keep the UI responsive.
    * Includes a safe cancellation system that zips partial results.
    * Automatic session logging and crash reporting.
* **Format Support:** Exports to PNG, JPG, or BMP.

## 🛠️ Built With

* **Language:** Python 3.11
* **GUI:** PySide6 (Qt for Python)
* **Core Engine:** FFmpeg (subprocess automation)

## 📦 Installation & Usage

### Option A: Download (Windows)
No coding required. Download the latest version from the [Releases Page](link-to-releases).
1. Unzip the folder.
2. Run `CineSlice.exe`.

### Option B: Run from Source
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/yourusername/CineSlice.git](https://github.com/yourusername/CineSlice.git)
    cd CineSlice
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Setup FFmpeg:**
    * Download `ffmpeg.exe` and `ffprobe.exe` (Essentials Build).
    * Create a folder named `ffmpeg` in the project root.
    * Place the `.exe` files inside `ffmpeg/`.
4.  **Run the app:**
    ```bash
    python main.py
    ```

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.