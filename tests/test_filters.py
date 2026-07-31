from datetime import datetime, timezone, timedelta
from core.filters import is_future, is_free, is_relevant_location, apply_all


def test_is_future():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d")

    assert is_future({"date": today}) is True
    assert is_future({"date": tomorrow}) is True
    assert is_future({"date": yesterday}) is False
    assert is_future({"date": "TBD"}) is True


def test_is_free():
    assert is_free({"fee": "free", "price": 0}) is True
    assert is_free({"fee": "₹0", "price": 0}) is True
    assert is_free({"fee": "₹1000", "price": 1000}) is False


def test_is_relevant_location():
    assert is_relevant_location({"online": True, "location": "Online"}) is True
    assert is_relevant_location({"online": False, "location": "Chennai, Tamil Nadu"}) is True
    assert is_relevant_location({"online": False, "location": "Bengaluru, Karnataka"}) is True
    assert is_relevant_location({"online": False, "location": "Delhi"}) is False


def test_apply_all():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
    events = [
        {"title": "Event 1", "date": today, "fee": "free", "price": 0, "online": True},
        {"title": "Event 2", "date": yesterday, "fee": "free", "price": 0, "online": True},
        {"title": "Event 3", "date": today, "fee": "₹1000", "price": 1000, "online": True},
    ]
    filtered = apply_all(events)
    assert len(filtered) == 1
    assert filtered[0]["title"] == "Event 1"
