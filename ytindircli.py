import subprocess

def download(url, choice):
    if choice == "mp4":
        cmd = [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]",
            url
        ]

    elif choice == "mp3":
        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            url
        ]
    else:
        print("Hatalı seçim. Sadece mp3 veya mp4 yaz.")
        return

    subprocess.run(cmd)

# ----------- MAIN -----------
url = input("URL gir: ").strip()
choice = input("mp3 mi mp4 mü?: ").strip().lower()

download(url, choice)
