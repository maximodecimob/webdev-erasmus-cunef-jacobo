from app.errors import NotFound
from app.repositories.event_repo import EventRepository

def to_iso(value):
    """DB text 'YYYY-MM-DD HH:MM:SS' (UTC) -> '2026-11-10T21:00:00Z'."""
    return str(value).replace(" ", "T") + "Z"


class EventService:
    @staticmethod
    def list_upcoming_events():
        events = EventRepository.get_upcoming_events()
        result = []
        for e in events:
            result.append({
                "id": e["id"],
                "title": e["title"],
                "venue": e["venue"],
                "date": to_iso(e["date"]),
                "price": float(e["price"]),
                "total_tickets": e["total_tickets"],
                "tickets_left": e["tickets_left"]
            })
        return result

    @staticmethod
    def get_event(event_id):
        e = EventRepository.get_by_id(event_id)
        if e is None:
            raise NotFound("Event not found")
        return {
            "id": e["id"], "title": e["title"], "venue": e["venue"], "date": to_iso(e["date"]),
            "price": float(e["price"]), "total_tickets": e["total_tickets"], "tickets_left": e["tickets_left"],
        }
