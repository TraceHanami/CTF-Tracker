"""core/filters.py — Regional and quality filters."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta

TN_KEYWORDS = [
    "tamil nadu", "tamilnadu", "chennai", "coimbatore", "madurai",
    "tiruchirappalli", "trichy", "salem", "tirunelveli", "vellore",
    "erode", "tiruppur", "thoothukudi", "tuticorin", "nagercoil",
    "kanchipuram", "kumbakonam", "thanjavur", "hosur", "dindigul",
    "cuddalore", "nagapattinam", "pondicherry", "puducherry",
    "anna university", "iit madras", "nit trichy", "vit vellore",
    "srm", "srmist", "sastra", "amrita", "psg", "ceg",
]

ONLINE_KEYWORDS = [
    "online", "virtual", "remote", "hybrid", "worldwide", "global",
    "anywhere", "web", "digital",
]

PAID_KEYWORDS = ["paid", "entry fee", "registration fee", "₹", "$", "usd", "inr fee"]
FREE_KEYWORDS = ["free", "₹0", "$0", "no fee", "no registration fee", "open", "gratis"]


def is_free(event: dict) -> bool:
    fee = str(event.get("fee", "free")).lower()
    cost = str(event.get("cost", "")).lower()
    combined = fee + " " + cost
    if any(k in combined for k in PAID_KEYWORDS):
        # allow if explicitly marked free too
        return any(k in combined for k in FREE_KEYWORDS)
    return True


def is_relevant_location(event: dict) -> bool:
    if event.get("online", False):
        return True
    loc = (event.get("location", "") or "").lower()
    return any(k in loc for k in TN_KEYWORDS + ONLINE_KEYWORDS)


def is_future(event: dict) -> bool:
    date_str = event.get("date", "TBD")
    end_date_str = event.get("end_date", "")
    if date_str in ("TBD", "", "unknown"):
        return True

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # If an end date is provided, event is considered future/active if end_date >= today
    if end_date_str and end_date_str not in ("TBD", "", "unknown"):
        try:
            end_d = datetime.strptime(end_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            return end_d >= today_start
        except ValueError:
            pass

    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return d >= today_start
    except ValueError:
        return True


def within_window(event: dict, months: int = 4) -> bool:
    date_str = event.get("date", "TBD")
    if date_str in ("TBD", "", "unknown"):
        return True
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        horizon = datetime.now(timezone.utc) + timedelta(days=months * 30)
        return d <= horizon
    except ValueError:
        return True


def apply_all(events: list[dict]) -> list[dict]:
    out = []
    for e in events:
        if not is_future(e):
            continue
        if not within_window(e):
            continue
        if not is_free(e):
            continue
        if not is_relevant_location(e):
            continue
        out.append(e)
    return out
