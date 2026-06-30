"""
app.py — Production-ready Flask backend for CTF & Hackathon Tracker.

Sources: CTFtime API · Devpost API · Devfolio API · HackerEarth API
         · MLH scraper · Unstop API · DuckDuckGo Web Search

Run:  python app.py
SMTP: set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables.
"""

from __future__ import annotations

import json
import logging
import os
import re
import smtplib
import traceback
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS

load_dotenv()

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("ctf_tracker")

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Offline regions accepted by the filter — match any substring of location
VALID_OFFLINE_REGIONS = [
    "tamil nadu", "tamilnadu",
    "chennai", "coimbatore", "madurai", "trichy", "vellore",
    "kerala", "kochi", "trivandrum", "thrissur", "calicut",
    "bengaluru", "bangalore", "karnataka",
]


# ---------------------------------------------------------------------------
# Field normalisation — unify the different schemas across scrapers
# ---------------------------------------------------------------------------

def _normalise(event: dict) -> dict:
    """
    Ensure every event has a consistent set of fields regardless of which
    scraper produced it. Fields: title, event_type, organizer, price, mode,
    location, date, registration_link, source, description, url.
    """
    e = dict(event)

    # --- event_type ---
    if not e.get("event_type"):
        raw_type = (e.get("type") or "").strip()
        e["event_type"] = raw_type if raw_type else "Hackathon"

    # --- online / mode ---
    online_flag = e.get("online")
    if online_flag is None:
        # Fall back to mode field
        mode_raw = (e.get("mode") or "").lower()
        online_flag = (mode_raw != "offline")
    e["online"] = bool(online_flag)
    e["mode"]   = "Online" if e["online"] else "Offline"

    # --- location ---
    loc = (e.get("location") or "").strip()
    if not loc:
        loc = "Online" if e["online"] else "TBD"
    e["location"] = loc

    # --- price ---
    price = e.get("price")
    if price is None:
        fee = (e.get("fee") or "free").lower()
        price = 0 if "free" in fee else 999
    e["price"] = int(price)

    # --- organizer ---
    if not e.get("organizer"):
        e["organizer"] = e.get("source", "Unknown")

    # --- registration_link ---
    if not e.get("registration_link"):
        e["registration_link"] = e.get("url") or e.get("ctftime_url") or ""

    # --- date ---
    if not e.get("date"):
        e["date"] = "TBD"

    # --- description ---
    if not e.get("description"):
        e["description"] = ""

    return e


# ---------------------------------------------------------------------------
# Filter — RULE 1 price ≤ 500, RULE 2 online or TN/KL/BLR offline
# ---------------------------------------------------------------------------

def _is_past(date_str: str) -> bool:
    """
    Return True if the event date is BEFORE today (midnight UTC).
    Events with unknown/TBD date are kept (return False).
    """
    if not date_str or date_str in ("TBD", "unknown", ""):
        return False   # keep events with no date
    try:
        event_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        # Cutoff = start of today (00:00 UTC), so today's events are still included
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return event_date < today_start
    except ValueError:
        return False   # unparseable date → keep


def _passes_filter(e: dict) -> bool:
    # RULE 1 — Price: free or ≤ ₹500
    price = e.get("price", 0)
    if price > 500:
        return False

    # RULE 2 — Location / mode: online (any) or offline TN/KL/BLR only
    if e.get("online"):
        location_ok = True
    else:
        loc = (e.get("location") or "").lower()
        location_ok = any(r in loc for r in VALID_OFFLINE_REGIONS)
    if not location_ok:
        return False

    # RULE 3 — Date: must be today or in the future (past events excluded)
    if _is_past(e.get("date", "TBD")):
        return False

    return True


# ---------------------------------------------------------------------------
# Scrape → normalise → filter → deduplicate → enrich
# ---------------------------------------------------------------------------

