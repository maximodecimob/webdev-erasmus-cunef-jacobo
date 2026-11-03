import datetime

from app.errors import Conflict, Invalid, NotAllowed, NotFound
from app.repositories.event_repo import EventRepository
from app.repositories.ticket_repo import TicketRepository
from app.services.event_service import to_iso


def require_organizer(user):
    if user["role"] != "organizer":
        raise NotAllowed("This area is for organizers")


def _own_event(user, event_id):
    require_organizer(user)
    event = EventRepository.get_by_id(event_id)
    if event is None:
        raise NotFound("Event not found")
    if event["organizer_id"] != user["id"]:
        raise NotAllowed("This is not your event")
    return event


def _clean(data):
    """Validate an event payload (AC-20) and return the values as stored."""
    title = str(data.get("title") or "").strip()
    venue = str(data.get("venue") or "").strip()
    if not title or not venue:
        raise Invalid("Title and venue are required")
    try:
        when = datetime.datetime.fromisoformat(str(data.get("date")).replace("Z", "+00:00"))
        if when.tzinfo is None:
            when = when.replace(tzinfo=datetime.timezone.utc)
        when = when.astimezone(datetime.timezone.utc)
    except ValueError:
        raise Invalid("Enter a valid date and time")
    if when <= datetime.datetime.now(datetime.timezone.utc):
        raise Invalid("The date must be in the future")
    price, total = data.get("price"), data.get("total_tickets")
    if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
        raise Invalid("The price must be 0 or more")
    if isinstance(total, bool) or not isinstance(total, int) or total < 1:
        raise Invalid("There must be at least 1 ticket")
    return title, venue, when.strftime("%Y-%m-%d %H:%M:%S"), float(price), total


def list_own(user):
    require_organizer(user)
    return [{**e, "date": to_iso(e["date"]), "price": float(e["price"])}
            for e in EventRepository.list_by_organizer(user["id"])]


def create(user, data):
    require_organizer(user)
    event_id = EventRepository.create(user["id"], *_clean(data))
    return {"id": event_id}


def update(user, event_id, data):
    event = _own_event(user, event_id)
    values = _clean(data)
    sold = event["total_tickets"] - event["tickets_left"]
    if values[4] < sold:
        raise Conflict(f"{sold} tickets are already sold, so the total cannot go below {sold}")
    EventRepository.update(event_id, *values)
    return {"id": event_id}


def delete(user, event_id):
    _own_event(user, event_id)
    EventRepository.delete(event_id)


def attendees(user, event_id):
    _own_event(user, event_id)
    return [dict(a) for a in TicketRepository.list_attendees(event_id)]
