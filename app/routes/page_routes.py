import os

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, RedirectResponse

from app.utils import verify_session_token

router = APIRouter()
STATIC = os.path.join("app", "static")


def page(name):
    return FileResponse(os.path.join(STATIC, name))


@router.get("/")
def home():
    return page("events.html")  # public (AC-13)


@router.get("/events")
def events_page(request: Request):
    token = request.cookies.get("vibe_session")
    if not (token and verify_session_token(token)):
        return RedirectResponse(url="/login", status_code=303)  # AC-9
    return page("events.html")


@router.get("/events/{event_id}")
def event_page(event_id: int):
    return page("event.html")


@router.get("/register")
def register_page():
    return page("register.html")


@router.get("/tickets")
def tickets_page():
    return page("tickets.html")


@router.get("/organizer")
def organizer_page():
    return page("organizer.html")
