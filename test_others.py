import sys
from scrapers.unstop import get_unstop_events
from scrapers.hackerearth import get_hackerearth_events
from scrapers.mlh import get_mlh_events
from scrapers.devpost import get_devpost_events
from scrapers.dare2compete import get_dare2compete_events
from scrapers.india_offline import get_india_offline_events

scrapers = [
    ("Unstop", get_unstop_events),
    ("HackerEarth", get_hackerearth_events),
    ("MLH", get_mlh_events),
    ("Devpost", get_devpost_events),
    ("Dare2Compete", get_dare2compete_events),
    ("India Offline", get_india_offline_events),
]

for name, fn in scrapers:
    print(f"\nTesting {name} scraper...")
    try:
        events = fn()
        print(f"-> Success: Found {len(events)} events.")
        if events:
            print(f"   Sample Event: {events[0].get('title')} ({events[0].get('url')})")
    except Exception as e:
        print(f"-> Failed: {e}")
        import traceback
        traceback.print_exc()
