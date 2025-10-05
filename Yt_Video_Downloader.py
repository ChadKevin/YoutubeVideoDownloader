import subprocess
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import threading
import Video_downloader_cmd as vdc
import os

APP_TITLE = "YouTube Video Downloader"
SAVE_FILE = "last_path.txt"
download_thread = None
stop_download = False  # Flag to cancel download

# ----------------------------
# Functions
# ----------------------------

def convert_opus_to_mp3(video_path):
    # Construct new file name
    base, ext = os.path.splitext(video_path)
    new_path = base + "_converted.mp4"  # You can keep mp4 extension
    try:
        # FFmpeg command: keep video stream, convert audio to mp3
        subprocess.run([
            "ffmpeg",
            "-i", video_path,
            "-c:v", "copy",       # copy video stream
            "-c:a", "mp3",        # convert audio to mp3
            "-y",                 # overwrite if exists
            new_path
        ], check=True)
        log_message(f"Converted audio to MP3: {new_path}", "success")
        # Optionally replace original file
        os.replace(new_path, video_path)
    except subprocess.CalledProcessError as e:
        log_message(f"FFmpeg conversion failed: {str(e)}", "error")
        
def select_path():
    selected_path = filedialog.askdirectory()
    if selected_path:
        path_var.set(selected_path)
        save_path(selected_path)

def save_path(path):
    with open(SAVE_FILE, "w") as f:
        f.write(path)

def load_path():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            path_var.set(f.read().strip())

def progress_hook(d):
    global stop_download
    if stop_download:
        raise Exception("Download cancelled by user.")

    if d['status'] == 'downloading':
        if d.get('total_bytes'):
            percent = d['downloaded_bytes'] / d['total_bytes'] * 100
        elif d.get('total_bytes_estimate'):
            percent = d['downloaded_bytes'] / d['total_bytes_estimate'] * 100
        else:
            percent = 0
        progress_var.set(int(percent))
        root.update_idletasks()

    elif d['status'] == 'finished':
        progress_var.set(100)
        log_message("Download finished!", "success")
        run_button.config(state=tk.NORMAL)
        cancel_button.config(state=tk.DISABLED)



def download_video():
    global stop_download
    stop_download = False
    video_url = url_var.get()
    download_path = path_var.get()
    progress_var.set(0)  # reset progress bar
    
    if video_url and download_path:
        log_message(f"Downloading: {video_url}", "download")
        try:
            vdc.download_video(video_url, download_path, progress_hook, log_message)
        except Exception as e:
            log_message(f"{str(e)}", "error")
        finally:
            run_button.config(state=tk.NORMAL)
            cancel_button.config(state=tk.DISABLED)
    else:
        log_message("Please enter a valid URL and select a download folder.", "error")
        run_button.config(state=tk.NORMAL)
        cancel_button.config(state=tk.DISABLED)
    

def start_thread():
    run_button.config(state=tk.DISABLED)
    cancel_button.config(state=tk.NORMAL)
    threading.Thread(target=download_video, daemon=True).start()

def cancel_download_func():
    global stop_download
    stop_download = True
    log_message("Download cancelled.", "error")
    run_button.config(state=tk.NORMAL)
    cancel_button.config(state=tk.DISABLED)

def log_message(msg, tag="info"):
    console.configure(state=tk.NORMAL)
    console.insert(tk.END, msg + "\n", tag)
    console.configure(state=tk.DISABLED)
    console.see(tk.END)

def clear_console():
    console.configure(state=tk.NORMAL)
    console.delete("1.0", tk.END)
    console.configure(state=tk.DISABLED)

def on_closing():
    cancel_download_func()
    root.destroy()

# ----------------------------
# UI Setup
# ----------------------------
root = tk.Tk()
root.title(APP_TITLE)
root.state('zoomed')  # maximized window
root.option_add("*Font", "SegoeUI 10")

# --- Title ---
title_label = ttk.Label(root, text=APP_TITLE, font=("SegoeUI", 18, "bold"))
title_label.pack(pady=10)

# --- URL Section ---
frame_url = ttk.LabelFrame(root, text="YouTube URL")
frame_url.pack(fill="x", padx=10, pady=5)

url_var = tk.StringVar()
url_entry = ttk.Entry(frame_url, textvariable=url_var, width=70)
url_entry.pack(side="left", padx=5, pady=5)

# --- Path Section ---
frame_path = ttk.LabelFrame(root, text="Download Folder")
frame_path.pack(fill="x", padx=10, pady=5)

path_var = tk.StringVar()
path_entry = ttk.Entry(frame_path, textvariable=path_var, width=70)
path_entry.pack(side="left", padx=5, pady=5)

browse_button = ttk.Button(frame_path, text="Browse", command=select_path)
browse_button.pack(side="left", padx=5, pady=5)

# Load last saved path
load_path()

# --- Console Section ---
frame_console = ttk.LabelFrame(root, text="Console Output")
frame_console.pack(fill="both", expand=True, padx=10, pady=5)

console = scrolledtext.ScrolledText(frame_console, height=15, state=tk.DISABLED, bg="black", fg="white")
console.pack(fill="both", expand=True, padx=5, pady=5)

console.tag_config("info", foreground="white")
console.tag_config("error", foreground="red")
console.tag_config("success", foreground="green")
console.tag_config("download", foreground="cyan")

clear_console_button = ttk.Button(frame_console, text="Clear Console", command=clear_console)
clear_console_button.pack(pady=5)

# --- Progress + Controls ---
frame_controls = ttk.Frame(root)
frame_controls.pack(fill="x", padx=10, pady=10)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(frame_controls, orient="horizontal", length=500, mode="determinate", variable=progress_var, maximum=100)
progress_bar.pack(side="left", padx=5, pady=5)

run_button = ttk.Button(frame_controls, text="Download", command=start_thread)
run_button.pack(side="left", padx=5)

cancel_button = ttk.Button(frame_controls, text="Cancel", command=cancel_download_func, state=tk.DISABLED)
cancel_button.pack(side="left", padx=5)

# --- Window events ---
root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()