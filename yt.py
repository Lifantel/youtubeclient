import sys
import json
import os
import shutil
import subprocess
import datetime
import tempfile
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QPushButton, QListWidget, 
                             QListWidgetItem, QLabel, QTabWidget, QMessageBox, 
                             QCheckBox, QFrame, QComboBox, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette
import yt_dlp

# --- Sabitler ve Ayarlar ---
HISTORY_FILE = "history.json"

class HistoryManager:
    """Geçmişi yönetmek için sınıf"""
    @staticmethod
    def load():
        if not os.path.exists(HISTORY_FILE):
            return []
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []

    @staticmethod
    def add(video_data):
        history = HistoryManager.load()
        history = [v for v in history if v['id'] != video_data['id']]
        
        entry = {
            "id": video_data['id'],
            "title": video_data['title'],
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "url": f"https://www.youtube.com/watch?v={video_data['id']}"
        }
        history.insert(0, entry)
        history = history[:50]
        
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

class SearchThread(QThread):
    """Arayüzün donmaması için aramayı arka planda yapar"""
    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        ydl_opts = {
            "quiet": True,
            "extract_flat": True,
            "noplaylist": True,
            "ignoreerrors": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"],
                    "skip": ["hls", "dash"]
                }
            }
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if self.query.startswith("http"):
                    info = ydl.extract_info(self.query, download=False)
                    data = [info] if info else []
                else:
                    info = ydl.extract_info(f"ytsearch10:{self.query}", download=False)
                    data = info.get("entries", [])
                
                self.results_ready.emit(data)
        except Exception as e:
            self.error_occurred.emit(str(e))


class PlayThread(QThread):
    """Video oynatma için arka plan thread'i - yt-dlp subprocess kullanarak"""
    error_occurred = pyqtSignal(str)
    success = pyqtSignal()

    def __init__(self, url, audio_only, quality):
        super().__init__()
        self.url = url
        self.audio_only = audio_only
        self.quality = quality

    def run(self):
        try:
            # MPV komutunu oluştur
            cmd = ["mpv", "--force-window=immediate"]
            
            # Format ayarları - kaliteye göre
            if self.audio_only:
                cmd.extend([
                    "--no-video",
                    "--ytdl-format=bestaudio[ext=m4a]/bestaudio/best"
                ])
            else:
                # Kalite seçimine göre format
                if self.quality == "1080p":
                    format_str = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best"
                elif self.quality == "720p":
                    format_str = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best"
                elif self.quality == "480p":
                    format_str = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best"
                else:  # "En İyi"
                    format_str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
                
                cmd.extend([
                    f"--ytdl-format={format_str}"
                ])
            
            # yt-dlp Android client kullanması için
            cmd.extend([
                "--script-opts=ytdl_hook-try_ytdl_first=yes",
                "--ytdl-raw-options=extractor-args=youtube:player_client=android",
                self.url
            ])
            
            # MPV'yi başlat
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            
            # Kısa bir süre bekle - başarılı başladıysa success signal gönder
            import time
            time.sleep(2)
            
            if process.poll() is None:  # Hala çalışıyorsa
                self.success.emit()
            else:
                stderr = process.stderr.read().decode('utf-8', errors='ignore')
                if stderr:
                    raise Exception(f"MPV hatası: {stderr[:500]}")
                else:
                    raise Exception("MPV beklenmedik şekilde kapandı")
                
        except Exception as e:
            self.error_occurred.emit(str(e))


class ModernPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Player - No Cookies Required")
        self.setGeometry(100, 100, 900, 650)
        
        # MPV Kontrolü
        if not shutil.which("mpv"):
            QMessageBox.critical(self, "Hata", "MPV bulunamadı! Lütfen sisteminize MPV yükleyin.")
            sys.exit(1)

        self.play_thread = None
        self.setup_ui()
        self.setup_theme()
        
        self.load_history_list()

    def setup_theme(self):
        """Koyu, modern bir tema uygular"""
        app = QApplication.instance()
        app.setStyle("Fusion")
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        app.setPalette(palette)

        self.setStyleSheet("""
            QLineEdit { padding: 8px; border-radius: 5px; border: 1px solid #5c5c5c; background: #2b2b2b; color: white; }
            QPushButton { padding: 8px 15px; border-radius: 5px; background-color: #0d6efd; color: white; font-weight: bold; }
            QPushButton:hover { background-color: #0b5ed7; }
            QListWidget { border: none; background-color: #2b2b2b; outline: none; }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #3d3d3d; }
            QListWidget::item:selected { background-color: #3d3d3d; }
            QTabWidget::pane { border: 1px solid #3d3d3d; }
            QTabBar::tab { background: #353535; color: white; padding: 10px 20px; }
            QTabBar::tab:selected { background: #2b2b2b; border-bottom: 2px solid #0d6efd; }
            QTextEdit { background-color: #2b2b2b; color: #aaa; border: 1px solid #3d3d3d; }
        """)

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Info label
        info_label = QLabel("🎵 Android Client kullanarak cookie'siz çalışır")
        info_label.setStyleSheet("color: #4CAF50; font-weight: bold; padding: 5px;")
        layout.addWidget(info_label)

        # --- Arama Bölümü ---
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("YouTube'da ara veya URL yapıştır...")
        self.search_input.returnPressed.connect(self.start_search)
        
        self.search_btn = QPushButton("🔍 Ara")
        self.search_btn.clicked.connect(self.start_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)

        # --- Orta Bölüm: Sekmeler ---
        self.tabs = QTabWidget()
        
        # Sekme 1: Sonuçlar
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.play_selected)
        self.tabs.addTab(self.results_list, "Arama Sonuçları")
        
        # Sekme 2: Geçmiş
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.play_history_item)
        self.tabs.addTab(self.history_list, "Geçmiş")
        
        # Sekme 3: Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        self.tabs.addTab(self.log_text, "Log")
        
        layout.addWidget(self.tabs)

        # --- Alt Bölüm: Kontroller ---
        controls_layout = QHBoxLayout()
        
        self.audio_only_check = QCheckBox("🎵 Sadece Ses")
        self.audio_only_check.setStyleSheet("color: white; font-size: 14px;")
        
        # Kalite seçici
        quality_label = QLabel("Kalite:")
        quality_label.setStyleSheet("color: white; margin-left: 15px;")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["En İyi", "1080p", "720p", "480p"])
        self.quality_combo.setCurrentText("1080p")
        self.quality_combo.setStyleSheet("min-width: 100px;")
        
        self.status_label = QLabel("Hazır")
        self.status_label.setStyleSheet("color: #aaaaaa;")

        self.play_btn = QPushButton("▶️ Oynat")
        self.play_btn.clicked.connect(self.play_selected)
        self.play_btn.setStyleSheet("background-color: #198754;")

        controls_layout.addWidget(self.audio_only_check)
        controls_layout.addWidget(quality_label)
        controls_layout.addWidget(self.quality_combo)
        controls_layout.addStretch()
        controls_layout.addWidget(self.status_label)
        controls_layout.addWidget(self.play_btn)
        
        layout.addLayout(controls_layout)

    def log(self, message):
        """Log mesajı ekle"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def start_search(self):
        query = self.search_input.text().strip()
        if not query:
            return

        self.log(f"Arama başlatılıyor: {query}")
        self.status_label.setText("Aranıyor...")
        self.search_btn.setEnabled(False)
        self.results_list.clear()

        self.worker = SearchThread(query)
        self.worker.results_ready.connect(self.display_results)
        self.worker.error_occurred.connect(self.search_error)
        self.worker.finished.connect(lambda: self.search_btn.setEnabled(True))
        self.worker.start()

    def display_results(self, results):
        if not results:
            self.status_label.setText("Sonuç bulunamadı.")
            self.log("Sonuç bulunamadı")
            return

        for video in results:
            if 'title' in video and 'id' in video:
                item = QListWidgetItem(f"{video['title']}")
                item.setData(Qt.ItemDataRole.UserRole, video)
                self.results_list.addItem(item)
        
        self.status_label.setText(f"{len(results)} sonuç bulundu.")
        self.log(f"{len(results)} sonuç bulundu")
        self.tabs.setCurrentIndex(0)

    def search_error(self, error_msg):
        self.status_label.setText("Arama hatası!")
        self.log(f"HATA: {error_msg}")
        QMessageBox.warning(self, "Arama Hatası", error_msg)

    def play_selected(self):
        if self.tabs.currentIndex() == 0:
            current_item = self.results_list.currentItem()
        else:
            current_item = self.history_list.currentItem()

        if not current_item:
            QMessageBox.information(self, "Bilgi", "Lütfen oynatmak için bir video seçin.")
            return

        video_data = current_item.data(Qt.ItemDataRole.UserRole)
        self.launch_mpv(video_data)

    def play_history_item(self):
        current_item = self.history_list.currentItem()
        if current_item:
            video_data = current_item.data(Qt.ItemDataRole.UserRole)
            self.launch_mpv(video_data)

    def launch_mpv(self, video_data):
        url = video_data.get('url')
        if not url:
            url = f"https://www.youtube.com/watch?v={video_data['id']}"
            video_data['url'] = url

        audio_mode = self.audio_only_check.isChecked()
        quality = self.quality_combo.currentText()
        
        self.log(f"Oynatılıyor: {video_data['title']} ({quality})")
        self.status_label.setText(f"Başlatılıyor...")
        self.play_btn.setEnabled(False)
        
        self.play_thread = PlayThread(url, audio_mode, quality)
        self.play_thread.success.connect(lambda: self.on_play_success(video_data))
        self.play_thread.error_occurred.connect(self.on_play_error)
        self.play_thread.finished.connect(lambda: self.play_btn.setEnabled(True))
        self.play_thread.start()

    def on_play_success(self, video_data):
        mode = "Ses" if self.audio_only_check.isChecked() else "Video"
        self.status_label.setText(f"▶️ Oynatılıyor ({mode})")
        self.log(f"✓ Başarıyla başlatıldı: {video_data['title']}")
        HistoryManager.add(video_data)
        self.load_history_list()

    def on_play_error(self, error_msg):
        self.status_label.setText("❌ Hata!")
        self.log(f"✗ HATA: {error_msg}")
        QMessageBox.critical(self, "Oynatma Hatası", f"Video oynatılamadı:\n{error_msg}")

    def load_history_list(self):
        self.history_list.clear()
        history = HistoryManager.load()
        for item_data in history:
            display_text = f"[{item_data['timestamp']}] {item_data['title']}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, item_data)
            self.history_list.addItem(item)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModernPlayer()
    window.show()
    sys.exit(app.exec())