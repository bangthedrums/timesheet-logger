# config.py
import os

BASE_DIR = os.path.dirname(__file__)
LOG_FILE = os.path.join(BASE_DIR, "timesheetLogEntries.csv")
SESSION_FILE = os.path.join(BASE_DIR, "sessionLog.csv")
CONFIG_FILE = os.path.join(BASE_DIR, "projectConfig.csv")
DEBUG_LOG_FILE = os.path.join(BASE_DIR, "debug_logfile.txt")

INTERVAL_OPTIONS = {
    # "10 secs": 10 * 1000,
    "5 mins": 5 * 60 * 1000,
    "15 mins": 15 * 60 * 1000,
    "30 mins": 30 * 60 * 1000,
    "1 hour": 1 * 60 * 60 * 1000,
    "2 hours": 2 * 60 * 60 * 1000,
    "4 hours": 4 * 60 * 60 * 1000
}
DEFAULT_INTERVAL = "15 mins"
