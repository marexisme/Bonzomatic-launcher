import os
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog, Menu
import sys
import fnmatch
import stat

# === Constants ===
EXE_NAME = "Bonzomatic_W64_GLFW.exe"
MAX_PER_COLUMN = 10
USER_HOME = os.path.expanduser("~\\Appdata\\Roaming")
CONFIG_DIR = os.path.join(USER_HOME, "BonzomaticLauncher")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.txt")

EXE_NAMES_PRIORITY = [
    "Bonzomatic_W64_GLFW.exe",  # Priorité 1 : GLFW 64-bit
    "Bonzomatic_W32_GLFW.exe",  # Priorité 2 : GLFW 32-bit (si tu veux)
    "Bonzomatic.exe",           # Priorité 3 : exécutable générique
]

def resource_path(relative_path):
    """ Récupère le chemin absolu d’un fichier, que l’on soit en .py ou en .exe """
    if hasattr(sys, '_MEIPASS'):
        # En exécutable
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Exemple d’accès à un fichier ou dossier dans bonzo/
MODEL_FOLDER_PATH = resource_path("new")

# === Colors and Style ===
COLOR_BG = "#2b2b2b"
COLOR_BTN = "#3c3c3c"
COLOR_BTN_HOVER = "#505050"
COLOR_TEXT = "#ffffff"
COLOR_ACCENT = "#aaaaaa"

FONT_LABEL = ("Segoe UI", 12)
FONT_BTN = ("Segoe UI", 11, "bold")

def resource_path2(relative_path):
    try:
        base_path = sys._MEIPASS  # utilisé par PyInstaller
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_last_used_folder():
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                path = f.read().strip()
                if os.path.isdir(path):
                    return path
        except Exception as e:
            print(f"[Warning] Could not load config: {e}")
    return None

# === Main window ===
root = tk.Tk()
root.title("Bonzomatic Launcher")
root.configure(bg=COLOR_BG)
root.minsize(500, 300)
root.iconbitmap(resource_path2("logo.ico"))

# === Hover effect for buttons ===
def add_hover_effect(widget, base_color, hover_color):
    def on_enter(e):
        if not getattr(widget, 'active', False):
            widget['background'] = hover_color
    def on_leave(e):
        if not getattr(widget, 'active', False):
            widget['background'] = base_color
    def on_press(e):
        # Si actif, ne change pas la couleur au clic
        if getattr(widget, 'active', False):
            return "break"  # empêche la propagation et le changement de couleur
        else:
            widget['background'] = hover_color
    def on_release(e):
        # Si actif, garder rouge, sinon base_color
        if getattr(widget, 'active', False):
            widget['background'] = 'red'
        else:
            widget['background'] = base_color

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)
    widget.bind("<ButtonPress-1>", on_press)
    widget.bind("<ButtonRelease-1>", on_release)
    widget['cursor'] = 'hand2'

def refresh_versions():
    if parent_folder_global:
        display_versions(parent_folder_global)
    else:
        messagebox.showinfo("No folder", "Please select a folder first.")

# === Top section ===
top_frame = tk.Frame(root, bg=COLOR_BG)
top_frame.pack(pady=10, anchor="w", padx=10)

label_info = tk.Label(
    top_frame,
    text="No folder selected.",
    bg=COLOR_BG,
    fg=COLOR_ACCENT,
    font=FONT_LABEL
)
label_info.pack(side="left", padx=(0, 10))

btn_choose = tk.Button(
    top_frame,
    text="📁",
    font=FONT_BTN,
    bg=COLOR_BTN,
    fg=COLOR_TEXT,
    activebackground=COLOR_BTN_HOVER,
    activeforeground=COLOR_TEXT,
    relief="flat",
    bd=1,
    width=4,
    height=1,
    command=lambda: choose_folder()
)
btn_choose.pack(side="left")
add_hover_effect(btn_choose, COLOR_BTN, COLOR_BTN_HOVER)

btn_refresh = tk.Button(
    top_frame,
    text="⟳",
    font=FONT_BTN,
    bg=COLOR_BTN,
    fg=COLOR_TEXT,
    activebackground=COLOR_BTN_HOVER,
    activeforeground=COLOR_TEXT,
    relief="flat",
    bd=1,
    width=4,
    height=1,
    command=refresh_versions
)
btn_refresh.pack(side="left", padx=(5, 0))
add_hover_effect(btn_refresh, COLOR_BTN, COLOR_BTN_HOVER)

