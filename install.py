import os
import sys
import subprocess
import requests
import zipfile
import tempfile
import shutil
import webbrowser

# ======================
# CONFIG
# ======================

APP_VERSION = "1.0"

VERSION_TXT_URL = "https://raw.githubusercontent.com/Lifantel/youtubeclient/refs/heads/main/version.txt"
GITHUB_RELEASE_URL = "https://github.com/Lifantel/youtubeclient"

YT_DLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
MPV_URL = "https://sourceforge.net/projects/mpv-player-windows/files/latest/download"

BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(__file__)

YT_DLP_PATH = os.path.join(BASE_DIR, "yt-dlp.exe")
MPV_DIR = os.path.join(BASE_DIR, "mpv")
MPV_EXE = os.path.join(MPV_DIR, "mpv.exe")

MAIN_EXE = os.path.join(BASE_DIR, "YouTubePlayer.exe")

# ======================
# HELPERS
# ======================

def download(url, out_path):
    r = requests.get(url, stream=True, timeout=15)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)

def get_remote_version():
    try:
        r = requests.get(VERSION_TXT_URL, timeout=10)
        return r.text.strip()
    except:
        return None

# ======================
# VERSION CHECK
# ======================

def check_app_version():
    remote = get_remote_version()
    if not remote:
        return

    if remote != APP_VERSION:
        print(f"Guncelleme var! Lokal: {APP_VERSION} | Remote: {remote}")
        webbrowser.open(GITHUB_RELEASE_URL)

# ======================
# yt-dlp
# ======================

def ensure_yt_dlp():
    if not os.path.exists(YT_DLP_PATH):
        print("yt-dlp yok, indiriliyor...")
        download(YT_DLP_URL, YT_DLP_PATH)
        return

    try:
        subprocess.run([YT_DLP_PATH, "-U"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        print("yt-dlp guncellenemedi, yeniden indiriliyor...")
        download(YT_DLP_URL, YT_DLP_PATH)

# ======================
# mpv
# ======================

def ensure_mpv():
    if os.path.exists(MPV_EXE):
        return

    print("mpv yok, indiriliyor...")
    tmp_zip = tempfile.mktemp(suffix=".zip")
    download(MPV_URL, tmp_zip)

    if os.path.exists(MPV_DIR):
        shutil.rmtree(MPV_DIR)

    os.makedirs(MPV_DIR, exist_ok=True)

    with zipfile.ZipFile(tmp_zip, "r") as z:
        z.extractall(MPV_DIR)

    os.remove(tmp_zip)

# ======================
# MAIN
# ======================

def main():
    check_app_version()
    ensure_yt_dlp()
    ensure_mpv()

    if os.path.exists(MAIN_EXE):
        subprocess.Popen([MAIN_EXE])

if __name__ == "__main__":
    main()
