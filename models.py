# models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Session:
    project: str
    start_time: datetime
    duration: Optional[float] = None  # duration in seconds


@dataclass
class Adjustment:
    from_project: str
    to_project: str
    seconds: float
