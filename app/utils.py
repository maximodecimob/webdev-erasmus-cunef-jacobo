import os
from itsdangerous import Signer, BadSignature
from dotenv import load_dotenv

load_dotenv()
SESSION_SECRET = os.getenv("SESSION_SECRET", "change-me")
signer = Signer(SESSION_SECRET)

def create_session_token(user_id: int) -> str:
    return signer.sign(str(user_id)).decode("utf-8")

def verify_session_token(token: str) -> int | None:
    try:
        unsigned = signer.unsign(token)
        return int(unsigned.decode("utf-8"))
    except (BadSignature, ValueError, TypeError):
        return None
