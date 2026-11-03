import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_connection
from app.seed import seed_database

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    seed_database()

def test_AC_9_visitor_redirected_to_login():
    """AC-9: visitor redirected to login"""
    response = client.get("/events", follow_redirects=False)
    assert response.status_code == 303
    assert "/login" in response.headers.get("location", "")

    # The events list itself is public since AC-13 (the home page shows it to visitors)
    assert client.get("/api/events").status_code == 200

def test_AC_10_signed_in_customer_sees_events():
    """AC-10: signed in customer sees events"""
    # Login first
    login_res = client.post("/login", data={"email": "customer@vibe.test", "password": "secret123"}, follow_redirects=False)
    assert login_res.status_code == 303
    
    # Get events API
    api_res = client.get("/api/events")
    assert api_res.status_code == 200
    events = api_res.json()
    assert len(events) == 3

    for ev in events:
        assert "title" in ev
        assert "date" in ev
        assert "tickets_left" in ev
        assert ev["title"] in ["Techno Warehouse Madrid", "House Night Rooftop", "Indie Pop Live"]

def test_AC_11_deleting_event_removes_it_from_screen():
    """AC-11: deleting event removes it from screen"""
    # Login first
    client.post("/login", data={"email": "customer@vibe.test", "password": "secret123"})

    # Check initially 3 events
    res1 = client.get("/api/events")
    assert len(res1.json()) == 3

    # Delete one event from database
    conn = get_connection()
    try:
        conn.execute("DELETE FROM events WHERE title = 'Indie Pop Live';")
        conn.commit()
    finally:
        conn.close()

    # Check now 2 events remain
    res2 = client.get("/api/events")
    assert res2.status_code == 200
    events = res2.json()
    assert len(events) == 2
    titles = [e["title"] for e in events]
    assert "Indie Pop Live" not in titles