# === Frame for version buttons ===
btn_frame = tk.Frame(root, bg=COLOR_BG)
btn_frame.pack(pady=10)

parent_folder_global = None

active_processes = {}
active_button = None

def launch_bonzomatic(exe_path, btn):
    global active_processes

    # Si process déjà actif et vivant, ne rien faire (bouton reste rouge)
    if btn in active_processes and active_processes[btn].poll() is None:
        # juste s'assurer que bouton est actif (rouge)
        btn.config(bg="red")
        btn.active = True
        return

    try:
        proc = subprocess.Popen(exe_path, cwd=os.path.dirname(exe_path))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to launch:\n{exe_path}\n\n{e}")
        return

    active_processes[btn] = proc
    btn.config(bg="red")
    btn.active = True
    check_process_alive(btn)

def check_process_alive(btn):
    global active_processes

    if btn in active_processes:
        retcode = active_processes[btn].poll()
        if retcode is not None:
            btn.config(bg=COLOR_BTN)
            btn.active = False
            del active_processes[btn]
        else:
            root.after(1000, lambda: check_process_alive(btn))


def clear_buttons():
    global active_button
    for widget in btn_frame.winfo_children():
        widget.destroy()
    active_button = None

def save_last_used_folder(folder_path):
    try:
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        with open(CONFIG_FILE, "w") as f:
            f.write(folder_path)
    except Exception as e:
        print(f"[Warning] Could not save config: {e}")

def choose_folder():
    global parent_folder_global
    folder = filedialog.askdirectory(title="Select Bonzomatic parent folder")
    if folder:
        parent_folder_global = folder
        label_info.config(text=f"Selected folder: {folder}")
        save_last_used_folder(folder)  # Sauvegarde le chemin dans le fichier config dans le dossier choisi
        display_versions(folder)

def find_bonzomatic_versions(parent_folder):
    versions = []
    for folder in os.listdir(parent_folder):
        folder_path = os.path.join(parent_folder, folder)
        if os.path.isdir(folder_path):
            exe_path = None
            for exe_name in EXE_NAMES_PRIORITY:
                candidate = os.path.join(folder_path, exe_name)
                if os.path.isfile(candidate):
                    exe_path = candidate
                    break  # prend le premier trouvé dans l’ordre de priorité
            if exe_path:
                versions.append((folder, exe_path))
    return versions

def split_text_two_lines(text, max_line_length=20):
    if len(text) <= max_line_length:
        return text
    mid = len(text) // 2
    left_space = text.rfind(' ', 0, mid)
    right_space = text.find(' ', mid)
    split_pos = -1
    if left_space == -1 and right_space == -1:
        split_pos = mid
    else:
        if left_space == -1:
            split_pos = right_space
        elif right_space == -1:
            split_pos = left_space
        else:
            if mid - left_space <= right_space - mid:
                split_pos = left_space
            else:
                split_pos = right_space
    if split_pos == -1:
        split_pos = mid
    return text[:split_pos] + "\n" + text[split_pos+1:]

