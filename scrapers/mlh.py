"""scrapers/mlh.py — Hackathons from Major League Hacking."""
from __future__ import annotations
import re
from datetime import datetime
from bs4 import BeautifulSoup
from core.utils import get_logger, safe_get, parse_date

logger = get_logger("scrapers.mlh")
PARSER = "lxml"
CY = datetime.now().year

MLH_URLS = [
    f"https://mlh.io/seasons/{CY}/events",
    f"https://mlh.io/seasons/{CY + 1}/events",
    "https://mlh.io/events",
]


def _clean_date(raw: str) -> str:
    if not raw:
        return "TBD"
    raw = raw.strip()
    m = re.match(r"([A-Za-z]+ \d+).*?(\d{4})", raw)
    if m:
        return parse_date(f"{m.group(1)}, {m.group(2)}")
    return parse_date(raw)


def get_mlh_events() -> list[dict]:
    events: list[dict] = []
    seen: set[str] = set()

    for mlh_url in MLH_URLS:
        resp = safe_get(mlh_url, timeout=20)
        if not resp:
            continue

        soup = BeautifulSoup(resp.text, PARSER)
        cards = soup.select(".event-wrapper, [class*='event-wrapper'], .event")
        if not cards:
            cards = soup.select("a[href*='hack'], a[href*='event']")

        for card in cards:
            name_el = (card.select_one(".event-name, [class*='event-name']")
                       or card.select_one("h3") or card.select_one("h4"))
            date_el = (card.select_one(".event-date, [class*='event-date']")
                       or card.select_one("time") or card.select_one("[class*='date']"))
            loc_el  = (card.select_one(".event-location, [class*='location']")
                       or card.select_one("[class*='city']"))
            link_el = card if card.name == "a" else card.select_one("a[href]")

            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name:
                continue

            href = ""
            if link_el:
                href = link_el.get("href", "")
                if href and not href.startswith("http"):
                    href = "https://mlh.io" + href

            date_raw = date_el.get_text(" ", strip=True) if date_el else ""
            loc = loc_el.get_text(strip=True) if loc_el else "Online"
            key = href or name
            if key in seen:
                continue
            seen.add(key)

            is_online = "online" in loc.lower() or not loc or loc == "Online"
            events.append({
                "source":      "MLH",
                "type":        "Hackathon",
                "event_type":  "Hackathon",
                "title":       name,
                "url":         href or "https://mlh.io/events",
                "date":        _clean_date(date_raw),
                "end_date":    "TBD",
                "location":    loc,
                "online":      is_online,
                "mode":        "Online" if is_online else "Offline",
                "format":      "Hackathon",
                "fee":         "free",
                "price":       0,
                "team_size":   "1–4 members",
                "organizer":   "MLH",
                "description": "",
                "registration_link": href or "https://mlh.io/events",
            })

        if events:
            logger.info("MLH: %d events from %s", len(events), mlh_url)
            break

    logger.info("MLH: %d events total", len(events))
    return events
