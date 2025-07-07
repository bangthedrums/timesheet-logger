# tracker.py
from datetime import datetime
from typing import List, Dict
from models import Session


def finalize_sessions(sessions: List[Session]) -> List[Session]:
    now = datetime.now()
    finalized = []
    for s in sessions:
        if s.duration is None:
            s.duration = (now - s.start_time).total_seconds()
            finalized.append(s)
    return finalized


def switch_project(sessions: List[Session], new_project: str) -> List[Session]:
    now = datetime.now()

    # Sanitize: drop any existing unfinalized sessions before switching
    finalized_sessions = []
    for s in sessions:
        if s.duration is None:
            s.duration = (now - s.start_time).total_seconds()
        finalized_sessions.append(s)

    # Append the new session
    finalized_sessions.append(Session(new_project, now, None))
    return finalized_sessions




def compute_totals(sessions: List[Session]) -> Dict[str, float]:
    now = datetime.now()
    totals = {}
    for s in sessions:
        dur = s.duration if s.duration is not None else (now - s.start_time).total_seconds()
        totals[s.project] = totals.get(s.project, 0) + dur
    return totals
