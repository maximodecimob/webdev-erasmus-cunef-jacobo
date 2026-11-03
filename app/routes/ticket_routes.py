from fastapi import APIRouter, Depends, Response

from app.deps import current_user
from app.services import ticket_service

router = APIRouter()


@router.post("/api/events/{event_id}/tickets", status_code=201)
def buy(event_id: int, user=Depends(current_user)):
    return ticket_service.buy_ticket(user, event_id)


@router.get("/api/tickets")
def my_tickets(user=Depends(current_user)):
    return ticket_service.my_tickets(user)


@router.delete("/api/tickets/{ticket_id}", status_code=204)
def cancel(ticket_id: int, user=Depends(current_user)):
    ticket_service.cancel_ticket(user, ticket_id)
    return Response(status_code=204)
