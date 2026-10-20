import datetime
import bcrypt
from app.database import get_connection, run_migrations

def seed_database():
    run_migrations()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Clean existing data for clean test runs
            cur.execute("TRUNCATE TABLE tickets, events, users RESTART IDENTITY CASCADE;")
            
            # Hash test passwords
            customer_pw = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode("utf-8")
            organizer_pw = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode("utf-8")

            # Insert users
            cur.execute("""
                INSERT INTO users (email, password_hash, role)
                VALUES (%s, %s, %s) RETURNING id;
            """, ("customer@vibe.test", customer_pw, "customer"))
            customer_id = cur.fetchone()["id"]

            cur.execute("""
                INSERT INTO users (email, password_hash, role)
                VALUES (%s, %s, %s) RETURNING id;
            """, ("organizer@vibe.test", organizer_pw, "organizer"))
            organizer_id = cur.fetchone()["id"]

            # Insert 3 future events
            now = datetime.datetime.now(datetime.timezone.utc)
            events_data = [
                ("Techno Warehouse Madrid", "Garaje Club", now + datetime.timedelta(days=7), 20.00, 150, organizer_id),
                ("House Night Rooftop", "Terraza Sky", now + datetime.timedelta(days=14), 25.00, 80, organizer_id),
                ("Indie Pop Live", "Sala Sol", now + datetime.timedelta(days=21), 15.00, 200, organizer_id),
            ]

            for title, venue, date, price, total_tickets, org_id in events_data:
                cur.execute("""
                    INSERT INTO events (title, venue, date, price, total_tickets, organizer_id)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, (title, venue, date, price, total_tickets, org_id))

            conn.commit()
            print("Database seeded successfully with 2 users and 3 future events.")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    seed_database()
