import secrets
from app.database import IntegrityErrors
from app.errors import AlreadyHolds, EventStarted, NotAllowed, NotFound, SoldOut
from app.repositories.event_repo import EventRepository
from app.repositories.ticket_repo import TicketRepository
from app.services.event_service import to_iso


def buy_ticket(user, event_id):
    if user["role"] != "customer":
        raise NotAllowed("Only customers can buy tickets")
    event = EventRepository.get_by_id(event_id)
    if event is None:
        raise NotFound("Event not found")
    if event["started"]:
        raise EventStarted()
    if TicketRepository.has_active(event_id, user["id"]):
        raise AlreadyHolds()
    if event["tickets_left"] <= 0:
        raise SoldOut()
    code = "VIBE-" + secrets.token_hex(4).upper()
    try:
        ticket_id = TicketRepository.create(event_id, user["id"], code)
    except IntegrityErrors:  # two clicks at once: the unique index wins
        raise AlreadyHolds()
    if ticket_id is None:  # the insert refused: someone took the last place first
        raise SoldOut()
    return {"id": ticket_id, "code": code, "event_id": event_id, "status": "active"}


def my_tickets(user):
    return [{**t, "date": to_iso(t["date"])} for t in TicketRepository.list_for_customer(user["id"])]


def cancel_ticket(user, ticket_id):
    ticket = TicketRepository.get_by_id(ticket_id)
    if ticket is None or ticket["status"] != "active":
        raise NotFound("Ticket not found")
    if ticket["customer_id"] != user["id"]:
        raise NotAllowed("This ticket is not yours")
    if EventRepository.get_by_id(ticket["event_id"])["started"]:
        raise EventStarted("This event has already started, so the ticket cannot be cancelled")
    TicketRepository.cancel(ticket_id)
