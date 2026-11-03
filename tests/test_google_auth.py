import base64
import json
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.database import get_connection
from app.errors import AppError
from app.routes import google_routes
from app.services import google_auth

app = FastAPI()
app.include_router(google_routes.router)


@app.exception_handler(AppError)
def _handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status, content={"error": exc.message})


def _id_token(email, sub="g-123", verified=True):
    body = json.dumps({"email": email, "sub": sub, "email_verified": verified}).encode()
    return "h." + base64.urlsafe_b64encode(body).decode().rstrip("=") + ".s"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cid")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret")
    return TestClient(app)


def _start(client):
    res = client.get("/auth/google", follow_redirects=False)
    assert res.status_code == 303
    return res, parse_qs(urlparse(res.headers["location"]).query)["state"][0]


def _users():
    return get_connection().execute("SELECT id, email, role, google_id FROM users").fetchall()


def _google_login(client, monkeypatch, email, **kw):
    monkeypatch.setattr(google_auth, "exchange_code", lambda code, verifier: {"id_token": _id_token(email, **kw)})
    _, state = _start(client)
    return client.get(f"/auth/google/callback?code=abc&state={state}", follow_redirects=False)


def test_AC_7_start_redirects_to_google_with_pkce(client, world):
    """AC-7: start redirects to google with pkce"""
    res, _ = _start(client)
    q = parse_qs(urlparse(res.headers["location"]).query)
    assert res.headers["location"].startswith("https://accounts.google.com/o/oauth2/v2/auth")
    assert q["code_challenge_method"] == ["S256"] and q["response_type"] == ["code"]
    assert q["redirect_uri"] == ["http://localhost:3000/auth/google/callback"]


def test_AC_7_google_not_configured_redirects_to_login(monkeypatch, world):
    """AC-7: google not configured redirects to login"""
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "")
    res = TestClient(app).get("/auth/google", follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/login?error=google_not_configured"


def test_AC_7_existing_password_account_is_linked_not_duplicated(client, monkeypatch, world):
    """AC-7: existing password account is linked not duplicated"""
    before = len(_users())
    res = _google_login(client, monkeypatch, "customer@vibe.test")
    assert res.status_code == 303 and res.headers["location"] == "/events"
    assert "vibe_session" in res.cookies
    rows = _users()
    assert len(rows) == before
    assert [r["google_id"] for r in rows if r["id"] == world.customer["id"]] == ["g-123"]


def test_AC_7_returning_google_user_signs_in_to_same_row(client, monkeypatch, world):
    """AC-7: returning google user signs in to same row"""
    _google_login(client, monkeypatch, "customer@vibe.test")
    before = len(_users())
    res = _google_login(client, monkeypatch, "customer@vibe.test")
    assert "vibe_session" in res.cookies and len(_users()) == before


def test_AC_7_new_email_creates_one_customer(client, monkeypatch, world):
    """AC-7: new email creates one customer"""
    before = len(_users())
    res = _google_login(client, monkeypatch, "New@Gmail.com", sub="g-new")
    assert res.headers["location"] == "/events" and "vibe_session" in res.cookies
    rows = _users()
    assert len(rows) == before + 1
    new = [r for r in rows if r["google_id"] == "g-new"][0]
    assert new["email"] == "new@gmail.com" and new["role"] == "customer"


def test_AC_7_bad_state_is_rejected_without_session(client, monkeypatch, world):
    """AC-7: bad state is rejected without session"""
    monkeypatch.setattr(google_auth, "exchange_code", lambda code, verifier: pytest.fail("must not be called"))
    _start(client)
    res = client.get("/auth/google/callback?code=abc&state=wrong", follow_redirects=False)
    assert res.headers["location"] == "/login?error=google_failed"
    assert "vibe_session" not in res.cookies


def test_AC_7_missing_state_cookie_is_rejected(client, world):
    """AC-7: missing state cookie is rejected"""
    res = client.get("/auth/google/callback?code=abc&state=x", follow_redirects=False)
    assert res.headers["location"] == "/login?error=google_failed"


def test_AC_7_unverified_email_is_rejected(client, monkeypatch, world):
    """AC-7: unverified email is rejected"""
    before = len(_users())
    res = _google_login(client, monkeypatch, "customer@vibe.test", verified=False)
    assert res.headers["location"] == "/login?error=google_failed"
    assert "vibe_session" not in res.cookies and len(_users()) == before


def test_AC_7_failed_code_exchange_is_rejected(client, monkeypatch, world):
    """AC-7: failed code exchange is rejected"""
    def boom(code, verifier):
        raise RuntimeError("google down")
    monkeypatch.setattr(google_auth, "exchange_code", boom)
    _, state = _start(client)
    res = client.get(f"/auth/google/callback?code=abc&state={state}", follow_redirects=False)
    assert res.headers["location"] == "/login?error=google_failed"
