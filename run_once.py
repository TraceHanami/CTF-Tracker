"""
run_once.py — Manual one-shot test run with rich output table.
Usage:
    python run_once.py
    python run_once.py --source ctftime
    python run_once.py --no-notify
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
Path("data").mkdir(parents=True, exist_ok=True)

from core.utils import get_logger
from core.filters import apply_all
from core.aggregator import _deduplicate, _sort_events, _enrich

logger = get_logger("run_once")

SCRAPER_MAP = {
    "ctftime":     ("scrapers.ctftime",     "get_ctf_events"),
    "devfolio":    ("scrapers.devfolio",    "get_devfolio_events"),
    "unstop":      ("scrapers.unstop",      "get_unstop_events"),
    "hackerearth": ("scrapers.hackerearth", "get_hackerearth_events"),
    "mlh":         ("scrapers.mlh",         "get_mlh_events"),
    "devpost":     ("scrapers.devpost",     "get_devpost_events"),
}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--no-notify", action="store_true")
    p.add_argument("--source", choices=list(SCRAPER_MAP.keys()))
    return p.parse_args()


def run_scraper(name: str):
    import importlib
    mod, fn = SCRAPER_MAP[name]
    return getattr(importlib.import_module(mod), fn)()


def print_table(events):
    if not events:
        print("  No events.\n")
        return
    w = [46, 12, 14, 8, 10]
    headers = ["TITLE", "DATE", "SOURCE", "MODE", "TEAM SIZE"]
    row_fmt = "  {:<46} {:<12} {:<14} {:<8} {:<10}"
    print(row_fmt.format(*headers))
    print("  " + "─" * 110)
    for e in events:
        t = e["title"][:44].ljust(46)
        d = e.get("date", "TBD")[:12].ljust(12)
        s = e.get("source", "")[:13].ljust(14)
        m = ("Online" if e.get("online") else "Offline").ljust(8)
        ts = str(e.get("team_size", "—"))[:9]
        print(f"  {t} {d} {s} {m} {ts}")
    print()


def main():
    args = parse_args()
    print("\n" + "═"*60)
    print("  CTF & Hackathon Tracker — ONE-SHOT TEST RUN")
    print("═"*60)

    all_raw = []
    sources = [args.source] if args.source else list(SCRAPER_MAP.keys())
    for name in sources:
        print(f"\n→ {name:15s}", end=" ", flush=True)
        try:
            res = run_scraper(name)
            print(f"✓ {len(res):3d} events")
            all_raw.extend(res)
        except Exception as e:
            print(f"✗ FAILED ({e})")

    filtered = apply_all(all_raw)
    deduped  = _deduplicate(filtered)
    sorted_  = _sort_events(deduped)
    enriched = _enrich(sorted_)

    print(f"\n{'═'*60}")
    print(f"  Raw: {len(all_raw)}  │  Filtered: {len(filtered)}  │  After dedup: {len(enriched)}")
    print(f"  Online: {sum(1 for e in enriched if e.get('online'))}  │  TN Offline: {sum(1 for e in enriched if not e.get('online'))}")
    print(f"{'═'*60}")
    print_table(enriched)
    return 0


if __name__ == "__main__":
    sys.exit(main())
