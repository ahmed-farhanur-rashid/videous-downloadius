# Packaging

One PyInstaller spec (`videous.spec`), built natively per OS — PyInstaller
doesn't cross-compile, so Windows/macOS/Linux binaries each require running
on that OS (GitHub Actions does this automatically, see `.github/workflows/`).

Output is a single executable. No installer, no separate FFmpeg or Python
install required by the end user.

## One-time: get FFmpeg binaries

Download a static build and drop it here (not committed to git — see
`.gitignore` — CI downloads these fresh on every build):

```
packaging/ffmpeg/win/ffmpeg.exe      https://www.gyan.dev/ffmpeg/builds/ (release essentials, static)
packaging/ffmpeg/mac/ffmpeg          https://evermeet.cx/ffmpeg/ (static)
packaging/ffmpeg/linux/ffmpeg        https://johnvansickle.com/ffmpeg/ (static build)
```

## Build locally

```bash
pip install -r ../requirements.txt pyinstaller
pyinstaller videous.spec --distpath ../dist --workpath ../build
```

Output lands in `dist/`:
- Windows: `VideousDownloadius.exe`
- macOS: `Videous Downloadius.app`
- Linux: `VideousDownloadius` (make executable: `chmod +x`)

## Icons

Drop `assets/icon.ico` (Windows) and `assets/icon.icns` (macOS) before
building, or the spec falls back to no icon. Linux binaries don't carry an
icon this way — pair with a `.desktop` file if you want one in app menus.
