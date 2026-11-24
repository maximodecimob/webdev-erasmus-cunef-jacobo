from fastapi import APIRouter, Body, Depends, File, Response, UploadFile

from app.deps import current_user
from app.services import organizer_service, poster

router = APIRouter()


@router.get("/api/organizer/events")
def list_own(user=Depends(current_user)):
    return organizer_service.list_own(user)


@router.post("/api/organizer/events", status_code=201)
def create(data: dict = Body(...), user=Depends(current_user)):
    return organizer_service.create(user, data)


@router.put("/api/organizer/events/{event_id}")
def update(event_id: int, data: dict = Body(...), user=Depends(current_user)):
    return organizer_service.update(user, event_id, data)


@router.delete("/api/organizer/events/{event_id}", status_code=204)
def delete(event_id: int, user=Depends(current_user)):
    organizer_service.delete(user, event_id)
    return Response(status_code=204)


@router.get("/api/events/{event_id}/attendees")
def attendees(event_id: int, user=Depends(current_user)):
    return organizer_service.attendees(user, event_id)


@router.post("/api/organizer/poster")
async def read_poster(image: UploadFile = File(...), user=Depends(current_user)):
    organizer_service.require_organizer(user)
    return poster.read_poster(await image.read(), image.content_type or "image/png")


@router.post("/api/organizer/events/{event_id}/poster")
async def set_poster(event_id: int, image: UploadFile = File(...), user=Depends(current_user)):
    return organizer_service.set_poster(user, event_id, await image.read(), image.content_type or "")
