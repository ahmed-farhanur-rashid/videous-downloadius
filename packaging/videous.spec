# PyInstaller spec: one-file binary, no installer, no external deps at runtime.
# Build per OS: `pyinstaller packaging/videous.spec` on each platform natively
# (PyInstaller does not cross-compile).
import sys
from pathlib import Path

block_cipher = None
root = Path(__file__).resolve().parent.parent

# ponytail: FFmpeg must be dropped at packaging/ffmpeg/<os>/ before building,
# see packaging/README.md. Bundled via datas so no separate install needed.
if sys.platform == "win32":
    ffmpeg_bin = [(str(root / "packaging/ffmpeg/win/ffmpeg.exe"), ".")]
    icon = str(root / "assets/icon.ico")
elif sys.platform == "darwin":
    ffmpeg_bin = [(str(root / "packaging/ffmpeg/mac/ffmpeg"), ".")]
    icon = str(root / "assets/icon.icns")
else:
    ffmpeg_bin = [(str(root / "packaging/ffmpeg/linux/ffmpeg"), ".")]
    icon = None  # linux binaries don't embed an icon this way

a = Analysis(
    [str(root / "src/app.py")],
    pathex=[str(root / "src")],
    binaries=ffmpeg_bin,
    datas=[],
    hiddenimports=["yt_dlp"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
    name="VideousDownloadius",
    onefile=True,
    console=False,
    icon=icon,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="Videous Downloadius.app",
        icon=icon,
        bundle_identifier="com.videous.downloadius",
    )
