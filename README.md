# Videous Downloadius

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()
[![Built with yt-dlp](https://img.shields.io/badge/built%20with-yt%20dlp-red.svg)](https://github.com/yt-dlp/yt-dlp)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://doc.qt.io/qtforpython-6/)

A universal video downloader with a native desktop UI. Paste a URL, pick a quality, download — no terminal required.

Built on [yt-dlp](https://github.com/yt-dlp/yt-dlp) (1000+ supported sites) with a PySide6 GUI on top.

## Download

Grab the binary for your OS from the [Releases](../../releases) page — no install, no Python, no FFmpeg setup.

| OS | File |
|---|---|
| Windows | `VideousDownloadius-windows.exe` |
| macOS | `VideousDownloadius-mac.zip` → unzip → run the `.app` |
| Linux | `VideousDownloadius-linux` → `chmod +x` → run |

## From source

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/app.py
```

## Features

- Download from YouTube, Reddit, Twitter/X, and hundreds of other sites
- Quality selection: Best, 1080p, 720p, 480p, or audio-only
- Dark / light / system-adaptive theme
- Live pipeline view (fetch → convert → save) instead of a generic spinner

## Building

See [`packaging/README.md`](packaging/README.md). CI (`.github/workflows/build.yml`) builds all three OS binaries automatically on release.

## License

[MIT](LICENSE)
