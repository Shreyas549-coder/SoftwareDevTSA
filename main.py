import tkinter as tk
import win32gui
import win32con
import keyboard
import threading
import sys
import colorsys
import random

# make window click-through
def click_through(hwnd):
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(
        hwnd,
        win32con.GWL_EXSTYLE,
        style
        | win32con.WS_EX_LAYERED
        | win32con.WS_EX_TRANSPARENT
        | win32con.WS_EX_NOACTIVATE
    )
    win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)

# overlay window
class Overlay:
    def __init__(self, color="#ffcc80", alpha=0.3):
        self.win = tk.Toplevel()
        self.win.attributes("-fullscreen", True)
        self.win.attributes("-topmost", True)
        self.win.overrideredirect(True)
        self.win.attributes("-transparentcolor", "black")
        self.win.config(bg=color)
        self.win.wm_attributes("-alpha", alpha)
        self.win.update_idletasks()
        click_through(self.win.winfo_id())
        self.visible = True

    def toggle(self):
        if self.visible:
            self.win.withdraw()
        else:
            self.win.deiconify()
        self.visible = not self.visible

    def close(self):
        try:
            self.win.destroy()
        except:
            pass

# overlay color modes
MODES = {
    "Protanopia": {"color": "#ffb6c1", "alpha": 0.25},
    "Deuteranopia": {"color": "#ffb266", "alpha": 0.25},
    "Tritanopia": {"color": "#a0d8ef", "alpha": 0.25},
    "Achromatopsia": {"color": "#808080", "alpha": 0.3},
    "Eye Saver": {"color": "#ffcc80", "alpha": 0.3},
}

