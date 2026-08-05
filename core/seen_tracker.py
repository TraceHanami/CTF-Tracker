"""core/seen_tracker.py — Track which events have been notified."""
from __future__ import annotations
import json
from pathlib import Path

import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", "/tmp/data" if os.environ.get("VERCEL") else BASE_DIR / "data"))
SEEN_FILE = DATA_DIR / "seen.json"


def _load() -> set[str]:
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text()))
        except Exception:
            pass
    return set()


def _save(seen: set[str]) -> None:
    try:
        SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        SEEN_FILE.write_text(json.dumps(sorted(seen), indent=2))
    except Exception:
        pass


def filter_new(events: list[dict]) -> list[dict]:
    seen = _load()
    return [e for e in events if e.get("url", "") not in seen]


def mark_seen(events: list[dict]) -> None:
    seen = _load()
    for e in events:
        url = e.get("url", "")
        if url:
            seen.add(url)
    _save(seen)
