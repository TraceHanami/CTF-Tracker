"""scrapers/unstop.py — Hackathons from Unstop public API."""
from __future__ import annotations
from core.utils import get_logger, safe_get, parse_date, throttle

logger = get_logger("scrapers.unstop")
BASE = "https://unstop.com"

# Unstop search API — free, online+india
API_PAGES = [
    f"{BASE}/api/public/opportunity/search-result?opportunity=hackathons&filters[0][type]=location&filters[0][value]=online&per_page=30&page={p}"
    for p in range(1, 4)
]


def _parse(e: dict) -> dict | None:
    title = e.get("title") or e.get("name") or ""
    if not title:
        return None

    fee_raw = str(e.get("registration_fees", "0")).strip()
    if fee_raw not in ("0", "", "Free", "free", "null", "None"):
        try:
            if float(fee_raw) > 0:
                return None
        except ValueError:
            pass

    uid   = e.get("id", "")
    slug  = e.get("seo_url", "") or str(uid)
    url   = f"{BASE}/{slug}" if slug else f"{BASE}/hackathons"
    loc   = e.get("city") or e.get("location") or "Online"
    is_online = (e.get("opportunity_type", "") == "online"
                 or "online" in str(loc).lower())

    starts = e.get("start_date") or e.get("starts_at") or ""
    ends   = e.get("end_date")   or e.get("ends_at")   or ""

    min_t = e.get("min_team_size") or 1
    max_t = e.get("max_team_size") or 4

    return {
        "source":      "Unstop",
        "type":        "Hackathon",
        "event_type":  "Hackathon",
        "title":       title,
        "url":         url,
        "date":        parse_date(str(starts)),
        "end_date":    parse_date(str(ends)),
        "location":    str(loc),
        "online":      is_online,
        "mode":        "Online" if is_online else "Offline",
        "format":      "Hackathon",
        "fee":         "free",
        "price":       0,
        "team_size":   f"{min_t}–{max_t} members",
        "organizer":   e.get("organisation", {}).get("name", "") if isinstance(e.get("organisation"), dict) else "",
        "description": e.get("description") or e.get("tagline") or "",
        "registration_link": url,
    }


def get_unstop_events() -> list[dict]:
    events: list[dict] = []
    seen: set[str] = set()

    for api_url in API_PAGES:
        resp = safe_get(api_url, timeout=8)
        if not resp:
            throttle(1.0)
            continue
        try:
            data = resp.json()
            items = (data.get("data", {}).get("data", [])
                     or data.get("results", [])
                     or (data if isinstance(data, list) else []))
            for item in items:
                parsed = _parse(item)
                if parsed and parsed["url"] not in seen:
                    seen.add(parsed["url"])
                    events.append(parsed)
        except Exception as exc:
            logger.warning("Unstop parse error: %s", exc)
        throttle(0.8)

    logger.info("Unstop: %d events", len(events))
    return events
