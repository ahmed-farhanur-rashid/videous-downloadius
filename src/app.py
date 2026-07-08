"""Universal Video Downloader - thin GUI over yt-dlp.

yt-dlp already handles site support (YouTube/Reddit/Twitter/1000+ others),
format/quality selection, and audio+video merging. No reason to reimplement
any of that with pytube/selenium/praw/moviepy/bs4.
"""
import sys
import threading
import time
from pathlib import Path

import yt_dlp
from PySide6.QtCore import Signal, QObject, QSettings
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QComboBox, QLabel, QFileDialog, QMessageBox,
    QDialog, QListWidget, QSpinBox, QFormLayout, QDialogButtonBox,
)

from theme import build_qss, tokens_for
from pipeline_widget import PipelineStrip

DEFAULT_DOWNLOAD_DIR = str(Path.home() / "Downloads")

VIDEO_QUALITIES = {
    "Best": "bestvideo+bestaudio/best",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
}

# kbps=None means "don't force a bitrate" - grab the best source audio
# stream as-is (faster, lossless if source already matches). A specific
# kbps forces an ffmpeg transcode to that target via postprocessor.
AUDIO_QUALITIES = {
    "Best (source)": None,
    "320 kbps": 320,
    "192 kbps": 192,
    "128 kbps": 128,
}

MODES = ["Video", "Audio only"]
THEMES = ["dark", "light", "system"]

# yt-dlp's own browser-cookie readers - covers the login-wall sites (e.g.
# Instagram) without us touching a cookie store ourselves. "None" is default.
COOKIE_SOURCES = ["None", "Chrome", "Firefox", "Edge", "Brave", "Safari", "Custom file..."]

# Concurrent fragment downloads only speed up HLS/DASH (fragmented) streams;
# progressive downloads stay single-stream regardless. Capped at 8 - higher
# risks throttling/blocks from a single IP.
CONCURRENCY_OPTIONS = [1, 2, 4, 8]


class Signals(QObject):
    stage = Signal(int, float)      # active_stage, progress 0..1
    finished = Signal(bool, str)    # success, message


class DownloaderWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal Video Downloader")
        self.resize(600, 420)
        self.setMinimumSize(600, 420)
        self.setMaximumWidth(900)  # ponytail: fixed cap stops QMessageBox long text from stretching the window
        self.settings = QSettings("videous", "downloadius")
        self.download_dir = self.settings.value("download_dir", DEFAULT_DOWNLOAD_DIR)
        self.retry_count = int(self.settings.value("retry_count", 2))
        self.cookie_source = self.settings.value("cookie_source", "None")
        self.cookie_file = self.settings.value("cookie_file", "")
        self.theme_name = self.settings.value("theme", "system")

        self.signals = Signals()
        self.signals.stage.connect(self._on_stage)
        self.signals.finished.connect(self._on_finished)

        self._build_ui()
        self._apply_theme()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        header_row = QHBoxLayout()
        header_row.setSpacing(12)
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        eyebrow = QLabel("VIDEOUS DOWNLOADIUS")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("Universal Video Downloader")
        title.setObjectName("title")
        title_col.addWidget(eyebrow)
        title_col.addWidget(title)
        header_row.addLayout(title_col)
        header_row.addStretch()
        history_btn = QPushButton("History")
        history_btn.setObjectName("ghost")
        history_btn.setFixedHeight(30)
        history_btn.clicked.connect(self._show_history)
        header_row.addWidget(history_btn)
        settings_btn = QPushButton("Settings")
        settings_btn.setObjectName("ghost")
        settings_btn.setFixedHeight(30)
        settings_btn.clicked.connect(self._show_settings)
        header_row.addWidget(settings_btn)
        self.theme_btn = QPushButton(self._theme_label())
        self.theme_btn.setObjectName("ghost")
        self.theme_btn.setFixedHeight(30)
        self.theme_btn.clicked.connect(self._cycle_theme)
        header_row.addWidget(self.theme_btn)
        layout.addLayout(header_row)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste a video URL...")
        layout.addWidget(self.url_input)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(10)
        self.mode_box = QComboBox()
        self.mode_box.addItems(MODES)
        self.mode_box.currentTextChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self.mode_box, 1)

        self.quality_box = QComboBox()
        mode_row.addWidget(self.quality_box, 1)

        self.concurrency_box = QComboBox()
        self.concurrency_box.addItems([f"{n}x" for n in CONCURRENCY_OPTIONS])
        self.concurrency_box.setCurrentIndex(1)  # default 2x - a safe speed bump
        self.concurrency_box.setToolTip(
            "Concurrent fragment downloads. Only helps on HLS/DASH streams.\n"
            "Higher values risk throttling from the source site."
        )
        mode_row.addWidget(self.concurrency_box, 1)
        layout.addLayout(mode_row)
        self._on_mode_changed(MODES[0])

        row = QHBoxLayout()
        row.setSpacing(10)
        self.dir_label = QLabel(self._short_dir())
        self.dir_label.setObjectName("dirlabel")
        dir_btn = QPushButton("Folder...")
        dir_btn.setObjectName("ghost")
        dir_btn.setFixedHeight(34)
        dir_btn.clicked.connect(self._choose_dir)
        row.addWidget(self.dir_label, 2)
        row.addWidget(dir_btn)
        layout.addLayout(row)

        self.download_btn = QPushButton("Download")
        self.download_btn.setFixedHeight(40)
        self.download_btn.clicked.connect(self._start_download)
        layout.addWidget(self.download_btn)

        layout.addSpacing(4)
        self.pipeline = PipelineStrip(tokens_for(self.theme_name))
        layout.addWidget(self.pipeline)

        self.status_label = QLabel("Ready.")
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)

    def _on_mode_changed(self, mode):
        self.quality_box.clear()
        if mode == "Audio only":
            self.quality_box.addItems(AUDIO_QUALITIES.keys())
        else:
            self.quality_box.addItems(VIDEO_QUALITIES.keys())

    def _short_dir(self):
        d = self.download_dir
        return d if len(d) < 40 else "..." + d[-37:]

    def _theme_label(self):
        return {"dark": "◐ Dark", "light": "◑ Light", "system": "◒ System"}[self.theme_name]

    def _cycle_theme(self):
        idx = THEMES.index(self.theme_name)
        self.theme_name = THEMES[(idx + 1) % len(THEMES)]
        self.settings.setValue("theme", self.theme_name)
        self.theme_btn.setText(self._theme_label())
        self._apply_theme()

    def _apply_theme(self):
        self.setStyleSheet(build_qss(self.theme_name))
        self.pipeline.set_tokens(tokens_for(self.theme_name))

    def _choose_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Choose download folder", self.download_dir)
        if d:
            self.download_dir = d
            self.settings.setValue("download_dir", d)
            self.dir_label.setText(self._short_dir())

    def _show_settings(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Settings")
        form = QFormLayout(dlg)

        retry_spin = QSpinBox()
        retry_spin.setRange(0, 10)
        retry_spin.setValue(self.retry_count)
        form.addRow("Auto-retry attempts:", retry_spin)

        cookie_box = QComboBox()
        cookie_box.addItems(COOKIE_SOURCES)
        cookie_box.setCurrentText(self.cookie_source)
        form.addRow("Cookies (for login-walled sites):", cookie_box)

        file_row = QHBoxLayout()
        file_label = QLabel(Path(self.cookie_file).name if self.cookie_file else "(none chosen)")
        file_btn = QPushButton("Choose file...")

        def pick_cookie_file():
            f, _ = QFileDialog.getOpenFileName(dlg, "Choose cookies.txt", "", "Text files (*.txt)")
            if f:
                file_label.setText(Path(f).name)
                file_btn.setProperty("chosen_path", f)

        file_btn.clicked.connect(pick_cookie_file)
        file_btn.setProperty("chosen_path", self.cookie_file)
        file_row.addWidget(file_label, 1)
        file_row.addWidget(file_btn)
        form.addRow("Cookie file:", file_row)

        clear_btn = QPushButton("Clear cookies")
        clear_btn.clicked.connect(lambda: cookie_box.setCurrentText("None"))
        form.addRow(clear_btn)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)

        if dlg.exec() == QDialog.Accepted:
            self.retry_count = retry_spin.value()
            self.settings.setValue("retry_count", self.retry_count)
            self.cookie_source = cookie_box.currentText()
            self.settings.setValue("cookie_source", self.cookie_source)
            if self.cookie_source == "Custom file...":
                self.cookie_file = file_btn.property("chosen_path") or ""
                self.settings.setValue("cookie_file", self.cookie_file)

    def _show_history(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Download history")
        dlg.resize(500, 300)
        layout = QVBoxLayout(dlg)
        list_widget = QListWidget()
        list_widget.addItems(reversed(self.settings.value("history", [])))
        layout.addWidget(list_widget)
        clear_btn = QPushButton("Clear history")
        clear_btn.clicked.connect(lambda: (self.settings.remove("history"), list_widget.clear()))
        layout.addWidget(clear_btn)
        dlg.exec()

    def _add_to_history(self, url, success):
        history = self.settings.value("history", [])
        stamp = time.strftime("%Y-%m-%d %H:%M")
        status = "OK" if success else "FAILED"
        history.append(f"[{stamp}] {status}  {url}")
        self.settings.setValue("history", history[-200:])  # ponytail: flat list cap, add DB if history needs search/filter later

    def _start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Missing URL", "Enter a video URL first.")
            return
        self.download_btn.setEnabled(False)
        self.status_label.setProperty("error", False)
        self.status_label.setText("Starting...")
        self.pipeline.set_state(0, 0.0)

        is_audio = self.mode_box.currentText() == "Audio only"
        quality_choice = self.quality_box.currentText()
        concurrency = CONCURRENCY_OPTIONS[self.concurrency_box.currentIndex()]
        threading.Thread(
            target=self._run_download,
            args=(url, is_audio, quality_choice, concurrency),
            daemon=True,
        ).start()

    def _run_download(self, url, is_audio, quality_choice, concurrency):
        def hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                pct = (d["downloaded_bytes"] / total) if total else 0.0
                self.signals.stage.emit(0, pct)  # stage 0 = FETCH
            elif d["status"] == "finished":
                self.signals.stage.emit(1, 0.5)  # stage 1 = CONVERT (merge/transcode)

        ydl_opts = {
            # restrictfilenames strips characters like '|' ':' '?' from titles
            # (image 1's crash: a title with '|' produced an invalid Windows
            # path). Playlists already work via yt-dlp's own
            # %(playlist_index)s numbering, no template change needed there.
            "outtmpl": str(Path(self.download_dir) / "%(title)s.%(ext)s"),
            "restrictfilenames": True,
            "progress_hooks": [hook],
            "quiet": True,
            "no_warnings": True,
            # Resume partial downloads/fragments on retry instead of
            # restarting from scratch (yt-dlp's own default, set explicitly
            # so it can't silently change on us).
            "continuedl": True,
            "concurrent_fragment_downloads": concurrency,
        }

        if self.cookie_source == "Custom file..." and self.cookie_file:
            ydl_opts["cookiefile"] = self.cookie_file
        elif self.cookie_source not in ("None", "Custom file..."):
            ydl_opts["cookiesfrombrowser"] = (self.cookie_source.lower(),)

        if is_audio:
            kbps = AUDIO_QUALITIES[quality_choice]
            ydl_opts["format"] = "bestaudio/best"
            postprocessor = {"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}
            if kbps is not None:
                postprocessor["preferredquality"] = str(kbps)
            ydl_opts["postprocessors"] = [postprocessor]
        else:
            ydl_opts["format"] = VIDEO_QUALITIES[quality_choice]
            ydl_opts["merge_output_format"] = "mp4"

        attempts = self.retry_count + 1
        last_error = None
        for attempt in range(attempts):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                self.signals.stage.emit(3, 1.0)  # 3 = fully done (past SAVE)
                self.signals.finished.emit(True, "Download complete.")
                self._add_to_history(url, True)
                return
            except Exception as e:
                last_error = e
                if attempt < attempts - 1:
                    self.signals.stage.emit(0, 0.0)
                    time.sleep(2 ** attempt)  # ponytail: basic backoff, no jitter/cap needed at <=10 retries

        self.signals.finished.emit(False, str(last_error))
        self._add_to_history(url, False)

    def _on_stage(self, stage, progress):
        self.pipeline.set_state(stage, progress)
        label = ["Fetching...", "Converting...", "Saving...", "Done."][min(stage, 3)]
        self.status_label.setText(label)

    def _on_finished(self, success, message):
        self.download_btn.setEnabled(True)
        self.status_label.setText(message)
        self.status_label.setProperty("error", not success)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        if not success:
            self.pipeline.set_state(self.pipeline.active_stage, self.pipeline.stage_progress, errored=True)
            # yt-dlp errors can be paragraphs long (see Instagram cookie
            # error) - a QMessageBox sizes to its text and drags the whole
            # window with it. Truncate the dialog copy; full text stays in
            # status_label/history for anyone who needs it.
            short = message if len(message) < 300 else message[:300] + "…"
            QMessageBox.critical(self, "Download failed", short)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = DownloaderWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
