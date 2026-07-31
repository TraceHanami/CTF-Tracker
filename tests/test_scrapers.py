from scrapers.ctftime import get_ctf_events
from scrapers.devpost import get_devpost_events
from scrapers.mlh import get_mlh_events
from scrapers.india_offline import get_india_offline_events


def test_ctftime_scraper():
    events = get_ctf_events()
    assert isinstance(events, list)
    if events:
        assert "title" in events[0]
        assert "date" in events[0]


def test_devpost_scraper():
    events = get_devpost_events()
    assert isinstance(events, list)


def test_mlh_scraper():
    events = get_mlh_events()
    assert isinstance(events, list)


def test_india_offline_scraper():
    events = get_india_offline_events()
    assert isinstance(events, list)
