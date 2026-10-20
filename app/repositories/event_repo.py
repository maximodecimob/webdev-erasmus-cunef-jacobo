from app.database import get_connection

class EventRepository:
    @staticmethod
    def get_upcoming_events():
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT e.id, e.title, e.venue, e.date, e.price, e.total_tickets,
                           (e.total_tickets - COUNT(t.id)) AS tickets_left
                    FROM events e
                    LEFT JOIN tickets t ON e.id = t.event_id AND t.status = 'active'
                    WHERE e.date > CURRENT_TIMESTAMP
                    GROUP BY e.id
                    ORDER BY e.date ASC;
                """)
                return cur.fetchall()
        finally:
            conn.close()
