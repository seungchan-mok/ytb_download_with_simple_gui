import tkinter as tk
from tkinter import messagebox
from yt_dlp import YoutubeDL
import sys, re
from typing import List
import threading
import os

MAX_THREADS = max(1, min(os.cpu_count(), 8))
thread_semaphore = threading.Semaphore(MAX_THREADS)
download_threads = []
progress_lock = threading.Lock()
completed_downloads = 0
failed_downloads = []

def extract_urls(playlist_url: str) -> List[str]:
    ydl_opts = {"extract_flat": True, "quiet": True, "skip_download": True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
    urls = []
    for e in (info.get("entries") or []):
        u = e.get("webpage_url") or e.get("url") or e.get("id")
        if not u:
            continue
        if len(u) == 11 and re.fullmatch(r"[A-Za-z0-9_-]{11}", u):
            urls.append(f"https://www.youtube.com/watch?v={u}")
        elif u.startswith("http"):
            urls.append(u)
        else:
            urls.append(f"https://www.youtube.com/watch?v={e.get('id', u)}")
    return urls

def download(url: str, format: str):
    thread_semaphore.acquire()
    if format == "mp3":
        params = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }],
            "outtmpl": "%(title)s.%(ext)s",
            "quiet": True, # Suppress console output for threaded downloads
            "no_warnings": True, # Suppress warnings
        }
    else:  # mp4
        params = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
            "outtmpl": "%(title)s.%(ext)s",
            "merge_output_format": "mp4",
            "quiet": True, # Suppress console output for threaded downloads
            "no_warnings": True, # Suppress warnings
        }

    try:
        with YoutubeDL(params) as ydl:
            ydl.download([url])
    except Exception as e:
        with progress_lock:
            global failed_downloads
            failed_downloads.append(url)
        print(f"Download failed for {url}: {e}")
    finally:
        with progress_lock:
            global completed_downloads
            completed_downloads += 1
        thread_semaphore.release()

def check_threads(total_urls):
    global completed_downloads
    global failed_downloads
    
    if completed_downloads < total_urls:
        status_label.config(text=f"{total_urls}개 중 {completed_downloads}개 다운로드 완료...")
        root.after(100, lambda: check_threads(total_urls))
    else:
        if not failed_downloads:
            messagebox.showinfo("완료", f"{total_urls}개의 파일 다운로드가 완료되었습니다!")
            status_label.config(text="다운로드 완료!")
        else:
            fail_count = len(failed_downloads)
            fail_urls = "\n".join(failed_downloads)
            messagebox.showwarning("부분 실패", f"{total_urls}개 중 {fail_count}개의 파일 다운로드에 실패했습니다.\n\n실패한 파일:\n{fail_urls}")
            status_label.config(text=f"다운로드 실패: {fail_count}개")
        
        download_btn.config(state=tk.NORMAL)
        url_entry.config(state=tk.NORMAL)

def download_media():
    youtube_url = url_entry.get().strip()
    if not youtube_url:
        messagebox.showerror("에러", "URL을 입력해주세요!")
        return
    
    download_btn.config(state=tk.DISABLED)
    url_entry.config(state=tk.DISABLED)
    status_label.config(text="다운로드 시작...")

    if "playlist" in youtube_url:
        urls = extract_urls(youtube_url)
    else:
        urls = [youtube_url]

    global completed_downloads
    completed_downloads = 0
    global failed_downloads
    failed_downloads = []

    for url in urls:
        thread = threading.Thread(target=download, args=(url, format_var.get()))
        download_threads.append(thread)
        thread.start()
    
    check_threads(len(urls))

# Tkinter UI
root = tk.Tk()
root.title("YouTube 다운로드")

tk.Label(root, text="YouTube URL:").pack(padx=10, pady=5)
url_string = tk.StringVar(value="재생목록 또는 동영상 URL을 입력하세요")
url_entry = tk.Entry(root, width=50, textvariable=url_string)
url_entry.pack(padx=10, pady=5)

# 포맷 선택
format_var = tk.StringVar(value="mp3")
tk.Label(root, text="다운로드 형식:").pack()
tk.Radiobutton(root, text="MP3", variable=format_var, value="mp3").pack()
tk.Radiobutton(root, text="MP4", variable=format_var, value="mp4").pack()

download_btn = tk.Button(root, text="다운로드", command=download_media)
download_btn.pack(padx=10, pady=10)

status_label = tk.Label(root, text="준비됨", relief=tk.SUNKEN, bd=1, anchor="w")
status_label.pack(fill=tk.X, padx=10, pady=5)

root.mainloop()
