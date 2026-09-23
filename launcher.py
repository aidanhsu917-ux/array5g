import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
import threading

SCRIPTS = {
"Pluto Line Tracking": "Pluto_beamformer_Monopulse_youtube.py",
"Pluto Compass Tracking": "compass_launcher.py",
"Angle with Null": "Pluto_MVDR_DOA.py",
}
PLUTO_IP = "192.168.2.1"

def check_pluto_connection():
    """Check if Pluto SDR is connected and accessible."""

    try:
        import adi
        sdr = adi.ad9361(uri=f'ip:{PLUTO_IP}')
        # Try to read a simple property to verify connection
        _ = sdr.sample_rate
        return True
    
    except Exception:
        return False

def update_connection_status():
    """Update the connection status indicator in a separate thread."""
    def check_and_update():
        is_connected = check_pluto_connection()
        if is_connected:
            status_label.config(text="Pluto Connected", foreground="#00ff88")
            status_indicator.config(background="#00ff88")
        else:
            status_label.config(text="Pluto Not Detected", foreground="#ff4444")
            status_indicator.config(background="#ff4444")
        # Schedule next check in 3 seconds
        root.after(3000, update_connection_status)
        # Run check in background thread to avoid blocking GUI
    thread = threading.Thread(target=check_and_update, daemon=True)
    thread.start()

def launch_script(script_filename):
    """Close the launcher and run the chosen script."""
    full_path = os.path.abspath(script_filename)
    if not os.path.exists(full_path):
        messagebox.showerror(
            "File Not Found",
            f"Could not find:\n{full_path}\n\nCheck the file name or location.",
        )
    return
# Start the selected script using the same Python interpreter
    subprocess.Popen([sys.executable, full_path])
# Optionally close the launcher after starting the script
# root.destroy()

# ---- Build the GUI --------------------------------------------------
root = tk.Tk()
root.title("Pluto Beamforming Demos")

root.geometry("450x520")
root.resizable(False, False) # Lock window size
root.configure(bg="#1a1a1a") # Dark background
# Custom styling for dark theme
style = ttk.Style(root)
# Configure dark theme colors
BG_COLOR = "#1a1a1a"
BUTTON_BG = "#2d2d2d"
BUTTON_HOVER = "#3d3d3d"
BUTTON_ACTIVE = "#4d4d4d"
TEXT_COLOR = "#e0e0e0"
ACCENT_COLOR = "#00aaff"
# Try to use available theme and customize it
try:
    style.theme_use("clam")
except:
    style.theme_use("default")
# Configure button style
style.configure(
    "Big.TButton",
    font=("Segoe UI", 14, "bold"),
    padding=20,
    background=BUTTON_BG,
    foreground=TEXT_COLOR,
    borderwidth=0,
    focuscolor="none",
    relief="flat"
)
style.map("Big.TButton",
    background=[("active", BUTTON_HOVER), ("pressed", BUTTON_ACTIVE)],
    foreground=[("active", TEXT_COLOR)]
)
# Configure title label style
style.configure(
    "Title.TLabel",
    font=("Segoe UI", 18, "bold"),
    background=BG_COLOR,
    foreground=ACCENT_COLOR,
)
# Configure status label style
style.configure(
    "Status.TLabel",
    font=("Segoe UI", 10),
    background=BG_COLOR,
    foreground="#ff4444",
)
# Main container frame
main_frame = tk.Frame(root, bg=BG_COLOR)
main_frame.pack(expand=True, fill="both", padx=20, pady=20)
# Title label
title_label = ttk.Label(
    main_frame,
    text="ADAPT-5G Demo Software",
    style="Title.TLabel",
)
title_label.pack(pady=(0, 10))
# Status frame (connection indicator)
status_frame = tk.Frame(main_frame, bg=BG_COLOR)
status_frame.pack(pady=(0, 20))
# Status indicator circle
status_indicator = tk.Canvas(
    status_frame,
    width=12,
    height=12,
    bg=BG_COLOR,
    highlightthickness=0
)
status_indicator.create_oval(2, 2, 10, 10, fill="#ff4444", outline="")
status_indicator.pack(side="left", padx=(0, 8))

# Status label
status_label = tk.Label(
    status_frame,
    text="Checking Connection...",
    font=("Segoe UI", 10),
    bg=BG_COLOR,
    fg="#888888"
)
status_label.pack(side="left")
# Separator line
separator = tk.Frame(main_frame, height=2, bg="#333333")
separator.pack(fill="x", pady=(0, 20))

# Button container
button_frame = tk.Frame(main_frame, bg=BG_COLOR)
button_frame.pack(fill="both", expand=True)

# Create styled buttons with rounded appearance
for name, filename in SCRIPTS.items():
    # Container for rounded button effect
    btn_container = tk.Frame(button_frame, bg=BG_COLOR)
    btn_container.pack(fill="x", pady=8)
# Custom button with rounded corners effect using Canvas
    canvas = tk.Canvas(
        btn_container,
        height=70,
        bg=BG_COLOR,
        highlightthickness=0
    )
    canvas.pack(fill="x")
# Draw rounded rectangle
    def create_rounded_button(canvas, text, filename):
        def on_enter(e):
            canvas.itemconfig(rect, fill=BUTTON_HOVER)

        def on_leave(e):
            canvas.itemconfig(rect, fill=BUTTON_BG)

        def on_click(e):
            canvas.itemconfig(rect, fill=BUTTON_ACTIVE)
            canvas.after(100, lambda: launch_script(filename))
# Rounded rectangle (simulated with polygon)
        radius = 15
        width = canvas.winfo_reqwidth()
        if width <= 1:
            width = 400
        height = 70
        rect = canvas.create_rectangle(
            10, 10, width-10, height-10,
            fill=BUTTON_BG,
            outline="",
            width=0
        )

        text_item = canvas.create_text(
            width//2, height//2,
            text=text,
            fill=TEXT_COLOR,
            font=("Segoe UI", 14, "bold")
        )
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", on_click)

        return rect, text_item
    
    # Delay button creation until canvas is sized
    canvas.update()
    create_rounded_button(canvas, name, filename)
# Footer text
footer = tk.Label(
    main_frame,
    text="Select a demo to begin",
    font=("Segoe UI", 9),
    bg=BG_COLOR,
    fg="#666666"
)
footer.pack(side="bottom", pady=(15, 0))
# Start connection status updates
root.after(500, update_connection_status)
root.mainloop()