from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.services import google_auth
from app.utils import cookie_secure, create_session_token

router = APIRouter()
COOKIE = "google_oauth"
SIGNUP_COOKIE = "google_signup"
SIGNUP_PATH = "/api/auth/google"


@router.get("/auth/google")
async def google_start(request: Request):
    if not google_auth.is_configured():
        return RedirectResponse("/login?error=google_not_configured", status_code=303)
    restart = google_auth.canonical_start(request.headers.get("host"))
    if restart:
        return RedirectResponse(restart, status_code=303)
    url, cookie = google_auth.start()
    response = RedirectResponse(url, status_code=303)
    response.set_cookie(COOKIE, cookie, max_age=600, httponly=True, samesite="lax", path="/auth/google", secure=cookie_secure())
    return response


@router.get("/auth/google/callback")
async def google_callback(request: Request, code: str = "", state: str = ""):
    user_id, signup = google_auth.sign_in(code, state, request.cookies.get(COOKIE))
    if signup:
        response = RedirectResponse("/register/google", status_code=303)
        response.set_cookie(SIGNUP_COOKIE, signup, max_age=600, httponly=True, samesite="lax", path=SIGNUP_PATH, secure=cookie_secure())
    elif user_id is None:
        response = RedirectResponse("/login?error=google_failed", status_code=303)
    else:
        response = RedirectResponse("/events", status_code=303)
        response.set_cookie("vibe_session", create_session_token(user_id), httponly=True, samesite="lax", secure=cookie_secure())
    response.delete_cookie(COOKIE, path="/auth/google")
    return response


@router.get("/api/auth/google/pending")
async def google_pending(request: Request):
    return {"email": google_auth.pending_email(request.cookies.get(SIGNUP_COOKIE))}


@router.post("/api/auth/google/role", status_code=201)
async def google_role(request: Request, data: dict = Body(...)):
    user = google_auth.complete_signup(request.cookies.get(SIGNUP_COOKIE), data.get("role"))
    response = JSONResponse(status_code=201, content=user)
    response.set_cookie("vibe_session", create_session_token(user["id"]), httponly=True, samesite="lax", secure=cookie_secure())
    response.delete_cookie(SIGNUP_COOKIE, path=SIGNUP_PATH)
    return response
