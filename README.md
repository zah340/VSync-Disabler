# SLOW VSync Disabler

A lightweight Windows tray app that automatically disables VSync for every Minecraft Bedrock user profile on the PC.

## How it works

- Runs silently in the system tray (bottom right near the clock)
- Watches for Minecraft to close in the background
- The moment Minecraft closes, it patches `gfx_vsync:0` in every user profile automatically
- Sends a Windows notification when done

## Usage

1. Download `SLOWVSyncDisabler.exe` and run it
2. It will appear as a **green icon** in your system tray
3. That's it just play Minecraft and VSync will be disabled automatically every time you close the game

**Right-click the tray icon for options:**
- `Patch Now` — manually patch all profiles immediately
- `Exit` — close the app

## Building from source

Requires Python 3.x, PyInstaller, pystray, and Pillow.

```
pip install pyinstaller pystray pillow
python -m PyInstaller --onefile --windowed --name "SLOWVSyncDisabler" --hidden-import "pystray._win32" vsync_disabler.py
```

The exe will be in the `dist/` folder.

## License

MIT — see [LICENSE](LICENSE).
