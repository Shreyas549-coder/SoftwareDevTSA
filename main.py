import tkinter as tk
import win32gui
import win32con
import keyboard
import threading
import sys


# === Overlay Helper ===
def make_clickthrough(hwnd):
    styles = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(
        hwnd,
        win32con.GWL_EXSTYLE,
        styles | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
    )
    win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)


# === Overlay Class ===
class ColorOverlay:
    def __init__(self, color="#ffcc80", alpha=0.3):
        self.root = tk.Toplevel()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-transparentcolor', 'black')
        self.root.config(bg=color)
        self.root.wm_attributes("-alpha", alpha)
        self.root.overrideredirect(True)
        self.root.update_idletasks()
        hwnd = self.root.winfo_id()
        make_clickthrough(hwnd)
        self.visible = True

    def toggle(self):
        if self.visible:
            self.root.withdraw()
        else:
            self.root.deiconify()
        self.visible = not self.visible

    def destroy(self):
        try:
            self.root.destroy()
        except:
            pass


# === Mode Presets ===
FILTERS = {
    "Protanopia": {"color": "#ffb6c1", "alpha": 0.25},
    "Deuteranopia": {"color": "#ffb266", "alpha": 0.25},
    "Tritanopia": {"color": "#a0d8ef", "alpha": 0.25},
    "Achromatopsia": {"color": "#808080", "alpha": 0.3},
    "Eye Saver": {"color": "#ffcc80", "alpha": 0.3},
}


# === GUI App ===
class App:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Color Assist")
        self.window.geometry("400x400")
        self.window.configure(bg="#222222")

        tk.Label(
            self.window,
            text="Select Mode:",
            font=("Segoe UI", 14),
            fg="white",
            bg="#222222"
        ).pack(pady=10)

        for mode in FILTERS:
            tk.Button(
                self.window,
                text=mode,
                font=("Segoe UI", 12),
                width=20,
                bg="#444444",
                fg="white",
                relief="flat",
                command=lambda m=mode: self.start_overlay(m)
            ).pack(pady=5)

        tk.Button(
            self.window,
            text="Disable Overlay",
            font=("Segoe UI", 12),
            width=20,
            bg="#555555",
            fg="white",
            relief="flat",
            command=self.disable_overlay
        ).pack(pady=10)

        tk.Button(
            self.window,
            text="Quit",
            font=("Segoe UI", 12),
            width=20,
            bg="#aa3333",
            fg="white",
            relief="flat",
            command=self.quit_program
        ).pack(pady=5)

        tk.Label(
            self.window,
            text="Press Ctrl + Shift + O to toggle overlay on/off",
            font=("Segoe UI", 10),
            fg="gray",
            bg="#222222"
        ).pack(side="bottom", pady=15)

        self.overlay = None
        self.window.protocol("WM_DELETE_WINDOW", self.quit_program)

        self.hotkey_thread = threading.Thread(target=self.listen_hotkey, daemon=True)
        self.hotkey_thread.start()

        self.window.mainloop()

    def start_overlay(self, mode):
        data = FILTERS[mode]
        self.disable_overlay()  # Remove old overlay if one exists
        self.overlay = ColorOverlay(color=data["color"], alpha=data["alpha"])

    def disable_overlay(self):
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None

    def listen_hotkey(self):
        while True:
            keyboard.wait("ctrl+shift+o")
            if self.overlay:
                self.overlay.toggle()

    def quit_program(self):
        self.disable_overlay()
        self.window.destroy()
        sys.exit()


# === Run the App ===
if __name__ == "__main__":
    App()
