"""
scrapers.py — Mock event data provider + strict filter logic.

get_all_scraped_events() returns 15 richly-varied mock events covering all
mandatory price points, modes, locations, and event types.

filter_target_events(events) applies two-rule filtering:
  RULE 1 — Price: Free (0) or price <= 500 INR only.
  RULE 2 — Location/Mode: Online OR (Offline AND Tamil Nadu / Kerala / Bengaluru).
"""

from __future__ import annotations
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Helper — build a future date string relative to today
# ---------------------------------------------------------------------------
def _future(days: int) -> str:
    return (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Mock event catalogue
# ---------------------------------------------------------------------------
_MOCK_EVENTS: list[dict] = [
    # ── FREE ONLINE ──────────────────────────────────────────────────────
    {
        "title": "PicoCTF 2026 — Global Online Challenge",
        "event_type": "CTF",
        "organizer": "Carnegie Mellon University",
        "price": 0,
        "mode": "Online",
        "location": "Online / Worldwide",
        "date": _future(5),
        "registration_link": "https://picoctf.org/",
    },
    {
        "title": "HackWith India — National Hackathon",
        "event_type": "Hackathon",
        "organizer": "Devfolio",
        "price": 0,
        "mode": "Online",
        "location": "Online / India",
        "date": _future(12),
        "registration_link": "https://devfolio.co/hackathons",
    },
    {
        "title": "Google CTF Qualifier 2026",
        "event_type": "CTF",
        "organizer": "Google Security",
        "price": 0,
        "mode": "Online",
        "location": "Online / Global",
        "date": _future(20),
        "registration_link": "https://capturetheflag.withgoogle.com/",
    },
    {
        "title": "MLH Localhost: AI Sprint",
        "event_type": "Hackathon",
        "organizer": "Major League Hacking",
        "price": 0,
        "mode": "Online",
        "location": "Online / Global",
        "date": _future(8),
        "registration_link": "https://mlh.io/",
    },

    # ── CHEAP / AFFORDABLE ONLINE (≤500) ────────────────────────────────
    {
        "title": "DevHack Season 4 — Web3 Edition",
        "event_type": "Hackathon",
        "organizer": "HackerEarth",
        "price": 150,
        "mode": "Online",
        "location": "Online / India",
        "date": _future(15),
        "registration_link": "https://hackerearth.com/challenges/hackathon/devhack4/",
    },
    {
        "title": "CyberStrike CTF — Beginner Track",
        "event_type": "CTF",
        "organizer": "CyberCell India",
        "price": 300,
        "mode": "Online",
        "location": "Online / India",
        "date": _future(18),
        "registration_link": "https://cybercell.example.com/cyberstrike",
    },

    # ── FREE OFFLINE — Tamil Nadu (VALID) ────────────────────────────────
    {
        "title": "TechFest Hackathon @ IIT Madras",
        "event_type": "Hackathon",
        "organizer": "IIT Madras Students",
        "price": 0,
        "mode": "Offline",
        "location": "Chennai, Tamil Nadu",
        "date": _future(25),
        "registration_link": "https://techfest.iitm.ac.in/",
    },
    {
        "title": "Coimbatore CTF Challenge — PSG College",
        "event_type": "CTF",
        "organizer": "PSG College of Technology",
        "price": 0,
        "mode": "Offline",
        "location": "Coimbatore, Tamil Nadu",
        "date": _future(30),
        "registration_link": "https://psgtech.edu/events/ctf2026",
    },
    {
        "title": "VIT Vellore HackOn 2026",
        "event_type": "Hackathon",
        "organizer": "VIT Vellore",
        "price": 0,
        "mode": "Offline",
        "location": "Vellore, Tamil Nadu",
        "date": _future(35),
        "registration_link": "https://vit.ac.in/hackon2026",
    },

    # ── AFFORDABLE OFFLINE — Tamil Nadu (VALID, ≤500) ────────────────────
    {
        "title": "Smart India Hack — Regional Round",
        "event_type": "Hackathon",
        "organizer": "Unstop / AICTE",
        "price": 300,
        "mode": "Offline",
        "location": "Chennai, Tamil Nadu",
        "date": _future(22),
        "registration_link": "https://unstop.com/hackathons/smart-india-hack",
    },

    # ── FREE OFFLINE — Kerala (VALID) ────────────────────────────────────
    {
        "title": "MuLearn HackFest — Kochi Edition",
        "event_type": "Hackathon",
        "organizer": "MuLearn Foundation",
        "price": 0,
        "mode": "Offline",
        "location": "Kochi, Kerala",
        "date": _future(28),
        "registration_link": "https://mulearn.org/hackfest",
    },

    # ── FREE OFFLINE — Bengaluru (VALID) ─────────────────────────────────
    {
        "title": "Bengaluru Tech Summit Hackathon 2026",
        "event_type": "Hackathon",
        "organizer": "Karnataka ITBT Department",
        "price": 0,
        "mode": "Offline",
        "location": "Bengaluru, Karnataka",
        "date": _future(40),
        "registration_link": "https://bengalurutechsummit.com/hackathon",
    },

    # ── EXPENSIVE → MUST BE REJECTED (>500) ─────────────────────────────
    {
        "title": "TechSpark Elite Hackathon — Delhi",
        "event_type": "Hackathon",
        "organizer": "TechSpark Events",
        "price": 600,
        "mode": "Offline",
        "location": "Delhi",
        "date": _future(20),
        "registration_link": "https://techspark.in/elite",
    },
    {
        "title": "InnovateFest Premium — Mumbai",
        "event_type": "Hackathon",
        "organizer": "InnovateFest Org",
        "price": 1200,
        "mode": "Offline",
        "location": "Mumbai",
        "date": _future(18),
        "registration_link": "https://innovatefest.in/premium",
    },

    # ── WRONG LOCATION OFFLINE → MUST BE REJECTED ────────────────────────
    {
        "title": "Hyderabad Hack Week — Season 3",
        "event_type": "Hackathon",
        "organizer": "T-Hub Hyderabad",
        "price": 0,
        "mode": "Offline",
        "location": "Hyderabad",
        "date": _future(14),
        "registration_link": "https://t-hub.co/hackweek",
    },
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_all_scraped_events() -> list[dict]:
    """Return all mock events (unfiltered)."""
    return [dict(e) for e in _MOCK_EVENTS]


def filter_target_events(events: list[dict]) -> list[dict]:
    """
    Apply two strict rules:

    RULE 1 — PRICE:
        Accept only events where price == 0 OR price <= 500.
        Reject anything above 500 (e.g. 600, 1200).

    RULE 2 — LOCATION / MODE:
        Accept if:
          A) mode == "Online"   (any price passing rule 1)
        OR
          B) mode == "Offline" AND location contains one of:
             "Tamil Nadu", "Kerala", "Bengaluru"
        Reject offline events from Delhi, Mumbai, Hyderabad, etc.
    """
    # Locations considered "nearby" for offline events
    VALID_OFFLINE_REGIONS = ["tamil nadu", "kerala", "bengaluru"]

    accepted: list[dict] = []
    for event in events:
        price: int | float = event.get("price", 0)
        mode: str = event.get("mode", "Online").strip()
        location: str = (event.get("location") or "").lower()

        # ── RULE 1: price gate ──────────────────────────────────────────
        if price > 500:
            continue  # reject 600, 1200, etc.

        # ── RULE 2: location/mode gate ──────────────────────────────────
        if mode == "Online":
            accepted.append(event)
        elif mode == "Offline":
            if any(region in location for region in VALID_OFFLINE_REGIONS):
                accepted.append(event)
            # else: offline but wrong region → rejected

    return accepted
