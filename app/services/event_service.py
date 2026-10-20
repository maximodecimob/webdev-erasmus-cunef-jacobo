from app.repositories.event_repo import EventRepository

class EventService:
    @staticmethod
    def list_upcoming_events():
        events = EventRepository.get_upcoming_events()
        # Format datetime or serialize as needed
        result = []
        for e in events:
            result.append({
                "id": e["id"],
                "title": e["title"],
                "venue": e["venue"],
                "date": e["date"].isoformat() if hasattr(e["date"], "isoformat") else str(e["date"]),
                "price": float(e["price"]),
                "total_tickets": e["total_tickets"],
                "tickets_left": e["tickets_left"]
            })
        return result
