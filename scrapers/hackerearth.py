"""scrapers/hackerearth.py — Hackathons / challenges from HackerEarth API."""
from __future__ import annotations
import re
from datetime import datetime, timezone
from core.utils import get_logger, safe_get, parse_date, throttle

logger = get_logger("scrapers.hackerearth")
BASE    = "https://www.hackerearth.com"
API_URL = "https://www.hackerearth.com/api/v3/challenges/?type=hackathon&status=upcoming"


def _clean_date(raw: str) -> str:
    if not raw:
        return "TBD"
    raw = raw.strip()
    # Strip time/timezone suffixes
    raw = re.sub(r"\s+UTC.*$", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s+IST.*$", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s+\(.*$",  "", raw)
    raw = re.sub(r"\s+\d{1,2}:\d{2}.*$", "", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    result = parse_date(raw)
    if result != "TBD":
        return result
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%b %d", "%B %d"):
        try:
            d = datetime.strptime(raw, fmt)
            if d.year == 1900:
                d = d.replace(year=datetime.now().year)
            return d.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return "TBD"


def _is_future(date_str: str) -> bool:
    if date_str in ("TBD", "", "unknown"):
        return True
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return d >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    except ValueError:
        return True


def get_hackerearth_events() -> list[dict]:
    events: list[dict] = []
    seen: set[str] = set()

    try:
        resp = safe_get(API_URL, timeout=20)
        if resp and "application/json" in resp.headers.get("Content-Type", ""):
            items = resp.json().get("results", [])
            for h in items:
                title = h.get("title") or h.get("name") or ""
                if not title:
                    continue

                start = _clean_date(str(h.get("start_utc_tz") or h.get("start_date") or ""))
                end   = _clean_date(str(h.get("end_utc_tz")   or h.get("end_date")   or ""))

                if not _is_future(start):
                    continue

                slug = h.get("slug", "")
                url  = h.get("url") or (f"{BASE}/challenges/hackathon/{slug}/" if slug else BASE)

                ts = h.get("allowed_team_size")
                team_size = (f"Up to {ts} members" if isinstance(ts, int) else "Individual / Team")

                rec = {
                    "source":      "HackerEarth",
                    "type":        "Hackathon",
                    "event_type":  "Hackathon",
                    "title":       title,
                    "url":         url,
                    "date":        start,
                    "end_date":    end,
                    "location":    "Online",
                    "online":      True,
                    "mode":        "Online",
                    "format":      "Online Challenge",
                    "fee":         "free",
                    "price":       0,
                    "team_size":   team_size,
                    "organizer":   h.get("company_name", "HackerEarth"),
                    "description": h.get("description", ""),
                    "registration_link": url,
                }
                if url not in seen:
                    seen.add(url)
                    events.append(rec)
    except Exception as exc:
        logger.warning("HackerEarth API error: %s", exc)

    logger.info("HackerEarth: %d events", len(events))
    return events
