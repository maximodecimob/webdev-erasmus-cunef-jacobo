import base64
import hashlib
import json
import logging
import os
import secrets
from urllib.parse import urlencode, urlparse

import httpx
from itsdangerous import BadData, URLSafeTimedSerializer

from app.database import IntegrityErrors
from app.errors import Conflict, Invalid, Unauthorized
from app.repositories.user_repo import UserRepository
from app.services.auth_service import ROLES
from app.utils import SESSION_SECRET

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
_serializer = URLSafeTimedSerializer(SESSION_SECRET, salt="google-oauth")
_signup = URLSafeTimedSerializer(SESSION_SECRET, salt="google-signup")


def is_configured() -> bool:
    return bool(os.getenv("GOOGLE_CLIENT_ID"))


def _base() -> str:
    return os.getenv("PUBLIC_BASE_URL", "http://localhost:3000").rstrip("/")


def _redirect_uri() -> str:
    return _base() + "/auth/google/callback"


def canonical_start(host):
    """The sign-in cookie only goes back to the host it was set for, so a sign-in started on another host
    (127.0.0.1 instead of localhost) must restart on the site address. None when the host is already right."""
    return None if urlparse(_base()).netloc == host else _base() + "/auth/google"


def start():
    """Return (google_url, cookie_value) for a new sign-in attempt."""
    state = secrets.token_urlsafe(24)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    url = AUTH_URL + "?" + urlencode({
        "client_id": os.getenv("GOOGLE_CLIENT_ID"), "redirect_uri": _redirect_uri(),
        "response_type": "code", "scope": "openid email", "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256"})
    return url, _serializer.dumps({"state": state, "verifier": verifier})


def exchange_code(code: str, verifier: str) -> dict:
    res = httpx.post(TOKEN_URL, timeout=20, data={
        "code": code, "code_verifier": verifier, "grant_type": "authorization_code",
        "client_id": os.getenv("GOOGLE_CLIENT_ID"), "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "redirect_uri": _redirect_uri()})
    res.raise_for_status()
    return res.json()


def sign_in(code, state, cookie):
    """Finish the sign-in. Returns (user_id, None) for an existing account, (None, signup_cookie) for an address
    with no account yet (the account is only created once the user picks a role), or (None, None) when anything is wrong."""
    try:
        saved = _serializer.loads(cookie or "", max_age=600)
        if not code or not secrets.compare_digest(saved["state"], state or ""):
            raise ValueError("missing code or the state does not match")
        payload = exchange_code(code, saved["verifier"])["id_token"].split(".")[1]
        # The token came straight from Google over TLS, so reading it without checking the signature is acceptable.
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        email, google_id = claims["email"].strip().lower(), claims["sub"]
    except Exception as error:
        logging.warning("google sign-in failed: %s", error)
        return None, None
    if claims.get("email_verified") is not True:
        logging.warning("google sign-in failed: the e-mail is not verified")
        return None, None

    user = UserRepository.get_by_google_id(google_id)
    if user:
        return user["id"], None
    user = UserRepository.get_by_email(email)
    if user:
        UserRepository.set_google_id(user["id"], google_id)
        return user["id"], None
    return None, _signup.dumps({"email": email, "google_id": google_id})


def _pending(cookie):
    try:
        return _signup.loads(cookie or "", max_age=600)
    except BadData:
        raise Unauthorized("Your Google sign-up expired. Please start again.")


def pending_email(cookie) -> str:
    return _pending(cookie)["email"]


def complete_signup(cookie, role) -> dict:
    """Create the account of a verified Google address with the role the user chose."""
    pending = _pending(cookie)
    if role not in ROLES:
        raise Invalid("Choose customer or organizer")
    try:
        user_id = UserRepository.create_google_user(pending["email"], pending["google_id"], role)
    except IntegrityErrors:
        raise Conflict("An account with this e-mail already exists")
    return {"id": user_id, "email": pending["email"], "role": role}
