# gui.py
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import askokcancel, WARNING
from datetime import datetime, date
import os, sys
from tracker import switch_project, compute_totals, finalize_sessions
from storage import save_sessions, load_sessions, load_projects, save_projects, overwrite_sessions
from config import INTERVAL_OPTIONS, DEFAULT_INTERVAL, CONFIG_FILE
from utils import format_seconds, log_debug_event
from models import Session
import pandas as pd

# Global GUI state
root = tk.Tk()
root.withdraw()

popup = None
status_label = None
interval_var = None
project_buttons = {}
project_time_labels = {}
total_time_label = None
update_ui_handle = None
open_window = None  # Used to track the currently open secondary window
open_window_type = None  # Used to track what type of window is currently open


#Background colours
main_win_bg = "#5EC5EC" # Main GUI window
manproj_win_bg = "#3EA5CC" # Manage projects window
summary_win_bg = "#3EA5CC" # View Summary window
edit_win_bg = "#3EA5CC" # Edit log window


# Application state
sessions = [s for s in load_sessions(for_date=date.today()) if s.duration is not None]
current_project = sessions[-1].project if sessions and sessions[-1].duration is None else None
selected_interval = DEFAULT_INTERVAL
INTERVAL = INTERVAL_OPTIONS[selected_interval]


def handle_window_request(requested_type):
    # Function checks on a button click if the requested subwindow is already open. If so it is brough to the foreground.
    # If a different subwindow has been requested, then the existing subwindow is destroyed before the new one is opened.
    # This ensures only one subwindow can ever be open at a time.
    global open_window, open_window_type

    if open_window and open_window.winfo_exists():
        if open_window_type == requested_type:
            open_window.lift()
            open_window.focus_force()
            return False  # Don't open a new window
        else:
            open_window.destroy()

    open_window = None
    open_window_type = requested_type
    return True  # Ok to open new window


def offset_position_near_popup(offset_x=50, offset_y=50):
    # Generate offset location coordinates for subwindows, relative to the main GUI window
    if popup and popup.winfo_exists():
        popup.update_idletasks()
        x = popup.winfo_x() + offset_x
        y = popup.winfo_y() + offset_y
        return f"+{x}+{y}"
    return ""



def end_workday():
    global sessions, update_ui_handle
    answer = askokcancel('Confirm exit', 'Save final log entry and quit Timesheet Logger app?', icon=WARNING, parent=popup)
    if answer:
        log_debug_event("End of workday triggered.")
        sessions = finalize_sessions(sessions)
        save_sessions(sessions)

        if update_ui_handle:
            popup.after_cancel(update_ui_handle)
            update_ui_handle = None
        
        try:
            popup.destroy()
            root.destroy()
            log_debug_event("Application shutdown completed.")
            sys.exit()
        except Exception as e:
            log_debug_event(f"Shutdown failed: {e}")


def open_manage_projects(projects):
    global open_window

    if not handle_window_request("manage"):
        return

    log_debug_event("Manage Projects window opened.")

    manage_win = tk.Toplevel(popup)
    manage_win.title("Manage Projects")
    # manage_win.geometry("300x400")
    manage_win.configure(bg=manproj_win_bg)
    manage_win.attributes("-topmost", True)
    open_window = manage_win
    manage_win.geometry(offset_position_near_popup())

    tk.Label(manage_win, text="Edit Project Names:", font=("Arial", 14), bg=manproj_win_bg).pack(pady=5)
    entry_frame = tk.Frame(manage_win, bg=manproj_win_bg)
    entry_frame.pack(fill="both", expand=True, padx=10)

    project_vars = []
    
    def add_row(name=""):
        row = tk.Frame(entry_frame, bg=manproj_win_bg)
        row.pack(fill="x", pady=2)

        var = tk.StringVar(value=name)
        entry = tk.Entry(row, textvariable=var, width=30)
        entry.pack(side="left", fill="x", expand=True)

        btn = tk.Button(row, text="❌", command=lambda: remove_row(row, var))
        btn.pack(side="left", padx=5)
        project_vars.append(var)

        # Resize window after adding row
        manage_win.update_idletasks()
        new_height = manage_win.winfo_reqheight() + 20
        manage_win.geometry(f"300x{new_height}")

    def remove_row(row_widget, var):
        project_vars.remove(var)
        row_widget.destroy()

        manage_win.update_idletasks()
        new_height = manage_win.winfo_reqheight() + 20
        manage_win.geometry(f"300x{new_height}")

    for name in projects:
        add_row(name)

    def save_and_close():
        new_projects = [var.get().strip() for var in project_vars if var.get().strip()]
        if new_projects:
            save_projects(new_projects)
            log_debug_event(f"Saved updated project list: {new_projects}")
            manage_win.destroy()
            popup.destroy()
            show_popup(new_projects)
        else:
            log_debug_event("Attempted to save empty project list. Ignored.")

    tk.Button(manage_win, text="Add Project", command=lambda: add_row("")).pack(pady=5)
    tk.Button(manage_win, text="Save Changes", command=save_and_close, bg="green", fg="white").pack(pady=10)

    manage_win.update_idletasks()
    height = manage_win.winfo_reqheight() + 20  # Add padding
    manage_win.geometry(f"300x{height}")


