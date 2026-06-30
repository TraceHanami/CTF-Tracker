"""scrapers/devpost.py — Real hackathons from Devpost public API."""
from __future__ import annotations
import re
from core.utils import get_logger, safe_get, parse_date, throttle

logger = get_logger("scrapers.devpost")
BASE = "https://devpost.com"
API_URL = "https://devpost.com/api/hackathons"


def _fetch_page(page: int) -> list[dict]:
    params = {
        "status[]": "upcoming",
        "challenge_type[]": "hackathon",
        "order_by": "deadline",
        "page": page,
    }
    resp = safe_get(API_URL, params=params, timeout=25)
    if not resp:
        return []
    try:
        return resp.json().get("hackathons", [])
    except Exception:
        return []


def _parse(h: dict) -> dict | None:
    title = h.get("title", "").strip()
    if not title:
        return None

    # Only free events
    if (h.get("registration_fee_cents") or 0) > 0:
        return None

    url = h.get("url") or BASE + "/hackathons"
    loc = h.get("location") or "Online"
    is_online = bool(h.get("online_only", True)) or "online" in str(loc).lower()

    # Parse submission period "March 01 – April 30, 2025"
    period = h.get("submission_period_dates", "") or ""
    date_str, end_str = "TBD", "TBD"
    if period:
        m = re.search(r"(\w+ \d+).*?(\w+ \d+),?\s*(\d{4})", period)
        if m:
            date_str = parse_date(f"{m.group(1)}, {m.group(3)}")
            end_str  = parse_date(f"{m.group(2)}, {m.group(3)}")
        else:
            date_str = parse_date(period[:20])

    min_t = h.get("minimum_members_per_team") or 1
    max_t = h.get("maximum_members_per_team") or 4
    organizer = ""
    if h.get("organizations"):
        organizer = h["organizations"][0].get("name", "")

    return {
        "source":      "Devpost",
        "type":        "Hackathon",
        "event_type":  "Hackathon",
        "title":       title,
        "url":         url,
        "date":        date_str,
        "end_date":    end_str,
        "location":    str(loc),
        "online":      is_online,
        "mode":        "Online" if is_online else "Offline",
        "format":      "Hackathon",
        "fee":         "free",
        "price":       0,
        "team_size":   f"{min_t}–{max_t} members",
        "organizer":   organizer,
        "description": h.get("tagline") or h.get("description") or "",
        "participants": h.get("registrations_count", 0),
        "registration_link": url,
    }


def get_devpost_events() -> list[dict]:
    events: list[dict] = []
    seen: set[str] = set()

    for page in range(1, 5):   # fetch up to 4 pages ≈ 100 events
        items = _fetch_page(page)
        if not items:
            break
        for h in items:
            parsed = _parse(h)
            if parsed and parsed["url"] not in seen:
                seen.add(parsed["url"])
                events.append(parsed)
        throttle(0.8)

    logger.info("Devpost: %d free events", len(events))
    return events
