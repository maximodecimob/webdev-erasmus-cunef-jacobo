import os
from itsdangerous import Signer, BadSignature
from dotenv import load_dotenv

load_dotenv()
SESSION_SECRET = os.getenv("SESSION_SECRET")
if not SESSION_SECRET:
    raise RuntimeError("SESSION_SECRET is not set. Put a long random string in the environment or in .env")
signer = Signer(SESSION_SECRET)

def create_session_token(user_id: int) -> str:
    return signer.sign(str(user_id)).decode("utf-8")

def verify_session_token(token: str) -> int | None:
    try:
        unsigned = signer.unsign(token)
        return int(unsigned.decode("utf-8"))
    except (BadSignature, ValueError, TypeError):
        return None
