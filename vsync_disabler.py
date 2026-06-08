import os
import subprocess
import tempfile
import threading
import time
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem as item

MINECRAFT_SUBPATH = os.path.join("games", "com.mojang", "minecraftpe", "options.txt")

def get_users_dir():
    appdata = os.environ.get("APPDATA") or os.path.join(
        os.environ.get("USERPROFILE", "C:\\Users\\Default"), "AppData", "Roaming"
    )
    return os.path.join(appdata, "Minecraft Bedrock", "Users")

def is_minecraft_running():
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        tmp.close()
        with open(tmp.name, "w") as out:
            subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Minecraft.Windows.exe", "/NH"],
                stdout=out, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW, timeout=10
            )
        with open(tmp.name, "r") as f:
            output = f.read()
        os.unlink(tmp.name)
        return "Minecraft.Windows.exe" in output
    except Exception:
        return False

def patch_all():
    users_dir = get_users_dir()
    if not os.path.isdir(users_dir):
        return 0, 0
    patched = 0
    already = 0
    folders = [f for f in os.listdir(users_dir) if os.path.isdir(os.path.join(users_dir, f))]
    for folder in folders:
        path = os.path.join(users_dir, folder, MINECRAFT_SUBPATH)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if "gfx_vsync:1" in content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content.replace("gfx_vsync:1", "gfx_vsync:0"))
                patched += 1
            elif "gfx_vsync:0" in content:
                already += 1
        except Exception:
            pass
    return patched, already

def make_icon(color):
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, size - 2, size - 2], fill=color)
    # Draw a V shape
    mid = size // 2
    d.line([(14, 18), (mid, 46)], fill="white", width=7)
    d.line([(mid, 46), (50, 18)], fill="white", width=7)
    return img

def main():
    was_running = False
    mc_running = False

    def monitor(icon):
        nonlocal was_running, mc_running
        time.sleep(1)
        while icon.visible or True:
            try:
                running = is_minecraft_running()
                mc_running = running

                if running:
                    icon.icon = make_icon("#e67e22")
                    icon.title = "SLOW VSync Disabler — Minecraft is running"
                else:
                    icon.icon = make_icon("#27ae60")
                    icon.title = "SLOW VSync Disabler — Watching for Minecraft"

                if was_running and not running:
                    # Minecraft just closed — patch immediately
                    patched, already = patch_all()
                    if patched > 0:
                        icon.notify(
                            f"VSync disabled for {patched} profile(s).",
                            "SLOW VSync Disabler"
                        )
                    else:
                        icon.notify(
                            "All profiles already had VSync off.",
                            "SLOW VSync Disabler"
                        )

                was_running = running
            except Exception:
                pass
            time.sleep(2)

    def on_patch_now(icon, menu_item):
        patched, already = patch_all()
        if patched > 0:
            icon.notify(f"Patched {patched} profile(s). ({already} already off)", "SLOW VSync Disabler")
        else:
            icon.notify(f"All {already} profile(s) already had VSync off.", "SLOW VSync Disabler")

    def on_exit(icon, menu_item):
        icon.stop()

    status_item = item(
        lambda text: "Minecraft: Running" if mc_running else "Minecraft: Not running",
        lambda: None,
        enabled=False
    )

    tray = pystray.Icon(
        "SLOW VSync Disabler",
        make_icon("#27ae60"),
        "SLOW VSync Disabler — Watching for Minecraft",
        menu=pystray.Menu(
            item("SLOW VSync Disabler", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            status_item,
            pystray.Menu.SEPARATOR,
            item("Patch Now", on_patch_now),
            pystray.Menu.SEPARATOR,
            item("Exit", on_exit),
        )
    )

    threading.Thread(target=monitor, args=(tray,), daemon=True).start()
    tray.run()

if __name__ == "__main__":
    main()
