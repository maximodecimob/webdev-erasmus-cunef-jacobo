from app.database import get_connection

class EventRepository:
    @staticmethod
    def get_upcoming_events():
        conn = get_connection()
        try:
            return conn.execute("""
                SELECT e.id, e.title, e.venue, e.date, e.price, e.total_tickets,
                       (e.total_tickets - COUNT(t.id)) AS tickets_left
                FROM events e
                LEFT JOIN tickets t ON e.id = t.event_id AND t.status = 'active'
                WHERE e.date > CURRENT_TIMESTAMP
                GROUP BY e.id
                ORDER BY e.date ASC;
            """).fetchall()
        finally:
            conn.close()

    @staticmethod
    def get_by_id(event_id: int):
        conn = get_connection()
        try:
            return conn.execute("""
                SELECT e.id, e.title, e.venue, e.date, e.price, e.total_tickets, e.organizer_id,
                       (e.total_tickets - COUNT(t.id)) AS tickets_left,
                       (e.date <= CURRENT_TIMESTAMP) AS started
                FROM events e
                LEFT JOIN tickets t ON e.id = t.event_id AND t.status = 'active'
                WHERE e.id = ?
                GROUP BY e.id;
            """, (event_id,)).fetchone()
        finally:
            conn.close()

    @staticmethod
    def list_by_organizer(organizer_id: int):
        conn = get_connection()
        try:
            return conn.execute("""
                SELECT e.id, e.title, e.venue, e.date, e.price, e.total_tickets, COUNT(t.id) AS tickets_sold
                FROM events e
                LEFT JOIN tickets t ON e.id = t.event_id AND t.status = 'active'
                WHERE e.organizer_id = ?
                GROUP BY e.id
                ORDER BY e.date ASC;
            """, (organizer_id,)).fetchall()
        finally:
            conn.close()

    @staticmethod
    def create(organizer_id: int, title, venue, date, price, total_tickets):
        conn = get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO events (title, venue, date, price, total_tickets, organizer_id) VALUES (?, ?, ?, ?, ?, ?);",
                (title, venue, date, price, total_tickets, organizer_id))
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    @staticmethod
    def update(event_id: int, title, venue, date, price, total_tickets):
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE events SET title = ?, venue = ?, date = ?, price = ?, total_tickets = ? WHERE id = ?;",
                (title, venue, date, price, total_tickets, event_id))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def delete(event_id: int):
        conn = get_connection()
        try:
            conn.execute("DELETE FROM events WHERE id = ?;", (event_id,))
            conn.commit()
        finally:
            conn.close()
