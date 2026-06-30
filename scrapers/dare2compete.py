"""
scrapers/dare2compete.py — Indian offline college hackathons & CTFs
from dare2compete.com (now rebranded to Unstop, but their old domain
still serves listings).

Also scrapes townscript.com which has many Tamil Nadu / Kerala / Bengaluru
tech events with direct registration links.
"""
from __future__ import annotations
import re
from bs4 import BeautifulSoup
from core.utils import get_logger, safe_get, parse_date, throttle

logger = get_logger("scrapers.dare2compete")

# ── dare2compete / Unstop competition listing API ────────────────────────────
D2C_API_PAGES = [
    "https://unstop.com/api/public/opportunity/search-result?opportunity=hackathon"
    "&filters[0][type]=location&filters[0][value]=offline"
    "&filters[1][type]=country&filters[1][value]=India"
    "&per_page=30&page=1",

    "https://unstop.com/api/public/opportunity/search-result?opportunity=hackathon"
    "&filters[0][type]=location&filters[0][value]=offline"
    "&filters[1][type]=country&filters[1][value]=India"
    "&per_page=30&page=2",
]

# ── Townscript — event registration platform popular in India ────────────────
TOWNSCRIPT_URLS = [
    "https://www.townscript.com/in/online?category=hackathon",
    "https://www.townscript.com/in/chennai?category=tech",
    "https://www.townscript.com/in/coimbatore?category=tech",
    "https://www.townscript.com/in/kochi?category=tech",
    "https://www.townscript.com/in/bangalore?category=hackathon",
]

# ── Regions accepted as valid offline ────────────────────────────────────────
VALID_REGIONS = [
    "tamil nadu", "chennai", "coimbatore", "madurai", "trichy", "vellore",
    "kerala", "kochi", "trivandrum", "thrissur", "calicut",
    "bengaluru", "bangalore", "karnataka",
]


def _location_valid(loc: str) -> bool:
    loc_lower = loc.lower()
    return any(r in loc_lower for r in VALID_REGIONS)


# ── dare2compete / Unstop offline API ────────────────────────────────────────

def _parse_unstop_offline(e: dict) -> dict | None:
    title = (e.get("title") or e.get("name") or "").strip()
    if not title:
        return None

    fee_raw = str(e.get("registration_fees", "0")).strip()
    try:
        if fee_raw not in ("0", "", "Free", "free", "null", "None"):
            if float(fee_raw) > 500:
                return None
            price = int(float(fee_raw))
        else:
            price = 0
    except ValueError:
        price = 0

    loc = (e.get("city") or e.get("location") or "").strip()
    if not loc or not _location_valid(loc):
        return None   # only accept TN/KL/BLR

    uid  = e.get("id", "")
    slug = e.get("seo_url", "") or str(uid)
    url  = f"https://unstop.com/{slug}" if slug else "https://unstop.com/hackathons"

    starts = e.get("start_date") or e.get("starts_at") or ""
    ends   = e.get("end_date")   or e.get("ends_at")   or ""

    min_t = e.get("min_team_size") or 1
    max_t = e.get("max_team_size") or 4

    return {
        "source":      "Unstop (Offline)",
        "type":        "Hackathon",
        "event_type":  "Hackathon",
        "title":       title,
        "url":         url,
        "date":        parse_date(str(starts)),
        "end_date":    parse_date(str(ends)),
        "location":    loc,
        "online":      False,
        "mode":        "Offline",
        "format":      "Hackathon",
        "fee":         "free" if price == 0 else f"₹{price}",
        "price":       price,
        "team_size":   f"{min_t}–{max_t} members",
        "organizer":   e.get("organisation", {}).get("name", "")
                       if isinstance(e.get("organisation"), dict) else "",
        "description": e.get("description") or e.get("tagline") or "",
        "registration_link": url,
    }


def _scrape_unstop_offline() -> list[dict]:
    events: list[dict] = []
    seen: set[str] = set()
    for api_url in D2C_API_PAGES:
        resp = safe_get(api_url, timeout=25)
        if not resp:
            throttle(1.0)
            continue
        try:
            data  = resp.json()
            items = (data.get("data", {}).get("data", [])
                     or data.get("results", [])
                     or (data if isinstance(data, list) else []))
            for item in items:
                parsed = _parse_unstop_offline(item)
                if parsed and parsed["url"] not in seen:
                    seen.add(parsed["url"])
                    events.append(parsed)
        except Exception as exc:
            logger.warning("Unstop offline API error: %s", exc)
        throttle(0.8)
    return events


# ── Townscript scraper ────────────────────────────────────────────────────────

def _city_from_url(url: str) -> str:
    """Infer location from Townscript listing URL."""
    parts = url.lower().split("/")
    city_map = {
        "chennai":    "Chennai, Tamil Nadu",
        "coimbatore": "Coimbatore, Tamil Nadu",
        "kochi":      "Kochi, Kerala",
        "bangalore":  "Bengaluru, Karnataka",
        "online":     "Online",
    }
    for part in parts:
        if part in city_map:
            return city_map[part]
    return "India"


def _scrape_townscript() -> list[dict]:
    events: list[dict] = []
    seen: set[str] = set()

    for url in TOWNSCRIPT_URLS:
        resp = safe_get(url, timeout=20)
        if not resp:
            throttle(1.0)
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        city_location = _city_from_url(url)
        is_online = "online" in city_location.lower()

        # Townscript card selectors
        cards = soup.select(".eventWrapper, .event-card, [class*='event']")
        if not cards:
            cards = soup.select("article, .card")

        for card in cards:
            title_el = (card.select_one("h2") or card.select_one("h3")
                        or card.select_one("[class*='title']"))
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title or len(title) < 4:
                continue

            link_el = card.select_one("a[href]")
            href = ""
            if link_el:
                href = link_el.get("href", "")
                if href and not href.startswith("http"):
                    href = "https://www.townscript.com" + href

            date_el = card.select_one("[class*='date'], time")
            date_str = parse_date(date_el.get_text(strip=True)) if date_el else "TBD"

            # Fee check — skip paid events
            fee_el   = card.select_one("[class*='price'], [class*='fee']")
            fee_text = fee_el.get_text(strip=True) if fee_el else "Free"
            if "₹" in fee_text:
                m = re.search(r"₹\s*(\d+)", fee_text)
                if m and int(m.group(1)) > 500:
                    continue

            key = href or title.lower()
            if key in seen:
                continue
            seen.add(key)

            events.append({
                "source":      "Townscript",
                "type":        "Hackathon",
                "event_type":  "Hackathon",
                "title":       title,
                "url":         href or url,
                "date":        date_str,
                "end_date":    "TBD",
                "location":    city_location,
                "online":      is_online,
                "mode":        "Online" if is_online else "Offline",
                "format":      "Hackathon",
                "fee":         "free",
                "price":       0,
                "team_size":   "—",
                "organizer":   "Townscript",
                "description": "",
                "registration_link": href or url,
            })

        throttle(1.0)

    logger.info("Townscript: %d events", len(events))
    return events


# ── Public entry point ────────────────────────────────────────────────────────

def get_dare2compete_events() -> list[dict]:
    """Return offline TN/KL/BLR events from Unstop offline API + Townscript."""
    events = []
    events.extend(_scrape_unstop_offline())
    events.extend(_scrape_townscript())
    logger.info("dare2compete total (offline India): %d events", len(events))
    return events
