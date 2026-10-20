import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.utils import verify_session_token
from app.services.event_service import EventService

router = APIRouter()

@router.get("/events")
async def events_page(request: Request):
    token = request.cookies.get("vibe_session")
    user_id = verify_session_token(token) if token else None
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    
    events_html_path = os.path.join("app", "static", "events.html")
    if os.path.exists(events_html_path):
        with open(events_html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<html><body><h1>Upcoming Events</h1></body></html>"

@router.get("/api/events")
async def api_events(request: Request):
    token = request.cookies.get("vibe_session")
    user_id = verify_session_token(token) if token else None
    if not user_id:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    
    events = EventService.list_upcoming_events()
    return events
