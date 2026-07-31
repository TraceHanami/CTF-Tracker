import json
import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_get_events(client):
    res = client.get("/api/events")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert isinstance(data["events"], list)


def test_get_stats(client):
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "total" in data
    assert "free" in data
    assert "online" in data


def test_teams_crud(client):
    # GET teams
    res = client.get("/api/teams")
    assert res.status_code == 200
    assert res.get_json()["success"] is True

    # POST team
    new_team = {"team": "Test Cyber Team", "lead": "Leader A", "members": ["Member 1", "Member 2"]}
    res = client.post("/api/teams", data=json.dumps(new_team), content_type="application/json")
    assert res.status_code == 200
    created = res.get_json()["team"]
    team_id = created["id"]
    assert created["team"] == "Test Cyber Team"

    # PUT team
    res = client.put(f"/api/teams/{team_id}", data=json.dumps({"team": "Test Cyber Team Altered"}), content_type="application/json")
    assert res.status_code == 200

    # DELETE team
    res = client.delete(f"/api/teams/{team_id}")
    assert res.status_code == 200


def test_events_crud(client):
    # POST event
    new_event = {
        "title": "Pytest Challenge 2026",
        "event_type": "CTF",
        "organizer": "Pytest Org",
        "price": 0,
        "mode": "Online",
        "date": "2026-12-01",
        "registration_link": "https://pytest.org",
    }
    res = client.post("/api/events", data=json.dumps(new_event), content_type="application/json")
    assert res.status_code == 200
    created = res.get_json()["event"]
    event_id = created["id"]

    # PUT event
    res = client.put(f"/api/events/{event_id}", data=json.dumps({"title": "Pytest Challenge 2026 Altered"}), content_type="application/json")
    assert res.status_code == 200

    # DELETE event
    res = client.delete(f"/api/events/{event_id}")
    assert res.status_code == 200
