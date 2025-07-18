# __main__.py
import tkinter as tk
from datetime import date
from gui import show_popup
from storage import load_projects
from config import INTERVAL_OPTIONS, DEFAULT_INTERVAL
from utils import log_debug_event

# Initialize the root window
root = tk.Tk()
root.withdraw()  # hide the base window

# Interval state
selected_interval = DEFAULT_INTERVAL
INTERVAL = INTERVAL_OPTIONS[selected_interval]
popup_interval_handle = None  # for tracking/rescheduling

# === Schedule pop-up function ===
def schedule_popup():
    global popup_interval_handle
    log_debug_event(f"Popup timer triggered at interval: {INTERVAL // 1000}s")
    show_popup(load_projects(), reschedule_callback=reschedule_popup)
    popup_interval_handle = root.after(INTERVAL, schedule_popup)


# === Reschedule after interval change ===
def reschedule_popup(new_interval_label=None):
    global INTERVAL, popup_interval_handle, selected_interval
    if new_interval_label:
        selected_interval = new_interval_label
        INTERVAL = INTERVAL_OPTIONS.get(selected_interval, INTERVAL_OPTIONS[DEFAULT_INTERVAL])
    if popup_interval_handle:
        root.after_cancel(popup_interval_handle)
    popup_interval_handle = root.after(INTERVAL, schedule_popup)
    log_debug_event(f"Popup interval reset to {INTERVAL // 1000}s after interaction.")


# === Entry point ===
if __name__ == "__main__":
    log_debug_event("---- App Started ----")

    # Initial popup after a short delay
    root.after(1000, lambda: show_popup(load_projects(), reschedule_callback=reschedule_popup))
    
    # Schedule recurring popups
    popup_interval_handle = root.after(INTERVAL, schedule_popup)

    root.mainloop()
