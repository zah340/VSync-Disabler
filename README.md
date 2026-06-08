# SLOW VSync Disabler

A small Windows utility that disables VSync for every Minecraft Bedrock user profile on the PC.

## What it does

- Closes `Minecraft.Windows.exe` if it is running
- Scans every profile under `%APPDATA%\Minecraft Bedrock\Users`
- Sets `gfx_vsync:0` in each profile's `options.txt`
- Shows a live progress bar and per-user log

## Usage

Download `SLOWVSyncDisabler.exe` and run it. No install required.

Click **Disable VSync** and the tool will handle the rest.

## Building from source

Requires Python 3.x and PyInstaller.

```
pip install pyinstaller
python -m PyInstaller --onefile --windowed --name "SLOWVSyncDisabler" vsync_disabler.py
```

The exe will be in the `dist/` folder.

## License

MIT — see [LICENSE](LICENSE).