def show_summary_window():
    global open_window

    if not handle_window_request("summary"):
        return

    log_debug_event("Summary window opened.")
    all_sessions = load_sessions()

    # Include active session duration as of now
    now = datetime.now()
    if sessions and sessions[-1].duration is None:
        active = sessions[-1]
        active_duration = (now - active.start_time).total_seconds()
        all_sessions.append(Session(active.project, active.start_time, active_duration))
        log_debug_event(f"Added active session to summary: {active.project} +{active_duration:.0f}s")

    if not all_sessions:
        tk.messagebox.showinfo("No Data", "No session data found.")
        return

    # Build DataFrame
    rows = [
        {"Date": s.start_time.date(), "Project": s.project, "Hours": s.duration / 3600}
        for s in all_sessions if s.duration
    ]
    if not rows:
        tk.messagebox.showinfo("No Data", "No completed sessions available.")
        return

    df = pd.DataFrame(rows)
    summary = df.pivot_table(
        index="Project", columns="Date", values="Hours",
        aggfunc="sum", fill_value=0
    ).sort_index(axis=1)

    summary = summary.round(2)

    dates = summary.columns
    projects = summary.index.tolist()

    # Create summary window
    summary_win = tk.Toplevel(popup)
    summary_win.title("Work Summary")
    summary_win.configure(bg=summary_win_bg)
    summary_win.attributes("-topmost", True)
    open_window = summary_win
    summary_win.geometry(offset_position_near_popup())


    # === Scrollable Canvas Setup ===
    canvas = tk.Canvas(summary_win, bg=summary_win_bg, height=400)
    h_scroll = tk.Scrollbar(summary_win, orient="horizontal", command=canvas.xview)
    canvas.configure(xscrollcommand=h_scroll.set)

    h_scroll.pack(side="bottom", fill="x")
    canvas.pack(side="top", fill="both", expand=True)

    table_frame = tk.Frame(canvas, bg=summary_win_bg)
    canvas.create_window((0, 0), window=table_frame, anchor="nw")

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    table_frame.bind("<Configure>", on_frame_configure)

    # === Table Header ===
    tk.Label(table_frame, text="Project", font=("Arial", 10, "bold"), bg=summary_win_bg).grid(row=0, column=0, padx=4, pady=2)
    for c, d in enumerate(dates, start=1):
        tk.Label(table_frame, text=d.strftime("%a %d %b"), font=("Arial", 10, "bold"), bg=summary_win_bg)\
            .grid(row=0, column=c, padx=4, pady=2)

    # === Table Body ===
    for r, proj in enumerate(projects, start=1):
        tk.Label(table_frame, text=proj, font=("Arial", 10, "bold"), bg=summary_win_bg)\
            .grid(row=r, column=0, sticky="w", padx=4)
        for c, d in enumerate(dates, start=1):
            val = summary.loc[proj, d]
            tk.Label(table_frame, text=f"{val:.2f}", bg="white", width=10)\
                .grid(row=r, column=c, padx=1, pady=1)

    # === Totals ===
    total_all = summary.sum()
    tk.Label(table_frame, text="TOTAL", font=("Arial", 10, "bold"), bg="#e0e0e0")\
        .grid(row=r+1, column=0, sticky="w", padx=4)
    for c, d in enumerate(dates, start=1):
        tk.Label(table_frame, text=f"{total_all[d]:.2f}", bg="#e0e0e0", width=10)\
            .grid(row=r+1, column=c, padx=1, pady=1)

    if 'Break' in summary.index:
        no_break = summary.drop('Break')
    else:
        no_break = summary
    total_no_break = no_break.sum()

    tk.Label(table_frame, text="TOTAL (excl Breaks)", font=("Arial", 10, "bold"), bg="#d0ffd0")\
        .grid(row=r+2, column=0, sticky="w", padx=4)
    for c, d in enumerate(dates, start=1):
        tk.Label(table_frame, text=f"{total_no_break[d]:.2f}", bg="#d0ffd0", width=10)\
            .grid(row=r+2, column=c, padx=1, pady=1)

    # === Delete Button INSIDE table_frame ===
    def delete_past_entries():
        answer = askokcancel('Confirmation', 'Are you sure?  This will delete all past log entries up to and including yesterday!', icon=WARNING, parent=summary_win)
        if answer:
            today = date.today()
            updated = [s for s in all_sessions if s.start_time.date() == today]
            overwrite_sessions(updated)
            log_debug_event("Deleted past session entries.")
            summary_win.destroy()
            show_summary_window()

    del_btn = tk.Button(
        table_frame, text="Delete Past Entries", command=delete_past_entries,
        fg="white", bg="red", font=("Arial", 10, "bold")
    )
    del_btn.grid(row=r+3, column=0, columnspan=len(dates)+1, pady=(15, 5))

    # === Final Resize ===
    summary_win.update_idletasks()
    summary_win.geometry("")  # Let the window auto-size cleanly to its contents


