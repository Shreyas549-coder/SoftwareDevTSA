import tkinter as tk
import win32gui
import win32con
import keyboard
import threading
import sys
import colorsys
import random

# ================= Overlay Helper =================
def make_clickthrough(hwnd):
    styles = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(
        hwnd,
        win32con.GWL_EXSTYLE,
        styles
        | win32con.WS_EX_LAYERED
        | win32con.WS_EX_TRANSPARENT
        | win32con.WS_EX_NOACTIVATE
    )
    win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)


# ================= Overlay Class =================
class ColorOverlay:
    def __init__(self, color="#ffcc80", alpha=0.3):
        self.root = tk.Toplevel()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)

        self.root.attributes("-transparentcolor", "black")
        self.root.config(bg=color)
        self.root.wm_attributes("-alpha", alpha)

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


# ================= Mode Presets =================
FILTERS = {
    "Protanopia": {"color": "#ffb6c1", "alpha": 0.25},
    "Deuteranopia": {"color": "#ffb266", "alpha": 0.25},
    "Tritanopia": {"color": "#a0d8ef", "alpha": 0.25},
    "Achromatopsia": {"color": "#808080", "alpha": 0.3},
    "Eye Saver": {"color": "#ffcc80", "alpha": 0.3},
}

# ================= Digit Masks =================
DIGITS = {
    "0": ["01110","10001","10011","10101","11001","10001","01110"],
    "1": ["00100","01100","00100","00100","00100","00100","01110"],
    "2": ["01110","10001","00001","00110","01000","10000","11111"],
    "3": ["11110","00001","00001","01110","00001","00001","11110"],
    "4": ["10010","10010","10010","11111","00010","00010","00010"],
    "5": ["11111","10000","10000","11110","00001","00001","11110"],
    "6": ["01110","10000","10000","11110","10001","10001","01110"],
    "7": ["11111","00001","00010","00100","01000","01000","01000"],
    "8": ["01110","10001","10001","01110","10001","10001","01110"],
    "9": ["01110","10001","10001","01111","00001","00001","01110"],
}

# ================= Ishihara Plate Generator =================
def generate_plate(canvas, number, fg, bg):
    canvas.delete("all")
    for _ in range(1200):
        x = random.randint(20, 300)
        y = random.randint(20, 300)
        r = random.randint(6, 10)
        canvas.create_oval(x, y, x+r, y+r, fill=bg, outline=bg)

    cell = 22
    ox, oy = 90, 90
    rows = DIGITS[number]

    for y, row in enumerate(rows):
        for x, bit in enumerate(row):
            if bit == "1":
                cx = ox + x * cell
                cy = oy + y * cell
                for _ in range(6):
                    dx = random.randint(-6, 6)
                    dy = random.randint(-6, 6)
                    canvas.create_oval(
                        cx+dx, cy+dy,
                        cx+dx+12, cy+dy+12,
                        fill=fg, outline=fg
                    )

# ================= Overlay Color Computation =================
def compute_overlay(rg_fail, by_fail):
    if rg_fail and by_fail:
        hue = 0.58
    elif rg_fail:
        hue = 0.62
    elif by_fail:
        hue = 0.08
    else:
        return None
    r, g, b = colorsys.hsv_to_rgb(hue, 0.75, 0.85)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

# ================= Main App =================
class App:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Color Assist")
        self.window.geometry("400x550")
        self.window.configure(bg="#222222")

        tk.Label(self.window, text="Select Mode:", font=("Segoe UI", 14), fg="white", bg="#222222").pack(pady=8)

        # Mode Buttons
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

        # Disable overlay
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

        # Custom Ishihara Test
        tk.Button(
            self.window,
            text="Color Vision Test (Ishihara)",
            font=("Segoe UI", 12),
            width=25,
            bg="#3366aa",
            fg="white",
            relief="flat",
            command=self.open_test
        ).pack(pady=6)

        # Quit button
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

        # Hotkey info
        tk.Label(
            self.window,
            text="Press Ctrl + Shift + O to toggle overlay on/off",
            font=("Segoe UI", 10),
            fg="gray",
            bg="#222222"
        ).pack(side="bottom", pady=15)

        self.overlay = None
        self.window.protocol("WM_DELETE_WINDOW", self.quit_program)

        threading.Thread(target=self.listen_hotkey, daemon=True).start()
        self.window.mainloop()

    # ================= Overlay Control =================
    def start_overlay(self, mode):
        self.disable_overlay()
        data = FILTERS[mode]
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

    # ================= Ishihara Test =================
    def open_test(self):
        self.test = tk.Toplevel(self.window)
        self.test.title("Ishihara Color Vision Test")
        self.test.geometry("360x540")
        self.test.configure(bg="#222")

        tk.Label(
            self.test,
            text="Type the NUMBER you see.\nLeave blank if you cannot see one.",
            fg="white",
            bg="#222",
            justify="center"
        ).pack(pady=10)

        self.canvas = tk.Canvas(self.test, width=320, height=320, bg="#222", highlightthickness=0)
        self.canvas.pack()

        self.entry = tk.Entry(self.test, font=("Segoe UI", 16), justify="center")
        self.entry.pack(pady=8)

        tk.Button(
            self.test,
            text="Submit",
            bg="#33aa66",
            fg="white",
            command=self.submit_test
        ).pack(pady=10)

        # Plates for test
        self.plates_rg = [random.choice(list(DIGITS)) for _ in range(4)]
        self.plates_by = [random.choice(list(DIGITS)) for _ in range(4)]
        self.stage = 0
        self.rg_fail = False
        self.by_fail = False

        self.show_plate()

    def show_plate(self):
        self.entry.delete(0, tk.END)

        if self.stage < len(self.plates_rg):
            self.current = self.plates_rg[self.stage]
            self.mode = "rg"
            fg, bg = "#cc4444", "#44aa44"
        else:
            idx = self.stage - len(self.plates_rg)
            if idx >= len(self.plates_by):
                self.finish_test()
                return
            self.current = self.plates_by[idx]
            self.mode = "by"
            fg, bg = "#4444cc", "#cccc44"

        generate_plate(self.canvas, self.current, fg, bg)

    def submit_test(self):
        if self.entry.get().strip() != self.current:
            if self.mode == "rg":
                self.rg_fail = True
            else:
                self.by_fail = True

        self.stage += 1
        self.show_plate()

    def finish_test(self):
        self.test.destroy()
        color = compute_overlay(self.rg_fail, self.by_fail)
        if color:
            self.disable_overlay()
            self.overlay = ColorOverlay(color, 0.28)


# ================= Run =================
if __name__ == "__main__":
    App()
