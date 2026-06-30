"""scrapers/ctftime.py — Real CTF events from CTFtime.org public API."""
from __future__ import annotations
from core.utils import get_logger, safe_get, window_timestamps, parse_date

logger = get_logger("scrapers.ctftime")
API_URL = "https://ctftime.org/api/v1/events/"


def get_ctf_events() -> list[dict]:
    start, finish = window_timestamps(months=6)
    resp = safe_get(
        API_URL,
        params={"limit": 200, "start": start, "finish": finish},
        timeout=20,
    )
    if resp is None:
        return []
    try:
        raw = resp.json()
    except ValueError:
        logger.warning("CTFtime: invalid JSON")
        return []

    events: list[dict] = []
    for e in raw:
        # Skip events that explicitly mention paid entry
        prizes = str(e.get("prizes", "")).lower()
        if "paid" in prizes or "entry fee" in prizes:
            continue

        location_raw = e.get("location", "") or ""
        # onsite=True means it is a physical event
        onsite = e.get("onsite", False)
        is_online = (not onsite) or ("online" in location_raw.lower()) or (not location_raw)
        location  = location_raw if location_raw else "Online"

        event_id  = e.get("id", "")
        ctf_url   = e.get("url") or f"https://ctftime.org/event/{event_id}"
        ctftime_url = f"https://ctftime.org/event/{event_id}"

        format_str = e.get("format", "")
        weight     = float(e.get("weight", 0) or 0)

        events.append({
            "source":       "CTFtime",
            "type":         "CTF",
            "event_type":   "CTF",
            "title":        e.get("title", "Unknown CTF"),
            "url":          ctf_url,
            "ctftime_url":  ctftime_url,
            "date":         parse_date(e.get("start", "")),
            "end_date":     parse_date(e.get("finish", "")),
            "location":     location,
            "online":       is_online,
            "mode":         "Online" if is_online else "Offline",
            "format":       format_str,
            "weight":       weight,
            "fee":          "free",
            "price":        0,
            "team_size":    "Individual / Team",
            "participants": e.get("participants", 0),
            "organizer":    e.get("organizers", [{}])[0].get("name", "Unknown") if e.get("organizers") else "Unknown",
            "description":  e.get("description", ""),
            "registration_link": ctf_url,
        })

    logger.info("CTFtime: %d events fetched", len(events))
    return events