def _run_scrapers() -> list[dict]:
    """Call every real scraper and return combined raw events."""
    from scrapers.ctftime       import get_ctf_events
    from scrapers.devpost       import get_devpost_events
    from scrapers.devfolio      import get_devfolio_events
    from scrapers.hackerearth   import get_hackerearth_events
    from scrapers.mlh           import get_mlh_events
    from scrapers.unstop        import get_unstop_events
    from scrapers.search_engine import get_search_engine_events
    from scrapers.dare2compete  import get_dare2compete_events
    from scrapers.india_offline import get_india_offline_events

    sources = [
        ("CTFtime",         get_ctf_events),
        ("Devpost",         get_devpost_events),
        ("Devfolio",        get_devfolio_events),
        ("HackerEarth",     get_hackerearth_events),
        ("MLH",             get_mlh_events),
        ("Unstop",          get_unstop_events),
        ("India Offline",   get_india_offline_events),
        ("Dare2Compete",    get_dare2compete_events),
        ("Web Search",      get_search_engine_events),
    ]

    all_raw: list[dict] = []
    for name, fn in sources:
        try:
            results = fn()
            logger.info("%s → %d raw events", name, len(results))
            all_raw.extend(results)
        except Exception as exc:
            logger.error("%s scraper failed: %s", name, exc, exc_info=True)

    return all_raw


def _deduplicate(events: list[dict]) -> list[dict]:
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    out: list[dict] = []
    for e in events:
        url   = (e.get("url") or e.get("registration_link") or "").rstrip("/")
        title = (e.get("title") or "").lower().strip()
        if url and url in seen_urls:
            continue
        if title in seen_titles:
            continue
        if url:
            seen_urls.add(url)
        if title:
            seen_titles.add(title)
        out.append(e)
    return out


def _enrich(events: list[dict]) -> list[dict]:
    now = datetime.utcnow()
    for e in events:
        date_str = e.get("date", "TBD")
        try:
            d     = datetime.strptime(date_str, "%Y-%m-%d")
            delta = (d - now).days
            e["days_until"] = delta
            if delta <= 0:
                e["urgency"] = "today"
            elif delta <= 7:
                e["urgency"] = "this_week"
            elif delta <= 30:
                e["urgency"] = "this_month"
            else:
                e["urgency"] = "upcoming"
        except ValueError:
            e["days_until"] = 999
            e["urgency"]    = "upcoming"
    return sorted(events, key=lambda x: x.get("date", "9999-99-99"))


def _refresh_events() -> list[dict]:
    raw      = _run_scrapers()
    normalised = [_normalise(e) for e in raw]
    filtered   = [e for e in normalised if _passes_filter(e)]
    deduped    = _deduplicate(filtered)
    enriched   = _enrich(deduped)

    logger.info(
        "Pipeline: raw=%d → normalised=%d → filtered=%d → deduped=%d",
        len(raw), len(normalised), len(filtered), len(deduped),
    )

    cache_file = DATA_DIR / "events.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    return enriched


