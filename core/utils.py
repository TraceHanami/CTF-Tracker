"""core/utils.py — Shared helpers across scrapers."""
from __future__ import annotations
import time
import logging
import importlib.util
from datetime import datetime, timezone, timedelta

import requests

_loggers: dict[str, logging.Logger] = {}

def get_logger(name: str) -> logging.Logger:
    if name not in _loggers:
        logger = logging.getLogger(name)
        if not logger.handlers:
            h = logging.StreamHandler()
            h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
            logger.addHandler(h)
        logger.setLevel(logging.INFO)
        _loggers[name] = logger
    return _loggers[name]


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

logger = get_logger("utils")


def safe_get(url: str, *, params=None, timeout: int = 15, retries: int = 2) -> requests.Response | None:
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
            else:
                logger.warning("GET %s failed: %s", url, e)
    return None


def throttle(seconds: float = 1.0) -> None:
    time.sleep(seconds)


def window_timestamps(months: int = 3) -> tuple[int, int]:
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=months * 30)
    return int(now.timestamp()), int(end.timestamp())


_DATE_FMTS = [
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d",
    "%b %d, %Y",
    "%B %d, %Y",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d %Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
]


def parse_date(raw: str) -> str:
    if not raw:
        return "TBD"
    raw = raw.strip()
    for fmt in _DATE_FMTS:
        try:
            d = datetime.strptime(raw[:len(fmt) + 5], fmt)
            return d.strftime("%Y-%m-%d")
        except ValueError:
            pass
    # Try slicing ISO
    if "T" in raw:
        try:
            return raw[:10]
        except Exception:
            pass
    return "TBD"
