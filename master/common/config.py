"""
Common configuration for the MASTER project
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

LOG_LEVEL_TAGS = [
    "DEBUG",
    "INFO",
    "SUCCESS",
    "WARNING",
    "ERROR",
    "CRITICAL",
    "PROGRESS",
    "COMPLETE",
]