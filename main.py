import tkinter as tk
import win32gui
import win32con
import keyboard
import threading
import sys
import colorsys
import random

# ================= Overlay Class =================
class ColorOverlay:
    def __init__(self, color="#ffcc80", alpha=0.3):
        self.root = tk.Toplevel()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.config(bg=color)
        self.root.wm_attributes("-alpha", alpha)

        # Click-through fix
        hwnd = self.root.winfo_id()
        styles = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(
            hwnd,
            win32con.GWL_EXSTYLE,
            styles | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_NOACTIVATE
        )
        win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)

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
    "5": ["11111","10000","10000","11110","00001","00001","11110"],
    "8": ["01110","10001","10001","01110","10001","10001","01110"],
    "12":["00100 01110","01100 10001","00100 00001","00100 00110","00100 01000","00100 10000","01110 11111"]
}

# ================= Ishihara Plate Generator =================
def generate_plate(canvas, number, fg, bg):
    canvas.delete("all")
    cell = 18
    ox, oy = 90, 90

    # Background dots
    for _ in range(1100):
        x = random.randint(20, 300)
        y = random.randint(20, 300)
        canvas.create_oval(x, y, x+6, y+6, fill=bg, outline=bg)

    # Foreground number
    rows = DIGITS[number]
    for y_idx, row in enumerate(rows):
        cols = row.split()
        for digit_idx, col_row in enumerate(cols):
            for x_idx, bit in enumerate(col_row):
                if bit == "1":
                    cx = ox + digit_idx * 6 * cell + x_idx * cell
                    cy = oy + y_idx * cell
                    for _ in range(5):
                        dx = random.randint(-4,4)
                        dy = random.randint(-4,4)
                        canvas.create_oval(
                            cx+dx, cy+dy,
                            cx+dx+12, cy+dy+12,
                            fill=fg, outline=fg
                        )

# ================= Overlay Color Calculation =================
def compute_overlay(rg_fail, by_fail):
    if rg_fail and by_fail:
        hue = 0.58  # cyan-blue
    elif rg_fail:
        hue = 0.62  # blue bias
    elif by_fail:
        hue = 0.08  # amber bias
    else:
        return None  # no overlay if passed

    r,g,b = colorsys.hsv_to_rgb(hue,0.75,0.85)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

# ================= Main App =================
class App:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Color Assist")
        self.window.geometry("400x550")
        self.window.configure(bg="#222")

        tk.Label(self.window, text="Select Mode:", fg="white", bg="#222", font=("Segoe UI", 14)).pack(pady=8)

        for mode in FILTERS:
            tk.Button(self.window, text=mode, width=20, bg="#444", fg="white",
                      command=lambda m=mode: self.start_overlay(m)).pack(pady=3)

        tk.Button(self.window, text="Disable Overlay", width=20, bg="#555", fg="white",
                  command=self.disable_overlay).pack(pady=8)

        tk.Button(self.window, text="Color Vision Test (Ishihara)", width=20, bg="#3366aa", fg="white",
                  command=self.open_test).pack(pady=6)

        tk.Label(self.window, text="Press Ctrl + Shift + O to toggle overlay on/off",
                 font=("Segoe UI", 10), fg="gray", bg="#222").pack(side="bottom", pady=15)

        self.overlay = None
        threading.Thread(target=self.listen_hotkey, daemon=True).start()
        self.window.mainloop()

    def start_overlay(self, mode):
        self.disable_overlay()
        d = FILTERS[mode]
        self.overlay = ColorOverlay(d["color"], d["alpha"])

    # ================= Ishihara Test =================
    def open_test(self):
        self.test = tk.Toplevel(self.window)
        self.test.title("Ishihara Test")
        self.test.geometry("360x550")
        self.test.configure(bg="#222")

        tk.Label(self.test, text="INSTRUCTIONS:\nType the NUMBER you see.\nLeave blank if you cannot see it.",
                 fg="white", bg="#222", wraplength=330, justify="center").pack(pady=10)

        self.canvas = tk.Canvas(self.test, width=320, height=320, bg="#222")
        self.canvas.pack()

        self.entry = tk.Entry(self.test, font=("Segoe UI", 16), justify="center")
        self.entry.pack(pady=8)

        tk.Button(self.test, text="Submit", bg="#33aa66", fg="white", command=self.submit_test).pack(pady=8)

        # Multiple plates
        self.plates_rg = [random.choice(list(DIGITS.keys())) for _ in range(3)]
        self.plates_by = [random.choice(list(DIGITS.keys())) for _ in range(3)]
        self.current_stage = 0
        self.total_stages = len(self.plates_rg) + len(self.plates_by)
        self.rg_fail = False
        self.by_fail = False

        self.show_plate()

    def show_plate(self):
        if self.current_stage >= self.total_stages:
            self.finish_test()
            return

        self.entry.delete(0, tk.END)
        if self.current_stage < len(self.plates_rg):
            self.current_number = self.plates_rg[self.current_stage]
            self.current_type = "rg"
            fg, bg = "#cc4444", "#44aa44"
        else:
            idx = self.current_stage - len(self.plates_rg)
            self.current_number = self.plates_by[idx]
            self.current_type = "by"
            fg, bg = "#4444cc", "#cccc44"

        generate_plate(self.canvas, self.current_number, fg, bg)

    def submit_test(self):
        answer = self.entry.get().strip()
        if answer != self.current_number:
            if self.current_type == "rg":
                self.rg_fail = True
            elif self.current_type == "by":
                self.by_fail = True

        self.current_stage += 1
        self.show_plate()

    def finish_test(self):
        self.test.destroy()
        color = compute_overlay(self.rg_fail, self.by_fail)
        if color:
            self.disable_overlay()
            self.overlay = ColorOverlay(color, 0.28)

    def disable_overlay(self):
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None

    def listen_hotkey(self):
        while True:
            keyboard.wait("ctrl+shift+o")
            if self.overlay:
                self.overlay.toggle()

# ================= Run =================
if __name__ == "__main__":
    App()
