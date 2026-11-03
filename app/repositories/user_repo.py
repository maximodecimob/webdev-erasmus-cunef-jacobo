from app.database import get_connection

class UserRepository:
    @staticmethod
    def get_by_email(email: str):
        conn = get_connection()
        try:
            return conn.execute("SELECT id, email, password_hash, role FROM users WHERE email = ?;", (email,)).fetchone()
        finally:
            conn.close()

    @staticmethod
    def get_by_id(user_id: int):
        conn = get_connection()
        try:
            return conn.execute("SELECT id, email, role FROM users WHERE id = ?;", (user_id,)).fetchone()
        finally:
            conn.close()

    @staticmethod
    def create(email: str, password_hash: str, role: str):
        conn = get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?);", (email, password_hash, role))
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    @staticmethod
    def get_by_google_id(google_id: str):
        conn = get_connection()
        try:
            return conn.execute("SELECT id, email, role FROM users WHERE google_id = ?;", (google_id,)).fetchone()
        finally:
            conn.close()

    @staticmethod
    def set_google_id(user_id: int, google_id: str):
        conn = get_connection()
        try:
            conn.execute("UPDATE users SET google_id = ? WHERE id = ?;", (google_id, user_id))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def create_google_user(email: str, google_id: str):
        conn = get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO users (email, password_hash, role, google_id) VALUES (?, NULL, 'customer', ?);",
                (email, google_id))
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()
