"""Pytest bootstrap helpers shared across the repository tests."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    # Keep imports stable regardless of how pytest is launched locally.
    sys.path.insert(0, str(ROOT))
