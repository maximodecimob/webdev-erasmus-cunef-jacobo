import datetime
import bcrypt
from app.database import get_connection, run_migrations

def seed_database():
    run_migrations()
    conn = get_connection()
    try:
        # Clean existing data for clean test runs
        conn.execute("DELETE FROM tickets;")
        conn.execute("DELETE FROM events;")
        conn.execute("DELETE FROM users;")

        # Hash test passwords
        customer_pw = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode("utf-8")
        organizer_pw = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode("utf-8")

        # Insert users
        cur = conn.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?);",
                           ("customer@vibe.test", customer_pw, "customer"))
        customer_id = cur.lastrowid

        cur = conn.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?);",
                           ("organizer@vibe.test", organizer_pw, "organizer"))
        organizer_id = cur.lastrowid

        # Insert 3 future events. Dates are stored as UTC text, like CURRENT_TIMESTAMP.
        now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0, tzinfo=None)
        events_data = [
            ("Techno Warehouse Madrid", "Garaje Club", now + datetime.timedelta(days=7), 20.00, 150, organizer_id),
            ("House Night Rooftop", "Terraza Sky", now + datetime.timedelta(days=14), 25.00, 80, organizer_id),
            ("Indie Pop Live", "Sala Sol", now + datetime.timedelta(days=21), 15.00, 200, organizer_id),
        ]

        for title, venue, date, price, total_tickets, org_id in events_data:
            conn.execute("""
                INSERT INTO events (title, venue, date, price, total_tickets, organizer_id)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (title, venue, date.strftime("%Y-%m-%d %H:%M:%S"), price, total_tickets, org_id))

        conn.commit()
        print("Database seeded successfully with 2 users and 3 future events.")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    seed_database()
