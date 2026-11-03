import base64
import hashlib
import json
import os
import secrets
from urllib.parse import urlencode

import httpx
from itsdangerous import URLSafeTimedSerializer

from app.repositories.user_repo import UserRepository
from app.utils import SESSION_SECRET

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
_serializer = URLSafeTimedSerializer(SESSION_SECRET, salt="google-oauth")


def is_configured() -> bool:
    return bool(os.getenv("GOOGLE_CLIENT_ID"))


def _redirect_uri() -> str:
    return os.getenv("PUBLIC_BASE_URL", "http://localhost:3000").rstrip("/") + "/auth/google/callback"


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
    res = httpx.post(TOKEN_URL, timeout=10, data={
        "code": code, "code_verifier": verifier, "grant_type": "authorization_code",
        "client_id": os.getenv("GOOGLE_CLIENT_ID"), "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "redirect_uri": _redirect_uri()})
    res.raise_for_status()
    return res.json()


def sign_in(code, state, cookie) -> int | None:
    """Finish the sign-in. Returns the user id, or None when anything is wrong."""
    try:
        saved = _serializer.loads(cookie or "", max_age=600)
        if not code or not secrets.compare_digest(saved["state"], state or ""):
            return None
        payload = exchange_code(code, saved["verifier"])["id_token"].split(".")[1]
        # The token came straight from Google over TLS, so reading it without checking the signature is acceptable.
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        email, google_id = claims["email"].strip().lower(), claims["sub"]
    except Exception:
        return None
    if claims.get("email_verified") is not True:
        return None

    user = UserRepository.get_by_google_id(google_id)
    if user:
        return user["id"]
    user = UserRepository.get_by_email(email)
    if user:
        UserRepository.set_google_id(user["id"], google_id)
        return user["id"]
    return UserRepository.create_google_user(email, google_id)
