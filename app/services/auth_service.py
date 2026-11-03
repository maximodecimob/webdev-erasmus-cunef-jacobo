import re
import sqlite3

import bcrypt

from app.errors import Conflict, Invalid
from app.repositories.user_repo import UserRepository

class AuthService:
    @staticmethod
    def authenticate(email: str, password: str):
        user = UserRepository.get_by_email(email)
        if not user or not user["password_hash"]:
            return None
        
        if bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            return {"id": user["id"], "email": user["email"], "role": user["role"]}
        return None

    @staticmethod
    def register(email, password, role):
        email = (email or "").strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise Invalid("Enter a valid e-mail address")
        if not isinstance(password, str) or len(password) < 8:
            raise Invalid("The password needs at least 8 characters")
        if role not in ("customer", "organizer"):
            raise Invalid("Choose customer or organizer")
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        try:
            user_id = UserRepository.create(email, hashed, role)
        except sqlite3.IntegrityError:
            raise Conflict("An account with this e-mail already exists")
        return {"id": user_id, "email": email, "role": role}
