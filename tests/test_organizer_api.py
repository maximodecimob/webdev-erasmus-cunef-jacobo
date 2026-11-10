import datetime

from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app
from tests.test_ticket_api import login


def future(days=10):
    when = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def payload(**over):
    base = {"title": "New Night", "venue": "Club X", "date": future(), "price": 12.5, "total_tickets": 50}
    return {**base, **over}


def count(table):
    return get_connection().execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]


def test_AC_18_register_signs_the_user_in(world):
    """AC-18: register signs the user in"""
    client = TestClient(app)
    res = client.post("/api/auth/register", json={"email": "new@vibe.test", "password": "longenough", "role": "organizer"})
    assert res.status_code == 201
    assert res.json()["role"] == "organizer"
    assert client.get("/api/me").json()["email"] == "new@vibe.test"


def test_AC_18_duplicate_email_is_409_and_adds_no_row(world):
    """AC-18: duplicate email is 409 and adds no row"""
    before = count("users")
    res = TestClient(app).post("/api/auth/register", json={"email": "customer@vibe.test", "password": "longenough", "role": "customer"})
    assert res.status_code == 409
    assert count("users") == before


def test_AC_18_weak_password_or_bad_role_is_422(world):
    """AC-18: weak password or bad role is 422"""
    client = TestClient(app)
    assert client.post("/api/auth/register", json={"email": "a@b.co", "password": "short", "role": "customer"}).status_code == 422
    assert client.post("/api/auth/register", json={"email": "a@b.co", "password": "longenough", "role": "admin"}).status_code == 422
    assert client.post("/api/auth/register", json={"email": "nope", "password": "longenough", "role": "customer"}).status_code == 422


def test_AC_19_organizer_creates_an_event_and_sees_it_in_their_list(world):
    """AC-19: organizer creates an event and sees it in their list"""
    org = login("organizer@vibe.test")
    res = org.post("/api/organizer/events", json=payload())
    assert res.status_code == 201
    mine = org.get("/api/organizer/events").json()
    assert "New Night" in [e["title"] for e in mine]
    assert all("tickets_sold" in e for e in mine)


def test_AC_19_customer_creating_an_event_is_403_and_visitor_401(world):
    """AC-19: customer creating an event is 403 and visitor 401"""
    before = count("events")
    assert login("customer@vibe.test").post("/api/organizer/events", json=payload()).status_code == 403
    assert TestClient(app).post("/api/organizer/events", json=payload()).status_code == 401
    assert count("events") == before


def test_AC_20_invalid_events_are_422_and_change_nothing(world):
    """AC-20: invalid events are 422 and change nothing"""
    org = login("organizer@vibe.test")
    before = count("events")
    for bad in (payload(date=future(-2)), payload(price=-1), payload(total_tickets=0), payload(title=""), payload(date="soon")):
        assert org.post("/api/organizer/events", json=bad).status_code == 422
    assert count("events") == before
    event_id = org.get("/api/organizer/events").json()[0]["id"]
    assert org.put(f"/api/organizer/events/{event_id}", json=payload(price=-5)).status_code == 422


def test_AC_21_another_organizers_event_cannot_be_edited_or_deleted(world, second_organizer):
    """AC-21: another organizers event cannot be edited or deleted"""
    event_id = world.add_event(title="Mine")
    other = TestClient(app)
    other.cookies.set("vibe_session", second_organizer.token)
    assert other.put(f"/api/organizer/events/{event_id}", json=payload(title="Hacked")).status_code == 403
    assert other.delete(f"/api/organizer/events/{event_id}").status_code == 403
    titles = [e["title"] for e in login("organizer@vibe.test").get("/api/organizer/events").json()]
    assert "Mine" in titles and "Hacked" not in titles


def test_AC_22_lowering_total_below_sold_is_409(world):
    """AC-22: lowering total below sold is 409"""
    event_id = world.add_event(total_tickets=5)
    world.add_ticket(event_id, world.customer["id"], "A")
    world.add_ticket(event_id, world.other["id"], "B")
    org = login("organizer@vibe.test")
    assert org.put(f"/api/organizer/events/{event_id}", json=payload(total_tickets=1)).status_code == 409
    assert org.put(f"/api/organizer/events/{event_id}", json=payload(total_tickets=2)).status_code == 200
    total = next(e for e in org.get("/api/organizer/events").json() if e["id"] == event_id)["total_tickets"]
    assert total == 2


def test_organizer_deletes_own_event_with_204(world):
    event_id = world.add_event()
    assert login("organizer@vibe.test").delete(f"/api/organizer/events/{event_id}").status_code == 204
    assert login("organizer@vibe.test").get(f"/api/events/{event_id}").status_code == 404


def test_AC_6_only_the_events_organizer_sees_attendees(world, second_organizer):
    """AC-6: only the events organizer sees attendees"""
    event_id = world.add_event()
    world.add_ticket(event_id, world.customer["id"], "CODE-1")
    seen = login("organizer@vibe.test").get(f"/api/events/{event_id}/attendees")
    assert seen.status_code == 200
    assert seen.json()[0]["email"] == "customer@vibe.test" and seen.json()[0]["code"] == "CODE-1"
    assert login("customer@vibe.test").get(f"/api/events/{event_id}/attendees").status_code == 403
    other = TestClient(app)
    other.cookies.set("vibe_session", second_organizer.token)
    assert other.get(f"/api/events/{event_id}/attendees").status_code == 403
    assert TestClient(app).get(f"/api/events/{event_id}/attendees").status_code == 401


PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 20


def upload(client, event_id, content=PNG, content_type="image/png"):
    return client.post(f"/api/organizer/events/{event_id}/poster", files={"image": ("p.png", content, content_type)})


def test_AC_27_an_uploaded_poster_is_served_and_flagged_on_the_event(world):
    """AC-27: an uploaded poster is served and flagged on the event"""
    client = login("organizer@vibe.test")
    event_id = world.add_event()
    assert client.get(f"/api/events/{event_id}").json()["has_poster"] is False
    assert upload(client, event_id).status_code == 200
    assert client.get(f"/api/events/{event_id}").json()["has_poster"] is True
    res = TestClient(app).get(f"/api/events/{event_id}/poster")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    assert res.content == PNG


def test_AC_27_a_file_that_is_not_an_image_is_422_and_stores_nothing(world):
    """AC-27: a file that is not an image is 422 and stores nothing"""
    client = login("organizer@vibe.test")
    event_id = world.add_event()
    assert upload(client, event_id, b"hello", "text/plain").status_code == 422
    assert TestClient(app).get(f"/api/events/{event_id}/poster").status_code == 404


def test_AC_27_only_the_owner_can_set_a_poster(world):
    """AC-27: only the owner can set a poster"""
    event_id = world.add_event()
    assert upload(login("customer@vibe.test"), event_id).status_code == 403
    assert TestClient(app).get(f"/api/events/{event_id}/poster").status_code == 404