# digits for test (Ishihara-style)
NUMBERS = {
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

# draw plate
def draw_plate(canvas, number, fg, bg):
    canvas.delete("all")
    for _ in range(1200):
        x = random.randint(20, 300)
        y = random.randint(20, 300)
        r = random.randint(6, 10)
        canvas.create_oval(x, y, x+r, y+r, fill=bg, outline=bg)

    cell = 22
    ox, oy = 90, 90
    for y_idx, row in enumerate(NUMBERS[number]):
        for x_idx, bit in enumerate(row):
            if bit == "1":
                cx = ox + x_idx * cell
                cy = oy + y_idx * cell
                for _ in range(6):
                    dx = random.randint(-6, 6)
                    dy = random.randint(-6, 6)
                    canvas.create_oval(
                        cx+dx, cy+dy,
                        cx+dx+12, cy+dy+12,
                        fill=fg, outline=fg
                    )

# overlay decision
def get_overlay_color(rg, by):
    if rg and by:
        hue = 0.58
    elif rg:
        hue = 0.62
    elif by:
        hue = 0.08
    else:
        return None
    r, g, b = colorsys.hsv_to_rgb(hue, 0.75, 0.85)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

class App:
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("Color Assist")
        self.win.geometry("460x700")  # bigger window
        self.win.minsize(460, 700)
        self.win.configure(bg="#1e1e1e")

        BG = "#1e1e1e"
        CARD = "#2a2a2a"
        BTN = "#3a3a3a"
        BTN_HOVER = "#505050"
        TEXT = "#ffffff"
        SUBTEXT = "#aaaaaa"
        ACCENT = "#4da6ff"

        def make_button(parent, text, cmd, color=BTN):
            btn = tk.Button(
                parent, text=text, font=("Segoe UI", 11),
                bg=color, fg=TEXT, relief="flat",
                activebackground=BTN_HOVER,
                command=cmd, padx=10, pady=8
            )
            btn.bind("<Enter>", lambda e: btn.config(bg=BTN_HOVER))
            btn.bind("<Leave>", lambda e: btn.config(bg=color))
            return btn

        # Title
        tk.Label(self.win, text="Color Assist",
                 font=("Segoe UI", 20, "bold"),
                 fg=TEXT, bg=BG).pack(pady=(15, 5))

        tk.Label(self.win, text="Accessibility overlay + Ishihara-style test",
                 font=("Segoe UI", 10),
                 fg=SUBTEXT, bg=BG).pack(pady=(0, 10))

        # Status
        self.status = tk.Label(self.win, text="No Overlay Active",
                               fg=SUBTEXT, bg=BG)
        self.status.pack(pady=5)

        # Modes
        frame = tk.Frame(self.win, bg=CARD)
        frame.pack(padx=15, pady=10, fill="x")

        tk.Label(frame, text="Overlay Modes",
                 font=("Segoe UI", 13, "bold"),
                 fg=TEXT, bg=CARD).pack(anchor="w", padx=10, pady=5)

        for mode in MODES:
            make_button(frame, mode,
                        lambda m=mode: self.start_overlay(m)
                        ).pack(fill="x", padx=10, pady=4)

        # Controls
        frame2 = tk.Frame(self.win, bg=CARD)
        frame2.pack(padx=15, pady=10, fill="x")

        tk.Label(frame2, text="Controls",
                 font=("Segoe UI", 13, "bold"),
                 fg=TEXT, bg=CARD).pack(anchor="w", padx=10, pady=5)

        make_button(frame2, "Disable Overlay",
                    self.disable_overlay, "#555").pack(fill="x", padx=10, pady=4)

        make_button(frame2, "Quit",
                    self.quit, "#aa3333").pack(fill="x", padx=10, pady=4)

        # Tools (TEST clearly visible now)
        frame3 = tk.Frame(self.win, bg=CARD)
        frame3.pack(padx=15, pady=10, fill="x")

        tk.Label(frame3, text="Vision Test (Ishihara Style)",
                 font=("Segoe UI", 13, "bold"),
                 fg=TEXT, bg=CARD).pack(anchor="w", padx=10, pady=5)

        make_button(frame3, "Start Test",
                    self.open_test, ACCENT).pack(fill="x", padx=10, pady=10)

        # Footer
        tk.Label(self.win, text="Hotkey: Ctrl + Shift + O",
                 fg=SUBTEXT, bg=BG).pack(side="bottom", pady=10)

        self.overlay = None
        self.win.protocol("WM_DELETE_WINDOW", self.quit)
        threading.Thread(target=self.hotkey_listener, daemon=True).start()
        self.win.mainloop()

    def start_overlay(self, mode):
        self.disable_overlay()
        data = MODES[mode]
        self.overlay = Overlay(data["color"], data["alpha"])
        self.status.config(text=f"Active: {mode}")

    def disable_overlay(self):
        if self.overlay:
            self.overlay.close()
            self.overlay = None
        self.status.config(text="No Overlay Active")

    def hotkey_listener(self):
        while True:
            keyboard.wait("ctrl+shift+o")
            if self.overlay:
                self.overlay.toggle()

    def quit(self):
        self.disable_overlay()
        self.win.destroy()
        sys.exit()

    # TEST WINDOW (unchanged logic, just clearer UI)
    def open_test(self):
        self.test_win = tk.Toplevel(self.win)
        self.test_win.title("Color Vision Test")
        self.test_win.geometry("400x600")
        self.test_win.configure(bg="#1e1e1e")

        tk.Label(self.test_win,
                 text="Enter the number you see",
                 fg="white", bg="#1e1e1e").pack(pady=10)

        self.canvas = tk.Canvas(self.test_win,
                                width=320, height=320,
                                bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack()

        self.entry = tk.Entry(self.test_win,
                              font=("Segoe UI", 16),
                              justify="center")
        self.entry.pack(pady=10)

        tk.Button(self.test_win,
                  text="Submit",
                  bg="#33aa66", fg="white",
                  command=self.submit_test).pack(pady=10)

        self.rg_plates = [random.choice(list(NUMBERS)) for _ in range(4)]
        self.by_plates = [random.choice(list(NUMBERS)) for _ in range(4)]
        self.stage = 0
        self.rg_fail = False
        self.by_fail = False
        self.show_plate()

    def show_plate(self):
        self.entry.delete(0, tk.END)
        if self.stage < len(self.rg_plates):
            self.current = self.rg_plates[self.stage]
            self.mode = "rg"
            fg, bg = "#cc4444", "#44aa44"
        else:
            idx = self.stage - len(self.rg_plates)
            if idx >= len(self.by_plates):
                self.finish_test()
                return
            self.current = self.by_plates[idx]
            self.mode = "by"
            fg, bg = "#4444cc", "#cccc44"

        draw_plate(self.canvas, self.current, fg, bg)

    def submit_test(self):
        if self.entry.get().strip() != self.current:
            if self.mode == "rg":
                self.rg_fail = True
            else:
                self.by_fail = True
        self.stage += 1
        self.show_plate()

    def finish_test(self):
        self.test_win.destroy()
        color = get_overlay_color(self.rg_fail, self.by_fail)
        if color:
            self.disable_overlay()
            self.overlay = Overlay(color, 0.28)
            self.status.config(text="Active: Auto-detected")

# run
if __name__ == "__main__":
    App()