import bcrypt
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
