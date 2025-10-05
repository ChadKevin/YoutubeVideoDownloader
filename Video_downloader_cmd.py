import yt_dlp
import os
import subprocess

# ----------------------------
# Custom logger for yt-dlp
# ----------------------------
class MyLogger:
    def __init__(self, log_callback):
        self.log_callback = log_callback

    def debug(self, msg):
        if "Downloading webpage" in msg or "Downloading video info" in msg:
            return  # skip spammy messages
        self.log_callback(msg, "info")

    def warning(self, msg):
        self.log_callback(msg, "error")

    def error(self, msg):
        self.log_callback(msg, "error")


# ----------------------------
# FFmpeg audio converter
# ----------------------------
def convert_opus_to_mp3(video_path, log_callback=None):
    base, ext = os.path.splitext(video_path)
    temp_path = base + "_converted.mp4"
    try:
        if log_callback:
            log_callback("Converting audio to MP3...", "info")

        subprocess.run([
            "ffmpeg",
            "-i", video_path,
            "-c:v", "copy",
            "-c:a", "mp3",
            "-y",
            temp_path
        ], check=True)

        os.replace(temp_path, video_path)

        if log_callback:
            log_callback(f"Audio converted to MP3: {os.path.basename(video_path)}", "success")

    except subprocess.CalledProcessError as e:
        if log_callback:
            log_callback(f"FFmpeg conversion failed: {str(e)}", "error")


# ----------------------------
# Video downloader
# ----------------------------
def download_video(url, path, hook=None, log_callback=None):
    ydl_opts = {
        'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'progress_hooks': [hook] if hook else [],
    }

    if log_callback:
        ydl_opts['logger'] = MyLogger(log_callback)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(info)

            # 🔸 Auto-convert Opus → MP3 after download
            convert_opus_to_mp3(video_file, log_callback)

            return video_file  # optional: return final path

    except Exception as e:
        if log_callback:
            log_callback(f"Error: {str(e)}", "error")
        else:
            print("Error:", e)
