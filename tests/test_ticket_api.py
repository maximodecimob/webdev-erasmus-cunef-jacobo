import pytest
from fastapi.testclient import TestClient

from app.main import app


def login(email):
    client = TestClient(app)
    res = client.post("/login", data={"email": email, "password": "secret123"}, follow_redirects=False)
    assert res.status_code == 303
    return client


@pytest.fixture
def event_id(world):
    return world.add_event(total_tickets=1)


def test_AC_13_visitor_sees_upcoming_events_and_the_home_page_without_login(world):
    """AC-13: visitor sees upcoming events and the home page without login"""
    visitor = TestClient(app)
    home = visitor.get("/", follow_redirects=False)
    assert home.status_code == 200
    events = visitor.get("/api/events")
    assert events.status_code == 200 and len(events.json()) == 3
    assert events.json()[0]["date"].endswith("Z")


def test_AC_14_buying_without_a_session_is_401_and_creates_nothing(world, event_id):
    """AC-14: buying without a session is 401 and creates nothing"""
    res = TestClient(app).post(f"/api/events/{event_id}/tickets")
    assert res.status_code == 401
    assert res.json() == {"error": "Please log in"}
    assert world.count_tickets() == 0


def test_AC_3_customer_buys_a_ticket_and_sees_it_in_my_tickets(world, event_id):
    """AC-3: customer buys a ticket and sees it in my tickets"""
    customer = login("customer@vibe.test")
    res = customer.post(f"/api/events/{event_id}/tickets")
    assert res.status_code == 201
    assert res.json()["code"].startswith("VIBE-")
    mine = customer.get("/api/tickets")
    assert mine.status_code == 200 and [t["event_id"] for t in mine.json()] == [event_id]


def test_AC_2_buying_a_sold_out_event_is_409(world, event_id):
    """AC-2: buying a sold out event is 409"""
    world.add_ticket(event_id, world.other["id"], "X")
    res = login("customer@vibe.test").post(f"/api/events/{event_id}/tickets")
    assert res.status_code == 409
    assert res.json() == {"error": "This event is sold out"}
    assert world.count_tickets() == 1


def test_AC_4_second_purchase_for_the_same_event_is_409(world):
    """AC-4: second purchase for the same event is 409"""
    event = world.add_event(total_tickets=5)
    customer = login("customer@vibe.test")
    assert customer.post(f"/api/events/{event}/tickets").status_code == 201
    assert customer.post(f"/api/events/{event}/tickets").status_code == 409


def test_AC_26_an_organizer_buying_is_403(world):
    """AC-26: an organizer buying is 403"""
    event = world.add_event()
    res = login("organizer@vibe.test").post(f"/api/events/{event}/tickets")
    assert res.status_code == 403
    assert world.count_tickets() == 0


def test_buying_an_unknown_event_is_404(world):
    assert login("customer@vibe.test").post("/api/events/9999/tickets").status_code == 404


def test_AC_16_cancel_without_session_is_401_and_other_customers_ticket_is_403(world):
    """AC-16: cancel without session is 401 and other customers ticket is 403"""
    event = world.add_event()
    ticket_id = world.add_ticket(event, world.customer["id"])
    assert TestClient(app).delete(f"/api/tickets/{ticket_id}").status_code == 401
    # a customer who is not the owner
    conn_other = TestClient(app)
    from app.utils import create_session_token
    conn_other.cookies.set("vibe_session", create_session_token(world.other["id"]))
    assert conn_other.delete(f"/api/tickets/{ticket_id}").status_code == 403
    assert len(login("customer@vibe.test").get("/api/tickets").json()) == 1


def test_AC_12_owner_cancels_with_204(world):
    """AC-12: owner cancels with 204"""
    event = world.add_event()
    ticket_id = world.add_ticket(event, world.customer["id"])
    customer = login("customer@vibe.test")
    assert customer.delete(f"/api/tickets/{ticket_id}").status_code == 204
    assert customer.get("/api/tickets").json() == []


def test_AC_17_cancelling_a_started_event_is_409(world):
    """AC-17: cancelling a started event is 409"""
    event = world.add_event(days=-1)
    ticket_id = world.add_ticket(event, world.customer["id"])
    res = login("customer@vibe.test").delete(f"/api/tickets/{ticket_id}")
    assert res.status_code == 409
    assert len(login("customer@vibe.test").get("/api/tickets").json()) == 1


def test_me_returns_the_user_or_401(world):
    assert TestClient(app).get("/api/me").status_code == 401
    me = login("organizer@vibe.test").get("/api/me")
    assert me.json()["role"] == "organizer"
