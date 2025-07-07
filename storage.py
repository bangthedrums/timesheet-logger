# storage.py
import csv
import os
from datetime import datetime, date
from typing import List, Optional
from models import Session
from config import SESSION_FILE, CONFIG_FILE


def save_sessions(new_sessions: List[Session]):
    file_exists = os.path.exists(SESSION_FILE)
    with open(SESSION_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Project", "Start", "Duration"])
        for s in new_sessions:
            if s.duration is None:
                continue  # Skip unfinished sessions
            writer.writerow([
                s.project,
                s.start_time.isoformat(),
                s.duration if s.duration is not None else ""
            ])


def overwrite_sessions(all_sessions: List[Session]):
    with open(SESSION_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Project", "Start", "Duration"])
        for s in all_sessions:
            writer.writerow([
                s.project,
                s.start_time.isoformat(),
                s.duration if s.duration is not None else ""
            ])


def load_projects():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return ["Project A", "Project B", "Break"]


def save_projects(projects: list[str]):
    with open(CONFIG_FILE, "w", newline="") as f:
        f.write("\n".join(projects))


def load_sessions(for_date: Optional[date] = None) -> List[Session]:
    sessions = []
    try:
        with open(SESSION_FILE, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                project = row['Project']
                start = datetime.fromisoformat(row['Start'])
                duration = float(row['Duration']) if row['Duration'] else None

                if for_date is None or start.date() == for_date:
                    sessions.append(Session(project, start, duration))
    except FileNotFoundError:
        pass
    return sessions

