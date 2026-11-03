from fastapi import Request

from app.errors import Unauthorized
from app.repositories.user_repo import UserRepository
from app.utils import verify_session_token


def current_user(request: Request):
    """The signed-in user from the session cookie, or a 401 (AC-14)."""
    token = request.cookies.get("vibe_session")
    user_id = verify_session_token(token) if token else None
    user = UserRepository.get_by_id(user_id) if user_id else None
    if user is None:
        raise Unauthorized()
    return user
