from fastapi import Request

from app.errors import Unauthorized
from app.repositories.user_repo import UserRepository
from app.utils import verify_session_token


def session_user(request: Request):
    """The user of the session cookie, or None."""
    token = request.cookies.get("vibe_session")
    user_id = verify_session_token(token) if token else None
    return UserRepository.get_by_id(user_id) if user_id else None


def current_user(request: Request):
    """The signed-in user from the session cookie, or a 401 (AC-14)."""
    user = session_user(request)
    if user is None:
        raise Unauthorized()
    return user
