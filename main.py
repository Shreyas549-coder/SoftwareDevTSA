import tkinter as tk

import win32con
import win32gui


def make_clickthrough(hwnd):
    # Make window transparent to mouse clicks
    styles = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(
        hwnd,
        win32con.GWL_EXSTYLE,
        styles | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
    )
    win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)


class ColorOverlay:
    def __init__(self, color="#ffcc80", alpha=0.3):  # warm orange tint
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-transparentcolor', 'black')
        self.root.config(bg=color)
        self.root.wm_attributes("-alpha", alpha)
        self.root.overrideredirect(True)  # remove window decorations

        # ✅ Get the correct window handle from tkinter itself
        self.root.update_idletasks()
        hwnd = self.root.winfo_id()
        make_clickthrough(hwnd)

    def start(self):
        self.root.mainloop()


if __name__ == "__main__":
    print("🔆 Eye Saver (Deuteranopia Mode) Enabled. Press Ctrl+C to close.")
    overlay = ColorOverlay(color="#ffb266", alpha=0.25)
    overlay.start()