def open_edit_log_window():
    global open_window

    if not handle_window_request("edit_log"):
        return

    log_debug_event("Edit Today's Log window opened.")
    today = date.today()

    now = datetime.now()
    day_sessions = []

    for s in sessions:
        if s.start_time.date() == today:
            if s.duration is not None:
                day_sessions.append(s)
            else:
                # Active session: simulate duration
                active_duration = (now - s.start_time).total_seconds()
                day_sessions.append(Session(s.project, s.start_time, active_duration))
                log_debug_event(f"Included active session in Edit Log: {s.project} +{active_duration:.0f}s")

    # Totals per project
    totals = {}
    for s in day_sessions:
        totals[s.project] = totals.get(s.project, 0) + s.duration

    if not totals:
        tk.messagebox.showinfo("No data", "No logged sessions for today.")
        return

    edit_win = tk.Toplevel(popup)
    edit_win.title("Edit Today's Log")
    edit_win.geometry("")
    edit_win.configure(bg=edit_win_bg)
    edit_win.attributes("-topmost", True)
    open_window = edit_win
    edit_win.geometry(offset_position_near_popup())

    tk.Label(edit_win, text="Edit Today's Log", bg=edit_win_bg, font=("Arial", 14, "bold")).pack(pady=(10, 5))
    tk.Label(edit_win, text="Time booked today:", bg=edit_win_bg, font=("Arial", 10)).pack(pady=(10, 5))

    table_frame = tk.Frame(edit_win, bg=edit_win_bg)  # black grid lines
    table_frame.pack(padx=5, pady=5)

    # Header row with grid
    tk.Label(table_frame, text="Project", bg="white", font=("Arial", 10, "bold"), width=20, anchor="c", relief="solid", borderwidth=1)\
        .grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
    tk.Label(table_frame, text="Hours", bg="white", font=("Arial", 10, "bold"), width=10, anchor="c", relief="solid", borderwidth=1)\
        .grid(row=0, column=1, sticky="nsew", padx=1, pady=1)

    # Data rows
    for row_idx, (proj, secs) in enumerate(totals.items(), start=1):
        hours = secs / 3600
        tk.Label(table_frame, text=proj, bg="white", anchor="c", relief="solid", borderwidth=1)\
            .grid(row=row_idx, column=0, sticky="nsew", padx=1, pady=1)
        tk.Label(table_frame, text=f"{hours:.2f}", bg="white", anchor="c", relief="solid", borderwidth=1)\
            .grid(row=row_idx, column=1, sticky="nsew", padx=1, pady=1)

    # FROM project
    tk.Label(edit_win, text="Move Time FROM:", bg=edit_win_bg).pack()
    from_var = tk.StringVar()
    from_menu = ttk.Combobox(edit_win, textvariable=from_var, values=list(totals.keys()), state="readonly")
    from_menu.pack()

    # TO project
    tk.Label(edit_win, text="Move Time TO:", bg=edit_win_bg).pack()
    to_var = tk.StringVar()
    all_projects = load_projects()
    to_menu = ttk.Combobox(edit_win, textvariable=to_var, values=all_projects, state="readonly")
    to_menu.pack()

    # Amount to move
    tk.Label(edit_win, text="Hours to move:", bg=edit_win_bg).pack()
    hours_var = tk.StringVar()
    tk.Entry(edit_win, textvariable=hours_var).pack(pady=5)

    msg_label = tk.Label(edit_win, text="", fg="red", bg=edit_win_bg)
    msg_label.pack()

    edit_win.update_idletasks()

    def apply_adjustment():
        global sessions

        # Finalize and save active session before editing
        finalized = finalize_sessions(sessions)
        new_finalized = [s for s in finalized if s.duration is not None]
        if new_finalized:
            save_sessions(new_finalized)
            log_debug_event(f"Auto-saved active session(s) before adjustment: {[s.project for s in new_finalized]}")
        sessions = finalized
        
        try:
            hrs = float(hours_var.get())
            if hrs <= 0:
                raise ValueError()
        except ValueError:
            msg_label.config(text="Enter a valid number > 0.")
            return

        from_proj = from_var.get()
        to_proj = to_var.get()

        if from_proj == to_proj:
            msg_label.config(text="Projects must be different.")
            return

        available = totals.get(from_proj, 0) / 3600
        if hrs > available:
            msg_label.config(text=f"Only {available:.2f} hrs in '{from_proj}'.")
            return

        # Apply adjustment by appending sessions
        seconds = hrs * 3600
        now = datetime.now()
        
        new_adjustments = [Session(from_proj, now, -seconds), Session(to_proj, now, seconds)]
        save_sessions(new_adjustments)
        sessions.extend(new_adjustments)

        log_debug_event(f"Moved {hrs:.2f} hrs from {from_proj} to {to_proj} for today.")

        # Restart the session on the same project (if one was active before applying an edit)
        if new_finalized:
            last_project = new_finalized[-1].project
            from tracker import switch_project
            sessions = switch_project(sessions, last_project)
            log_debug_event(f"Restarted session for {last_project} after edit.")

        edit_win.destroy()
        # Reload sessions from disk
        persisted_sessions = load_sessions(for_date=date.today())

        # If a new session was just restarted in memory, keep it
        if sessions and sessions[-1].duration is None:
            persisted_sessions.append(sessions[-1])

        sessions = persisted_sessions
        show_popup(load_projects())

    # Buttons
    btn_frame = tk.Frame(edit_win, bg=edit_win_bg)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Apply", command=apply_adjustment, width=10).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="Cancel", command=edit_win.destroy, width=10).grid(row=0, column=1, padx=5)


