# Timesheet Logger

**Timesheet Logger** is a lightweight desktop application for tracking time spent on various projects throughout the workday. It provides an intuitive GUI popup at scheduled intervals to prompt users to log their current task. The tool supports daily summaries, project management, and fine-tuned log editing, all stored in local CSV files for easy backup or analysis.

---

## Features

- Quick popup prompts at customizable intervals
- Track time across multiple projects
- Daily and cross-day time summaries
- Visual log editor for adjusting or correcting entries
- Simple project manager
- Designed for Windows desktop environments

---

## Installation & Running

### Prerequisites

- Python 3.8+
- Required packages (install with pip):

```bash
pip install pandas
```

### Running the App

Launch the application via:

```bash
python launch.pyw
```

> `launch.pyw` runs the application silently without a command window on Windows.

---

## Auto-Start on Windows

To run the app automatically on system startup:

1. Press `Win + R`, type `shell:startup`, and press Enter.
2. In the folder that opens, create a shortcut to the `launch.pyw` file.
3. That's it! The app will now run when your computer starts.

---

## User Guide

### Main Popup Window

The main window is titled **"Time Tracker"** and displays every `N` minutes (default: 15 mins). You can choose your current task with a single click.

#### Elements:

- **Project Buttons**: Click to start tracking a new project. The previously tracked task is automatically closed.
- **Time Labels**: Shows how much time you've logged for each project today.
- **Status Label**: Shows the last project logged.
- **Dropdown ("Ask me again in:")**: Changes how frequently the popup reappears.
- **Total Time Logged Today**: Summarizes total hours for the day.
- **GUI Buttons**:
  - `Manage Projects`: Open the project manager.
  - `View Summary`: View a grid of hours logged across all days and projects.
  - `Edit Today's Log`: Adjust time logged between projects.
  - `End Workday`: Finalizes all logs and closes the app.

---

## Popup Windows

### Manage Projects

- Allows editing the list of tracked project names.
- You can add, rename, or remove projects.
- Changes are saved in `projectConfig.csv`.

### View Summary

- Displays a scrollable table of hours per project, per day.
- Totals per day and optionally excluding "Break" time.
- Includes a button to delete all past sessions (retaining only today's data).

### Edit Today's Log

- Shows a table of today's logged time per project.
- Lets you **move hours** between projects for correction.
- Includes:
  - `From` project dropdown
  - `To` project dropdown
  - Hours to move
  - Apply/Cancel buttons

---

## Data Files

The app stores its data locally in the same folder:

- `sessionLog.csv` — logged session data.
- `projectConfig.csv` — list of current project names.
- `debug_logfile.txt` — internal debug messages for development.

---

## License

See the included [LICENSE](./LICENSE) file for details.
