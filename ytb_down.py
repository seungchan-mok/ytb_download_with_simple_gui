import tkinter as tk
from tkinter import messagebox
from yt_dlp import YoutubeDL
import sys, re
from typing import List

def extract_urls(playlist_url: str) -> List[str]:
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        # 플레이리스트일 때만 납작 추출 + 페이지네이션 수행
        "extract_flat": "in_playlist",
        # 범위를 크게 지정해서 첫 페이지만 먹고 끝나는 걸 회피
        "playlist_items": "1-100000",
        "ignoreerrors": True,
        # 필요하면 로그인 쿠키(비공개/연령제한 회피)
        # "cookiesfrombrowser": ("chrome",),  # 크롬 세션 사용
        # 또는 "cookiefile": "cookies.txt",
    }
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

def download(url, format, show_message=True):
    if format == "mp3":
        params = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }],
            "outtmpl": "%(title)s.%(ext)s",
        }
    else:  # mp4
        params = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
            "outtmpl": "%(title)s.%(ext)s",
            "merge_output_format": "mp4",
        }

    try:
        with YoutubeDL(params) as ydl:
            result = ydl.download([url])
        if show_message:
            messagebox.showinfo("완료", f"{format} 다운로드가 완료되었습니다!")
    except Exception as e:
        if show_message:
            messagebox.showerror("에러", f"다운로드 실패: {e}")

def download_media():
    youtube_url = url_entry.get().strip()
    if not youtube_url:
        messagebox.showerror("에러", "URL을 입력해주세요!")
        return
    
    
    if "playlist" in youtube_url:
        urls = extract_urls(youtube_url)
    else:
        urls = [youtube_url]
    messagebox.showinfo("정보", f"{len(urls)}개의 항목을 다운로드합니다.")
    for url in urls:
        download(url, format_var.get(), show_message=False)
    messagebox.showinfo("완료", f"{len(urls)}개의 파일 다운로드가 완료되었습니다!")
    


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

root.mainloop()
