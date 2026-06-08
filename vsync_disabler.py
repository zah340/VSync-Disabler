import os
import subprocess
import tempfile
import tkinter as tk
from tkinter import ttk
import threading
import time

MINECRAFT_SUBPATH = os.path.join("games", "com.mojang", "minecraftpe", "options.txt")

def get_users_dir():
    appdata = os.environ.get("APPDATA") or os.path.join(
        os.environ.get("USERPROFILE", "C:\\Users\\Default"), "AppData", "Roaming"
    )
    return os.path.join(appdata, "Minecraft Bedrock", "Users")

def set_readonly(path, readonly):
    import stat
    if readonly:
        os.chmod(path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
    else:
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)

def patch_options_file(path):
    # Ensure file is writable before we touch it
    set_readonly(path, False)

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if "gfx_vsync:1" in content:
        patched = content.replace("gfx_vsync:1", "gfx_vsync:0")
        with open(path, "w", encoding="utf-8") as f:
            f.write(patched)
        set_readonly(path, True)
        return "patched"

    if "gfx_vsync:0" in content:
        # Already correct — lock it so Minecraft can't reset it
        set_readonly(path, True)
        return "already_disabled"

    return "not_found"

def run_patch(log_text, progress_var, status_label, done_label, root):
    users_dir = get_users_dir()

    def log(msg):
        def _do():
            log_text.config(state="normal")
            log_text.insert("end", msg + "\n")
            log_text.see("end")
            log_text.config(state="disabled")
        root.after(0, _do)

    def set_status(msg):
        root.after(0, lambda: status_label.config(text=msg))

    def is_minecraft_running():
        try:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
            tmp.close()
            subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Minecraft.Windows.exe", "/NH"],
                stdout=open(tmp.name, "w"), stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW, timeout=10
            )
            with open(tmp.name, "r") as f:
                output = f.read()
            os.unlink(tmp.name)
            return "Minecraft.Windows.exe" in output
        except Exception:
            return False

    def kill_minecraft():
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "Minecraft.Windows.exe"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW, timeout=10
            )
        except Exception:
            pass

    try:
        if is_minecraft_running():
            log("Minecraft is running — closing it before patching...")
            set_status("Closing Minecraft...")
            kill_minecraft()
            time.sleep(2)
            log("Minecraft closed.\n")
        else:
            log("Minecraft is not running — patching files directly.\n")
    except Exception as e:
        log(f"WARNING: Could not check Minecraft status: {e}\nPatching anyway.\n")

    if not os.path.isdir(users_dir):
        log(f"ERROR: Directory not found:\n  {users_dir}")
        set_status("Failed — directory not found.")
        return

    folders = [f for f in os.listdir(users_dir) if os.path.isdir(os.path.join(users_dir, f))]
    total = len(folders)

    if total == 0:
        log("No user folders found.")
        set_status("Done — no users found.")
        return

    log(f"Found {total} user folder(s) in:\n  {users_dir}\n")

    patched_count = 0
    already_count = 0
    skipped_count = 0

    for i, folder in enumerate(folders, 1):
        options_path = os.path.join(users_dir, folder, MINECRAFT_SUBPATH)
        label = f"[{i}/{total}] {folder}"

        set_status(f"Processing {i} of {total}...")
        root.after(0, lambda v=i: progress_var.set(v))

        if not os.path.isfile(options_path):
            log(f"{label}\n  → options.txt not found, skipping.")
            skipped_count += 1
        else:
            result = patch_options_file(options_path)
            if result == "patched":
                log(f"{label}\n  → VSync disabled.")
                patched_count += 1
            elif result == "already_disabled":
                log(f"{label}\n  → Already disabled, locked to prevent reset.")
                already_count += 1
            elif result == "not_found":
                log(f"{label}\n  → gfx_vsync setting not found in file, skipping.")
                skipped_count += 1

        time.sleep(0.05)

    summary = (
        f"\n─── Summary ───────────────────────\n"
        f"  Total users:      {total}\n"
        f"  VSync disabled:   {patched_count}\n"
        f"  Already off:      {already_count}\n"
        f"  Skipped (no file):{skipped_count}\n"
        f"────────────────────────────────────"
    )
    log(summary)
    set_status(f"Done — {patched_count} patched, {already_count} already off, {skipped_count} skipped.")
    done_label.after(0, lambda: done_label.config(text="✔ All done!", fg="#4caf50"))

