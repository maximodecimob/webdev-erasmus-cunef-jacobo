import re

import bcrypt

from app.errors import Conflict, Invalid
from app.database import IntegrityErrors
from app.repositories.user_repo import UserRepository

ROLES = ("customer", "organizer")


def _hash(password):
    if not isinstance(password, str) or len(password) < 8:
        raise Invalid("The password needs at least 8 characters")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


class AuthService:
    @staticmethod
    def authenticate(email: str, password: str):
        user = UserRepository.get_by_email((email or "").strip().lower())
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
        hashed = _hash(password)
        if role not in ROLES:
            raise Invalid("Choose customer or organizer")
        try:
            user_id = UserRepository.create(email, hashed, role)
        except IntegrityErrors:
            raise Conflict("An account with this e-mail already exists")
        return {"id": user_id, "email": email, "role": role}

    @staticmethod
    def account(user):
        row = UserRepository.get_by_email(user["email"])
        return {"id": user["id"], "email": user["email"], "role": user["role"],
                "has_password": bool(row["password_hash"]), "has_google": bool(row["google_id"])}

    @staticmethod
    def change_password(user, current, new):
        """A password account must give its current password; a Google-only account sets its first one."""
        row = UserRepository.get_by_email(user["email"])
        if row["password_hash"] and not (isinstance(current, str)
                                         and bcrypt.checkpw(current.encode("utf-8"), row["password_hash"].encode("utf-8"))):
            raise Invalid("The current password is wrong")
        UserRepository.set_password(user["id"], _hash(new))
