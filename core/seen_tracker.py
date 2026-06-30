"""core/seen_tracker.py — Track which events have been notified."""
from __future__ import annotations
import json
from pathlib import Path

SEEN_FILE = Path("data/seen.json")


def _load() -> set[str]:
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text()))
        except Exception:
            pass
    return set()


def _save(seen: set[str]) -> None:
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(json.dumps(sorted(seen), indent=2))


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