def build_gui():
    root = tk.Tk()
    root.title("SLOW VSync Disabler")
    root.geometry("560x480")
    root.resizable(False, False)
    root.configure(bg="#1e1e1e")

    tk.Label(root, text="SLOW VSync Disabler", font=("Segoe UI", 14, "bold"),
             bg="#1e1e1e", fg="#ffffff").pack(pady=(16, 4))

    status_label = tk.Label(root, text="Ready.", font=("Segoe UI", 9),
                             bg="#1e1e1e", fg="#cccccc")
    status_label.pack()

    users_dir = get_users_dir()
    try:
        folders = [f for f in os.listdir(users_dir) if os.path.isdir(os.path.join(users_dir, f))]
        total = len(folders)
    except FileNotFoundError:
        total = 0

    progress_var = tk.IntVar(value=0)
    progress = ttk.Progressbar(root, variable=progress_var, maximum=max(total, 1),
                                length=500, mode="determinate")
    progress.pack(pady=8)

    counter_frame = tk.Frame(root, bg="#1e1e1e")
    counter_frame.pack()
    tk.Label(counter_frame, text=f"Total users found: {total}", font=("Segoe UI", 9),
             bg="#1e1e1e", fg="#bbbbbb").pack()

    log_frame = tk.Frame(root, bg="#1e1e1e")
    log_frame.pack(padx=16, pady=8, fill="both", expand=True)

    scrollbar = tk.Scrollbar(log_frame)
    scrollbar.pack(side="right", fill="y")

    log_text = tk.Text(log_frame, height=12, font=("Consolas", 9),
                       bg="#121212", fg="#d4d4d4", insertbackground="white",
                       yscrollcommand=scrollbar.set, state="disabled", relief="flat")
    log_text.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=log_text.yview)

    done_label = tk.Label(root, text="", font=("Segoe UI", 10, "bold"),
                          bg="#1e1e1e", fg="#4caf50")
    done_label.pack(pady=(0, 4))

    def on_start():
        start_btn.config(state="disabled")
        done_label.config(text="")
        log_text.config(state="normal")
        log_text.delete("1.0", "end")
        log_text.config(state="disabled")
        progress_var.set(0)

        try:
            folders = [f for f in os.listdir(users_dir) if os.path.isdir(os.path.join(users_dir, f))]
            progress.config(maximum=max(len(folders), 1))
        except Exception:
            pass

        def task():
            try:
                run_patch(log_text, progress_var, status_label, done_label, root)
            except Exception as e:
                def _show_err():
                    log_text.config(state="normal")
                    log_text.insert("end", f"\nERROR: {e}\n")
                    log_text.see("end")
                    log_text.config(state="disabled")
                    status_label.config(text=f"Failed: {e}")
                root.after(0, _show_err)
            start_btn.after(0, lambda: start_btn.config(state="normal"))

        threading.Thread(target=task, daemon=True).start()

    start_btn = tk.Button(root, text="Disable VSync",
                          font=("Segoe UI", 10, "bold"),
                          bg="#0078d4", fg="white", activebackground="#005a9e",
                          activeforeground="white", relief="flat", padx=16, pady=6,
                          cursor="hand2", command=on_start)
    start_btn.pack(pady=(0, 16))


    style = ttk.Style()
    style.theme_use("default")
    style.configure("TProgressbar", troughcolor="#2d2d2d", background="#0078d4",
                    thickness=18)

    root.mainloop()

if __name__ == "__main__":
    build_gui()
