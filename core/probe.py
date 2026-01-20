import subprocess
import json
import os
import sys

def get_ffmpeg_path(tool="ffmpeg"):
    """
    Locates ffmpeg/ffprobe binaries.
    Prioritizes a local 'ffmpeg' folder (for the bundled EXE),
    then falls back to system PATH.
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled .exe
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    local_bin = os.path.join(base_path, "ffmpeg", f"{tool}.exe" if os.name == 'nt' else tool)
    
    if os.path.exists(local_bin):
        return local_bin
    return tool  # Fallback to system PATH

def get_video_info(file_path):
    """
    Runs ffprobe to get JSON metadata about the video.
    """
    ffprobe_cmd = [
        get_ffmpeg_path("ffprobe"),
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration,nb_frames",
        "-of", "json",
        file_path
    ]

    try:
        # startupinfo to hide console window on Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        result = subprocess.run(
            ffprobe_cmd,
            capture_output=True,
            text=True,
            startupinfo=startupinfo
        )
        data = json.loads(result.stdout)
        stream = data["streams"][0]

        # Calculate FPS
        num, den = map(int, stream.get("r_frame_rate", "30/1").split('/'))
        fps = num / den if den != 0 else 30.0

        # Get Duration
        duration = float(stream.get("duration", 0))
        
        # Get Frame Count (sometimes missing in metadata, so we estimate)
        frames = stream.get("nb_frames")
        if frames:
            frames = int(frames)
        else:
            frames = int(duration * fps)

        return {
            "width": int(stream.get("width", 0)),
            "height": int(stream.get("height", 0)),
            "fps": fps,
            "duration": duration,
            "frames": frames
        }
    except Exception as e:
        print(f"Probe Error: {e}")
        return None