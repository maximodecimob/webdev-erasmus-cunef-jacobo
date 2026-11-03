from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.services import google_auth
from app.utils import create_session_token

router = APIRouter()
COOKIE = "google_oauth"


@router.get("/auth/google")
async def google_start():
    if not google_auth.is_configured():
        return RedirectResponse("/login?error=google_not_configured", status_code=303)
    url, cookie = google_auth.start()
    response = RedirectResponse(url, status_code=303)
    response.set_cookie(COOKIE, cookie, max_age=600, httponly=True, samesite="lax", path="/auth/google")
    return response


@router.get("/auth/google/callback")
async def google_callback(request: Request, code: str = "", state: str = ""):
    user_id = google_auth.sign_in(code, state, request.cookies.get(COOKIE))
    if user_id is None:
        response = RedirectResponse("/login?error=google_failed", status_code=303)
    else:
        response = RedirectResponse("/events", status_code=303)
        response.set_cookie("vibe_session", create_session_token(user_id), httponly=True, samesite="lax", secure=False)
    response.delete_cookie(COOKIE, path="/auth/google")
    return response
