from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app
from tests.test_ticket_api import login


def _password_works(email, password):
    return TestClient(app).post("/login", data={"email": email, "password": password}, follow_redirects=False).status_code == 303


def test_AC_33_the_account_page_data_needs_a_session_and_says_how_the_user_signs_in(world):
    """AC-33: account data needs a session and says how the user signs in"""
    assert TestClient(app).get("/api/account").status_code == 401
    assert login("customer@vibe.test").get("/api/account").json() == {
        "id": world.customer["id"], "email": "customer@vibe.test", "role": "customer", "has_password": True, "has_google": False}


def test_AC_33_changing_the_password_needs_the_current_one_and_a_long_enough_new_one(world):
    """AC-33: changing the password needs the current one and a long enough new one"""
    client = login("customer@vibe.test")
    change = lambda **body: client.post("/api/auth/password", json=body)
    assert change(current_password="wrong-one", new_password="brand-new-pass").status_code == 422
    assert change(new_password="brand-new-pass").status_code == 422
    assert change(current_password="secret123", new_password="short").status_code == 422
    assert _password_works("customer@vibe.test", "secret123")
    assert change(current_password="secret123", new_password="brand-new-pass").status_code == 204
    assert _password_works("customer@vibe.test", "brand-new-pass") and not _password_works("customer@vibe.test", "secret123")


def test_AC_33_changing_the_password_without_a_session_is_401_and_changes_nothing(world):
    """AC-33: changing the password without a session is 401 and changes nothing"""
    res = TestClient(app).post("/api/auth/password", json={"current_password": "secret123", "new_password": "brand-new-pass"})
    assert res.status_code == 401 and _password_works("customer@vibe.test", "secret123")


def test_AC_33_a_google_only_account_can_set_a_first_password(world):
    """AC-33: a google-only account can set a first password"""
    conn = get_connection()
    conn.execute("INSERT INTO users (email, password_hash, role, google_id) VALUES ('g@vibe.test', NULL, 'customer', 'g-1')")
    conn.commit()
    conn.close()
    from app.utils import create_session_token
    from app.repositories.user_repo import UserRepository
    client = TestClient(app)
    client.cookies.set("vibe_session", create_session_token(UserRepository.get_by_email("g@vibe.test")["id"]))
    assert client.get("/api/account").json()["has_google"] is True
    assert client.get("/api/account").json()["has_password"] is False
    assert client.post("/api/auth/password", json={"new_password": "first-password"}).status_code == 204
    assert _password_works("g@vibe.test", "first-password")
