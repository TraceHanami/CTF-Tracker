"""scrapers/devfolio.py — Hackathons from Devfolio public API."""
from __future__ import annotations
from bs4 import BeautifulSoup
from core.utils import get_logger, safe_get, parse_date, throttle

logger = get_logger("scrapers.devfolio")
BASE = "https://devfolio.co"

API_URLS = [
    "https://api.devfolio.co/api/hackathons?type=upcoming&page=1&per_page=50",
    "https://api.devfolio.co/api/hackathons?type=open&page=1&per_page=50",
    "https://api.devfolio.co/api/hackathons?type=upcoming&page=2&per_page=50",
]


def _parse_item(h: dict) -> dict | None:
    slug  = h.get("slug", "")
    title = h.get("name") or h.get("title") or ""
    if not title:
        return None

    starts = h.get("starts_at") or h.get("start_date") or ""
    ends   = h.get("ends_at")   or h.get("end_date")   or ""
    loc    = h.get("city") or h.get("location") or "Online"
    is_online = bool(h.get("is_online", True)) or "online" in str(loc).lower() or not loc

    min_t = h.get("min_team_size") or 1
    max_t = h.get("max_team_size") or 4
    team_size = f"{min_t}–{max_t} members"
    url = f"{BASE}/hackathons/{slug}" if slug else BASE + "/hackathons"

    return {
        "source":      "Devfolio",
        "type":        "Hackathon",
        "event_type":  "Hackathon",
        "title":       title,
        "url":         url,
        "date":        parse_date(str(starts)),
        "end_date":    parse_date(str(ends)),
        "location":    str(loc) if loc else "Online",
        "online":      is_online,
        "mode":        "Online" if is_online else "Offline",
        "format":      "Hackathon",
        "fee":         "free",
        "price":       0,
        "team_size":   team_size,
        "organizer":   h.get("organization_name", "Devfolio"),
        "description": h.get("tagline") or h.get("description") or "",
        "registration_link": url,
    }


def get_devfolio_events() -> list[dict]:
    events: list[dict] = []
    seen: set[str] = set()

    for api_url in API_URLS[:1]:   # First page returns 1000 items
        resp = safe_get(api_url, timeout=8)
        if not resp:
            throttle(1.0)
            continue
        try:
            data = resp.json()
            items = data if isinstance(data, list) else (data.get("result") or data.get("results") or data.get("hackathons") or [])
            for h in items:
                parsed = _parse_item(h)
                if parsed and parsed["url"] not in seen:
                    seen.add(parsed["url"])
                    events.append(parsed)
        except Exception as exc:
            logger.warning("Devfolio parse error: %s", exc)
        throttle(0.8)

    logger.info("Devfolio: %d events", len(events))
    return events
