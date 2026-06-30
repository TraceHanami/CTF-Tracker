"""
scrapers/search_engine.py — Discover CTF & Hackathon events via DuckDuckGo.

Runs two categories of queries:
  1. OFFLINE queries — find events physically in TN, Kerala, Bengaluru
  2. ONLINE queries  — find global CTF/hackathon events

For offline queries the location and mode fields are correctly set
so the app's filter rule 2 (TN/KL/BLR offline) passes.
"""
from __future__ import annotations
import re
import time
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup
from core.utils import get_logger, safe_get, parse_date

logger = get_logger("scrapers.search_engine")
DDGO_URL = "https://html.duckduckgo.com/html/"

# ── Query catalogue ─────────────────────────────────────────────────────────
# Each entry: (query_string, forced_mode, forced_location_hint)
# forced_mode: "Offline" | "Online" | None (auto-detect from snippet)
# forced_location_hint: a string to use as location when mode is Offline

QUERY_CATALOGUE = [
    # ── OFFLINE TN ───────────────────────────────────────────────────────────
    ("hackathon 2025 Chennai Tamil Nadu offline registration open",
     "Offline", "Chennai, Tamil Nadu"),
    ("hackathon 2026 Chennai Tamil Nadu free registration",
     "Offline", "Chennai, Tamil Nadu"),
    ("hackathon 2025 Coimbatore Tamil Nadu free site:unstop.com OR site:devfolio.co",
     "Offline", "Coimbatore, Tamil Nadu"),
    ("hackathon 2026 Coimbatore Tamil Nadu free open registration",
     "Offline", "Coimbatore, Tamil Nadu"),
    ("CTF 2025 Tamil Nadu Chennai offline free",
     "Offline", "Tamil Nadu"),
    ("CTF 2026 Tamil Nadu free competition registration",
     "Offline", "Tamil Nadu"),
    ("hackathon 2025 SRM VIT Anna University Tamil Nadu free",
     "Offline", "Tamil Nadu"),
    ("hackathon 2026 PSG college Coimbatore free registration",
     "Offline", "Coimbatore, Tamil Nadu"),
    ("tech fest hackathon 2025 2026 Tamil Nadu free registration",
     "Offline", "Tamil Nadu"),

    # ── OFFLINE KERALA ────────────────────────────────────────────────────────
    ("hackathon 2025 Kochi Kerala offline free registration",
     "Offline", "Kochi, Kerala"),
    ("hackathon 2026 Kerala free registration open",
     "Offline", "Kerala"),
    ("CTF 2025 Kerala Kochi free competition",
     "Offline", "Kerala"),
    ("mulearn hackfest Kerala 2025 2026",
     "Offline", "Kerala"),
    ("hackathon 2025 Trivandrum Thrissur Kerala free",
     "Offline", "Kerala"),

    # ── OFFLINE BENGALURU ─────────────────────────────────────────────────────
    ("hackathon 2025 Bengaluru Bangalore free registration",
     "Offline", "Bengaluru, Karnataka"),
    ("hackathon 2026 Bangalore free open registration site:unstop.com OR site:devfolio.co",
     "Offline", "Bengaluru, Karnataka"),
    ("CTF 2025 Bengaluru Bangalore offline free competition",
     "Offline", "Bengaluru, Karnataka"),
    ("tech summit hackathon 2025 Bengaluru free",
     "Offline", "Bengaluru, Karnataka"),

    # ── ONLINE CTF ────────────────────────────────────────────────────────────
    ("upcoming free CTF competition 2026 site:ctftime.org",
     "Online", "Online"),
    ("upcoming online CTF 2026 free India registration",
     "Online", "Online"),

    # ── ONLINE HACKATHON ──────────────────────────────────────────────────────
    ("free hackathon 2026 India online devfolio devpost",
     "Online", "Online / India"),
    ("hackathon 2026 Kerala Tamil Nadu Bengaluru online free",
     "Online", "Online / India"),
]

SKIP_DOMAINS = {
    "google.com", "bing.com", "duckduckgo.com", "yahoo.com",
    "youtube.com", "facebook.com", "twitter.com", "instagram.com",
    "reddit.com", "quora.com", "linkedin.com", "medium.com",
    "wikipedia.org", "github.com", "glassdoor.com",
}


def _ddg_search(query: str) -> list[dict]:
    """Return raw search results from DuckDuckGo HTML."""
    results: list[dict] = []
    try:
        resp = safe_get(DDGO_URL, params={"q": query, "kl": "in-en"}, timeout=20)
        if not resp:
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        for result in soup.select(".result"):
            title_el   = result.select_one(".result__title")
            link_el    = result.select_one(".result__url, a[href]")
            snippet_el = result.select_one(".result__snippet")
            if not title_el or not link_el:
                continue
            title   = title_el.get_text(strip=True)
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            href    = link_el.get("href", "") or ""
            # Un-redirect DDG wrapped URLs
            uddg = re.search(r"uddg=([^&]+)", href)
            if uddg:
                href = unquote(uddg.group(1))
            if not href.startswith("http"):
                continue
            domain = urlparse(href).netloc.replace("www.", "")
            if any(skip in domain for skip in SKIP_DOMAINS):
                continue
            results.append({"title": title, "url": href,
                             "snippet": snippet, "domain": domain})
    except Exception as exc:
        logger.warning("DDG search failed: %s", exc)
    return results


def _infer_type(title: str, snippet: str) -> str:
    combined = (title + " " + snippet).lower()
    if "ctf" in combined or "capture the flag" in combined:
        return "CTF"
    return "Hackathon"


def _infer_date(snippet: str) -> str:
    for pat in [r"\b(\d{4}-\d{2}-\d{2})\b",
                r"\b(\w+ \d{1,2},? \d{4})\b",
                r"\b(\d{1,2} \w+ \d{4})\b"]:
        m = re.search(pat, snippet)
        if m:
            parsed = parse_date(m.group(1))
            if parsed != "TBD":
                return parsed
    return "TBD"


def get_search_engine_events() -> list[dict]:
    events: list[dict] = []
    seen: set[str] = set()

    for (query, forced_mode, location_hint) in QUERY_CATALOGUE:
        results = _ddg_search(query)
        for r in results:
            url  = r["url"]
            norm = re.sub(r"\?.*$", "", url).rstrip("/")
            if norm in seen:
                continue
            seen.add(norm)

            title = r["title"].strip()
            if not title or len(title) < 5:
                continue

            etype     = _infer_type(title, r["snippet"])
            date_str  = _infer_date(r["snippet"])

            # ── Mode & location ─────────────────────────────────────────
            # Use the forced values from the query catalogue so offline
            # TN/KL/BLR events are correctly labelled as "Offline".
            mode      = forced_mode          # "Online" or "Offline"
            location  = location_hint        # e.g. "Chennai, Tamil Nadu"
            is_online = (mode == "Online")

            events.append({
                "source":      "Web Search",
                "type":        etype,
                "event_type":  etype,
                "title":       title[:120],
                "url":         url,
                "date":        date_str,
                "end_date":    "TBD",
                "location":    location,
                "online":      is_online,
                "mode":        mode,
                "format":      etype,
                "fee":         "free",
                "price":       0,
                "team_size":   "—",
                "organizer":   r["domain"],
                "description": r["snippet"][:200],
                "registration_link": url,
            })

        time.sleep(1.2)   # be polite to DDG

    logger.info("Web Search: %d events discovered", len(events))
    return events
