from app.database import get_connection

class UserRepository:
    @staticmethod
    def get_by_email(email: str):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, email, password_hash, role FROM users WHERE email = %s;", (email,))
                return cur.fetchone()
        finally:
            conn.close()

    @staticmethod
    def get_by_id(user_id: int):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, email, role FROM users WHERE id = %s;", (user_id,))
                return cur.fetchone()
        finally:
            conn.close()
