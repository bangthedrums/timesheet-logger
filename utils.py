# utils.py
import os
import logging
from datetime import timedelta
from config import DEBUG_LOG_FILE


# Configure the debug logger
logging.basicConfig(
    filename=DEBUG_LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def log_debug_event(msg: str):
    logging.info(msg)


def format_seconds(seconds: float) -> str:
    """Formats a float of seconds to HH:MM:SS."""
    return str(timedelta(seconds=int(seconds)))
