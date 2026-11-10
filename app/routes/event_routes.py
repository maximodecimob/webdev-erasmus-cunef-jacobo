from fastapi import APIRouter, Response

from app.services.event_service import EventService

router = APIRouter()


@router.get("/api/events")
def api_events():
    return EventService.list_upcoming_events()


@router.get("/api/events/{event_id}")
def api_event(event_id: int):
    return EventService.get_event(event_id)


@router.get("/api/events/{event_id}/poster")
def api_poster(event_id: int):
    image, content_type = EventService.get_poster(event_id)
    return Response(content=image, media_type=content_type)
