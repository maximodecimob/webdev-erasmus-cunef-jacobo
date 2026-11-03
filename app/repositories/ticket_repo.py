from app.database import get_connection


class TicketRepository:
    @staticmethod
    def create(event_id: int, customer_id: int, code: str):
        conn = get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO tickets (event_id, customer_id, code) VALUES (?, ?, ?);",
                (event_id, customer_id, code))
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    @staticmethod
    def has_active(event_id: int, customer_id: int) -> bool:
        conn = get_connection()
        try:
            return conn.execute(
                "SELECT 1 FROM tickets WHERE event_id = ? AND customer_id = ? AND status = 'active';",
                (event_id, customer_id)).fetchone() is not None
        finally:
            conn.close()

    @staticmethod
    def get_by_id(ticket_id: int):
        conn = get_connection()
        try:
            return conn.execute(
                "SELECT id, event_id, customer_id, code, status FROM tickets WHERE id = ?;",
                (ticket_id,)).fetchone()
        finally:
            conn.close()

    @staticmethod
    def list_for_customer(customer_id: int):
        conn = get_connection()
        try:
            return conn.execute("""
                SELECT t.id, t.code, t.status, t.event_id, e.title, e.venue, e.date
                FROM tickets t JOIN events e ON e.id = t.event_id
                WHERE t.customer_id = ? AND t.status = 'active'
                ORDER BY e.date ASC;
            """, (customer_id,)).fetchall()
        finally:
            conn.close()

    @staticmethod
    def cancel(ticket_id: int):
        conn = get_connection()
        try:
            conn.execute("UPDATE tickets SET status = 'cancelled' WHERE id = ?;", (ticket_id,))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def list_attendees(event_id: int):
        conn = get_connection()
        try:
            return conn.execute("""
                SELECT u.email, t.code, t.created_at
                FROM tickets t JOIN users u ON u.id = t.customer_id
                WHERE t.event_id = ? AND t.status = 'active'
                ORDER BY t.created_at ASC;
            """, (event_id,)).fetchall()
        finally:
            conn.close()