def display_versions(parent_folder, rename_target=None):
    clear_buttons()
    versions = find_bonzomatic_versions(parent_folder)

    buttons = []

    def force_remove_readonly(func, path, exc_info):    
        # Change les permissions et retente la suppression
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def on_rename(button, folder_name, folder_path):
        entry = tk.Entry(
            btn_frame,
            font=FONT_BTN,
            width=25,
            bg=COLOR_BTN,
            fg=COLOR_TEXT,
            insertbackground=COLOR_TEXT,
            relief="flat"
        )
        entry.insert(0, folder_name)
        entry.select_range(0, tk.END)
        entry.focus()
        entry.grid(row=button.grid_info()['row'], column=button.grid_info()['column'], padx=10, pady=5, sticky="nsew")

        button.grid_forget()

        def confirm_rename(event=None):
            new_name = entry.get().strip()
            if not new_name or new_name == folder_name:
                cancel_rename()
                return
            new_path = os.path.join(parent_folder, new_name)
            if os.path.exists(new_path):
                messagebox.showerror("Error", f"A folder named '{new_name}' already exists.")
                return
            try:
                os.rename(folder_path, new_path)
                display_versions(parent_folder)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to rename:\n{e}")

        def cancel_rename(event=None):
            entry.destroy()
            display_versions(parent_folder)

        entry.bind("<Return>", confirm_rename)
        entry.bind("<Escape>", cancel_rename)

    def on_delete(folder_name, folder_path):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{folder_name}'? This cannot be undone."):
            try:
                shutil.rmtree(folder_path, onerror=force_remove_readonly)
                display_versions(parent_folder)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete:\n{e}")

    for idx, (folder_name, exe_path) in enumerate(versions):
        col = idx // MAX_PER_COLUMN
        row = idx % MAX_PER_COLUMN
        folder_path = os.path.join(parent_folder, folder_name)

        btn = tk.Button(
            btn_frame,
            text=split_text_two_lines(folder_name, max_line_length=20),
            bg=COLOR_BTN,
            fg=COLOR_TEXT,
            activebackground=COLOR_BTN_HOVER,
            activeforeground=COLOR_TEXT,
            font=FONT_BTN,
            width=25,
            height=2,
            relief="flat",
            bd=1
        )
        btn.active = False
        btn.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
        add_hover_effect(btn, COLOR_BTN, COLOR_BTN_HOVER)
        def on_button_click(event, exe_path=exe_path, btn=btn):
            if getattr(btn, 'active', False):
                return "break"  # empêche la propagation du clic
            else:
                launch_bonzomatic(exe_path, btn)

        btn.bind("<Button-1>", on_button_click)

        menu = Menu(root, tearoff=0,bg=COLOR_BG,fg=COLOR_TEXT,activebackground=COLOR_BTN_HOVER,activeforeground=COLOR_TEXT,bd=0,relief='flat',font=FONT_BTN)
        menu.add_command(label="Rename", command=lambda b=btn, fn=folder_name, fp=folder_path: on_rename(b, fn, fp))
        menu.add_command(label="Delete", command=lambda fn=folder_name, fp=folder_path: on_delete(fn, fp))

        def do_popup(event, m=menu):
            try:
                m.tk_popup(event.x_root, event.y_root)
            finally:
                m.grab_release()

        btn.bind("<Button-3>", do_popup)

        buttons.append((btn, folder_name, folder_path))

    total_versions = len(versions)
    col = total_versions // MAX_PER_COLUMN
    row = total_versions % MAX_PER_COLUMN

    def create_new_bonzomatic():
        global parent_folder_global
        if not parent_folder_global:
            messagebox.showwarning("Warning", "Please select a parent folder first.")
            return

        if not os.path.isdir(MODEL_FOLDER_PATH):
            messagebox.showerror("Error", f"Model folder path is invalid:\n{MODEL_FOLDER_PATH}")
            return

        base_name = "Bonzomatic_New"
        i = 1
        while True:
            new_folder_name = f"{base_name}_{i}"
            new_folder_path = os.path.join(parent_folder_global, new_folder_name)
            if not os.path.exists(new_folder_path):
                break
            i += 1

        try:
            shutil.copytree(MODEL_FOLDER_PATH, new_folder_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy model folder:\n{e}")
            return

        display_versions(parent_folder_global, rename_target=new_folder_name)

    new_btn = tk.Button(
        btn_frame,
        text="+ New\nBonzomatic",
        bg="#4CAF50",
        fg=COLOR_TEXT,
        activebackground="#45a049",
        activeforeground=COLOR_TEXT,
        font=FONT_BTN,
        width=25,
        height=2,
        relief="flat",
        bd=1,
        command=create_new_bonzomatic
    )
    new_btn.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
    add_hover_effect(new_btn, "#4CAF50", "#45a049")

    root.update_idletasks()
    root.geometry("")


# === Charger le dossier précédent au démarrage ===
last_folder = load_last_used_folder()
if last_folder:
    parent_folder_global = last_folder
    label_info.config(text=f"Selected folder: {last_folder}")
    display_versions(last_folder)
else:
    label_info.config(text="No folder selected.")

root.mainloop()