def show_popup(projects, reschedule_callback=None):
    main_win_bg = "#61C4E9"
    global popup, status_label, interval_var, project_buttons, total_time_label

    log_debug_event("Popup displayed.")

    if not popup or not popup.winfo_exists():
        popup = tk.Toplevel(root)
        popup.title("Time Tracker")
        popup.configure(bg=main_win_bg)
        popup.protocol("WM_DELETE_WINDOW", popup.iconify)

    popup.deiconify()
    popup.attributes('-topmost', True)
    for widget in popup.winfo_children():
        widget.destroy()

    tk.Label(popup, text="What are you working on?", font=("Arial", 16), bg=main_win_bg).pack(pady=5)

    now = datetime.now()
    status = f"Last logged: {current_project + ' at ' + now.strftime('%H:%M:%S') if current_project else '-'}"


    status_label = tk.Label(popup, text=status, font=("Arial", 10), bg=main_win_bg)
    status_label.pack(pady=5)

    button_frame = tk.Frame(popup, bg=main_win_bg)
    button_frame.pack(pady=10)

    project_buttons.clear()
    project_time_labels.clear()

    for project in projects:
        row = tk.Frame(button_frame, bg=main_win_bg)
        row.pack(pady=3)

        btn = tk.Button(
            row, text=project,
            width=25, height=2,
            bg="#00FF00" if project == current_project else "#f0f0f0",
            command=lambda p=project: on_project_click(p, reschedule_callback)
        )
        btn.pack(side="left")

        time_lbl = tk.Label(row, text="00:00:00", font=("Arial", 10), bg=main_win_bg)
        time_lbl.pack(side="left", padx=10)

        project_buttons[project] = btn
        project_time_labels[project] = time_lbl

    total_time_label = tk.Label(popup, text="Total time logged today: 00:00:00", font=("Arial", 12), bg=main_win_bg)
    total_time_label.pack(pady=10)

    # 2x2 button grid
    button_frame = tk.Frame(popup, bg=main_win_bg)
    button_frame.pack(pady=15)

    button_width = 15
    button_height = 1
    button_font = ("Arial", 10)
    button_bg = "#dddddd"

    # Top-left: Manage Projects
    tk.Button(button_frame, text="Manage Projects", command=lambda: open_manage_projects(load_projects()), bg=button_bg, width=button_width, height=button_height, font = button_font)\
        .grid(row=0, column=0, padx=5, pady=5)

    # Top-right: View Summary
    tk.Button(button_frame, text="View Summary", command=show_summary_window, bg=button_bg, width=button_width, height=button_height, font = button_font)\
        .grid(row=0, column=1, padx=5, pady=5)

    # Bottom-left: Edit Today's Log
    tk.Button(button_frame, text="Edit Today's Log", command=open_edit_log_window, bg=button_bg, width=button_width, height=button_height, font = button_font)\
        .grid(row=1, column=0, padx=5, pady=5)

    # Bottom-right: End Workday
    tk.Button(button_frame, text="End Workday", command=end_workday, bg="red", fg="white", width=button_width, height=button_height, font = button_font)\
        .grid(row=1, column=1, padx=5, pady=5)

    # Interval dropdown (label + menu on same row)
    interval_frame = tk.Frame(popup, bg=main_win_bg)
    interval_frame.pack(pady=15)

    tk.Label(interval_frame, text="Ask me again in:", font=("Arial", 10), bg=main_win_bg)\
        .pack(side="left", padx=(0, 8))

    interval_var = tk.StringVar(value=selected_interval)
    option_menu = ttk.OptionMenu(
        interval_frame, interval_var, selected_interval, *INTERVAL_OPTIONS.keys(),
        command=lambda new_value: on_interval_change(new_value, reschedule_callback)
    )
    option_menu.pack(side="left")

    update_ui()
    popup.update_idletasks()
    width = 320
    height = popup.winfo_reqheight()
    popup.geometry(f"{width}x{height}")


