from fastapi import APIRouter

from app.services.event_service import EventService

router = APIRouter()


@router.get("/api/events")
def api_events():
    return EventService.list_upcoming_events()


@router.get("/api/events/{event_id}")
def api_event(event_id: int):
    return EventService.get_event(event_id)
