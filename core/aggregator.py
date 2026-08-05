"""core/aggregator.py — Scrape all sources, deduplicate, and sort."""
from __future__ import annotations
import json
import hashlib
from pathlib import Path
from datetime import datetime

from core.filters import apply_all
from core.utils import get_logger

logger = get_logger("aggregator")

import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", "/tmp/data" if os.environ.get("VERCEL") else BASE_DIR / "data"))
try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    DATA_DIR = Path("/tmp/data")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

EVENTS_FILE = DATA_DIR / "events.json"


def _fingerprint(event: dict) -> str:
    """Create a stable dedup key from title + date + source."""
    raw = f"{event.get('title','').lower().strip()}|{event.get('date','TBD')}|{event.get('source','').lower()}"
    return hashlib.md5(raw.encode()).hexdigest()


def _deduplicate(events: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    # Also deduplicate by URL
    seen_urls: set[str] = set()
    for e in events:
        fp = _fingerprint(e)
        url = e.get("url", "")
        if fp in seen:
            continue
        if url and url in seen_urls:
            continue
        seen.add(fp)
        if url:
            seen_urls.add(url)
        out.append(e)
    return out


def _sort_events(events: list[dict]) -> list[dict]:
    def sort_key(e):
        d = e.get("date", "9999-99-99")
        return d if d not in ("TBD", "", "unknown") else "9999-99-99"
    return sorted(events, key=sort_key)


def _enrich(events: list[dict]) -> list[dict]:
    """Add computed fields useful for UI display."""
    now_str = datetime.utcnow().strftime("%Y-%m-%d")
    for e in events:
        # Mode label
        if e.get("online"):
            e.setdefault("mode", "Online")
        else:
            e.setdefault("mode", "Offline")

        # Days until
        try:
            d = datetime.strptime(e["date"], "%Y-%m-%d")
            delta = (d - datetime.utcnow()).days
            e["days_until"] = delta
            if delta == 0:
                e["urgency"] = "today"
            elif delta <= 7:
                e["urgency"] = "this_week"
            elif delta <= 30:
                e["urgency"] = "this_month"
            else:
                e["urgency"] = "upcoming"
        except Exception:
            e["days_until"] = 999
            e["urgency"] = "upcoming"

        # Normalize fee
        e.setdefault("fee", "free")
        e.setdefault("team_size", "—")
        e.setdefault("description", "")
        e.setdefault("location", "Online" if e.get("online") else "TBD")

    return events


def aggregate(save: bool = True) -> list[dict]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    from scrapers.ctftime import get_ctf_events
    from scrapers.devfolio import get_devfolio_events
    from scrapers.unstop import get_unstop_events
    from scrapers.hackerearth import get_hackerearth_events
    from scrapers.mlh import get_mlh_events
    from scrapers.devpost import get_devpost_events

    scrapers = [
        ("CTFtime",     get_ctf_events),
        ("Devfolio",    get_devfolio_events),
        ("Unstop",      get_unstop_events),
        ("HackerEarth", get_hackerearth_events),
        ("MLH",         get_mlh_events),
        ("Devpost",     get_devpost_events),
    ]

    all_raw: list[dict] = []
    for name, fn in scrapers:
        try:
            results = fn()
            logger.info("%s → %d raw events", name, len(results))
            all_raw.extend(results)
        except Exception as e:
            logger.error("%s scraper failed: %s", name, e)

    filtered = apply_all(all_raw)
    deduped   = _deduplicate(filtered)
    sorted_   = _sort_events(deduped)
    enriched  = _enrich(sorted_)

    logger.info("Aggregate: raw=%d filtered=%d deduped=%d",
                len(all_raw), len(filtered), len(enriched))

    if save:
        with open(EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(enriched, f, ensure_ascii=False, indent=2)

    return enriched
