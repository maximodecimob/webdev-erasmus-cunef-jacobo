from fastapi.testclient import TestClient

from app.main import app
from tests.test_ticket_api import login


def test_AC_35_the_email_is_not_case_sensitive_when_logging_in(world):
    """AC-35: the e-mail is not case sensitive when logging in"""
    res = TestClient(app).post("/login", data={"email": " Customer@Vibe.TEST ", "password": "secret123"}, follow_redirects=False)
    assert res.status_code == 303


def test_AC_36_a_signed_in_user_is_sent_from_login_and_register_to_the_events(world):
    """AC-36: a signed-in user is sent from login and register to the events, and a visitor still sees them"""
    client = login("organizer@vibe.test")
    for page in ("/login", "/register"):
        res = client.get(page, follow_redirects=False)
        assert res.status_code == 303 and res.headers["location"] == "/events"
        assert TestClient(app).get(page).status_code == 200