def _load_events() -> list[dict]:
    cache_file = DATA_DIR / "events.json"
    if cache_file.exists():
        try:
            age_s = datetime.utcnow().timestamp() - cache_file.stat().st_mtime
            if age_s < 3600:
                with open(cache_file, encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
    return _refresh_events()


# ---------------------------------------------------------------------------
# Email helpers
# ---------------------------------------------------------------------------

def _send_email(recipient: str, excel_path: str, pdf_path: str) -> None:
    sender   = os.getenv("EMAIL_ADDRESS", "").strip()
    password = os.getenv("EMAIL_PASSWORD", "").strip()

    if not sender or not password:
        raise RuntimeError(
            "SMTP credentials not configured. "
            "Set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables."
        )

    msg = EmailMessage()
    msg["Subject"] = "🚩 Your CTF & Hackathon Events Report"
    msg["From"]    = sender
    msg["To"]      = recipient
    msg.set_content(
        "Hello,\n\n"
        "Please find attached your CTF & Hackathon Events report.\n\n"
        "Filters applied:\n"
        "  ✓ Price: Free (₹0) or ≤ ₹500\n"
        "  ✓ Online events (all regions)\n"
        "  ✓ Offline events in Tamil Nadu / Kerala / Bengaluru only\n\n"
        "Sources: CTFtime · Devpost · Devfolio · HackerEarth · MLH · Unstop · Web Search\n\n"
        "Stay sharp!\n— CTF & Hackathon Tracker"
    )

    with open(excel_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="events_export.xlsx",
        )
    with open(pdf_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename="events_export.pdf",
        )

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(sender, password)
        smtp.send_message(msg)

    logger.info("Email sent to %s", recipient)


def _safe_delete(*paths: str) -> None:
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/events", methods=["GET"])
def api_events():
    try:
        force  = request.args.get("refresh", "false").lower() == "true"
        events = _refresh_events() if force else _load_events()

        # Optional server-side search
        q = request.args.get("search", "").lower().strip()
        if q:
            events = [e for e in events
                      if q in (e.get("title", "") or "").lower()
                      or q in (e.get("organizer", "") or "").lower()
                      or q in (e.get("location", "") or "").lower()]

        return jsonify({
            "success":      True,
            "count":        len(events),
            "events":       events,
            "last_updated": datetime.utcnow().isoformat() + "Z",
        })
    except Exception as exc:
        logger.error("api_events error: %s", exc, exc_info=True)
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/stats", methods=["GET"])
def api_stats():
    try:
        events = _load_events()
        total   = len(events)
        free    = sum(1 for e in events if e.get("price", 0) == 0)
        online  = sum(1 for e in events if e.get("mode", "").lower() == "online")
        week    = sum(1 for e in events if e.get("urgency") in ("today", "this_week"))
        month   = sum(1 for e in events if e.get("urgency") == "this_month")

        by_source: dict[str, int] = {}
        by_type:   dict[str, int] = {}
        for e in events:
            s = e.get("source", "Unknown")
            t = e.get("event_type", "Unknown")
            by_source[s] = by_source.get(s, 0) + 1
            by_type[t]   = by_type.get(t, 0) + 1

        return jsonify({
            "success":    True,
            "total":      total,
            "free":       free,
            "online":     online,
            "offline":    total - online,
            "this_week":  week,
            "this_month": month,
            "by_source":  by_source,
            "by_type":    by_type,
        })
    except Exception as exc:
        logger.error("api_stats error: %s", exc, exc_info=True)
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/export/email", methods=["POST"])
def api_export_email():
    excel_path = pdf_path = None
    try:
        body  = request.get_json(silent=True) or {}
        email = (body.get("email") or "").strip()

        if not email:
            return jsonify({"success": False, "message": "Email address is required."}), 400
        if not _EMAIL_RE.match(email):
            return jsonify({"success": False, "message": f"'{email}' is not a valid email address."}), 400

        # ── Browser state ────────────────────────────────────────────────
        removed_keys = set(body.get("removed_keys") or [])
        active_keys  = set(body.get("active_keys")  or [])
        teams        = body.get("teams") or []          # list of team dicts from dashboard

        def _key(e: dict) -> str:
            return f"{e.get('title', '')}|{e.get('date', '')}"

        events = _load_events()
        if not events:
            return jsonify({
                "success": False,
                "message": "No events to export. Click Refresh first.",
            }), 404

        # Filter out user-removed events
        events = [e for e in events if _key(e) not in removed_keys]

        if not events:
            return jsonify({
                "success": False,
                "message": "All events have been removed. Nothing to export.",
            }), 404

        # Tag active/ongoing events
        for e in events:
            e["status"] = "Ongoing" if _key(e) in active_keys else "Upcoming"

        from exporter import generate_excel, generate_pdf
        logger.info(
            "Generating reports for %s — %d events (%d ongoing, %d removed filtered)",
            email, len(events),
            sum(1 for e in events if e["status"] == "Ongoing"),
            len(removed_keys),
        )
        excel_path = generate_excel(events, teams=teams)
        pdf_path   = generate_pdf(events)

        _send_email(email, excel_path, pdf_path)

        return jsonify({"success": True, "message": f"Report emailed to {email} 🎉"})

    except RuntimeError as exc:
        return jsonify({"success": False, "message": str(exc)}), 503
    except smtplib.SMTPAuthenticationError:
        return jsonify({"success": False, "message": "Gmail authentication failed. Check credentials."}), 503
    except smtplib.SMTPException as exc:
        return jsonify({"success": False, "message": f"Email delivery failed: {exc}"}), 503
    except Exception as exc:
        logger.error("api_export_email: %s", traceback.format_exc())
        return jsonify({"success": False, "message": f"Unexpected error: {exc}"}), 500
    finally:
        _safe_delete(excel_path, pdf_path)


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_):
    return jsonify({"success": False, "error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(exc):
    logger.error("Unhandled 500: %s", exc)
    return jsonify({"success": False, "error": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting CTF & Hackathon Tracker on http://0.0.0.0:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
