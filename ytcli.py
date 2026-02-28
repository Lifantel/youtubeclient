import sys
import subprocess
import shutil
import yt_dlp

def check_dependencies():
    if not shutil.which("mpv"):
        print("HATA: mpv bulunamadı. (pkg install mpv)")
        sys.exit(1)
    if not shutil.which("yt-dlp"):
        print("HATA: yt-dlp bulunamadı. (pkg install yt-dlp)")
        sys.exit(1)

def search_youtube(query, max_results=5):
    print(f"\n🔍 '{query}' aranıyor...\n")
    
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "default_search": "ytsearch",
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(
                f"ytsearch{max_results}:{query}",
                download=False
            )
            return info.get("entries", [])
        except Exception as e:
            print(f"Arama hatası: {e}")
            return []

def play_video(url, audio_only=False):
    print(f"\n▶️ Oynatılıyor: {url}\n")
    
    cmd = [
        "mpv",
        "--cache=yes",
        "--demuxer-readahead-secs=20",
        

        "--ytdl-format=best/bestaudio/bestvideo+bestaudio",
        
    
        "--ytdl-raw-options=extractor-args=youtube:player_client=android",
        
        url
    ]
    
    if audio_only:
        cmd.insert(1, "--no-video")
        
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        pass

def main():
    check_dependencies()
    
    print("=== Python YouTube Konsol Oynatıcısı (Android) ===")
    print("Çıkmak için 'q' yaz.\n")
    
    while True:
        try:
            user_input = input("[?] Arama terimi veya URL girin: ")
            
            if not user_input:
                continue
                
            if user_input.lower() == "q":
                print("Çıkış yapılıyor...")
                break
                
      
            if user_input.startswith("http"):
                mode = input("Sadece ses mi? (e/h): ").lower()
                play_video(user_input, audio_only=(mode == "e"))
                continue
                
            
            results = search_youtube(user_input)
            
            if not results:
                print("Sonuç bulunamadı.")
                continue
                
            print("\n--- Arama Sonuçları ---")
            for i, entry in enumerate(results, start=1):
                title = entry.get("title", "Bilinmeyen Başlık")
                uploader = entry.get("uploader", "Bilinmeyen Kanal")
                print(f"{i}. {title} ({uploader})")
                
            selection = input("\n[#] Oynatılacak numara (c iptal): ")
            
            if selection.lower() == "c":
                continue
                
            if selection.isdigit():
                idx = int(selection) - 1
                if 0 <= idx < len(results):
                    video_id = results[idx].get("id")
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    mode = input("Sadece ses mi? (e/h): ").lower()
                    play_video(video_url, audio_only=(mode == "e"))
                else:
                    print("Geçersiz seçim.")
            else:
                print("Geçersiz giriş.")
                
        except KeyboardInterrupt:
            print("\nÇıkış yapılıyor...")
            break

# --------------------------
if __name__ == "__main__":
    main()