def on_project_click(project, reschedule_callback=None):
    global sessions, current_project
    now = datetime.now()
    log_debug_event(f"Project clicked: {project} at {now.strftime('%H:%M:%S')}")

    # Count how many sessions are finalized before switch
    pre_finalized = [s for s in sessions if s.duration is not None]

    # Switch to the new project (this may finalize one session and append one)
    sessions = switch_project(sessions, project)

    # Compare finalized sessions after switching
    post_finalized = [s for s in sessions if s.duration is not None]
    if len(post_finalized) > len(pre_finalized):
        new_finalized = post_finalized[len(pre_finalized):]
        save_sessions(new_finalized)
        log_debug_event(f"Saved {len(new_finalized)} finalized session(s): {[s.project for s in new_finalized]}")
    else:
        log_debug_event("No finalized session — nothing written.")

    current_project = project
    if status_label:
        status_label.config(text=f"Last logged: {current_project} at {now.strftime('%H:%M:%S')}")

    if reschedule_callback:
        reschedule_callback()

    for proj, btn in project_buttons.items():
        btn.config(bg="#00FF00" if proj == project else "#f0f0f0")

    popup.iconify()


def on_interval_change(new_value, reschedule_callback=None):
    global INTERVAL, selected_interval
    selected_interval = new_value
    INTERVAL = INTERVAL_OPTIONS.get(selected_interval, INTERVAL_OPTIONS[DEFAULT_INTERVAL])
    log_debug_event(f"Interval changed to {selected_interval}")
    if reschedule_callback:
        reschedule_callback(selected_interval)


def update_ui():
    global update_ui_handle
    totals = compute_totals(sessions)
    total_all = sum(totals.values())

    for project, label in project_time_labels.items():
        label.config(text=format_seconds(totals.get(project, 0)))

    if total_time_label:
        total_time_label.config(text=f"Total time logged today: {format_seconds(total_all)}", font=("Arial", 10))

    update_ui_handle = popup.after(1000, update_ui)
