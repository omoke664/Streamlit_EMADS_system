import os
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta
from db import get_user_collection

SECRET = os.getenv("RESET_SECRET_KEY")  # set in your .env
EXPIRES_SEC = 3600                     # 1 hour expiry

def _get_serializer():
    return URLSafeTimedSerializer(SECRET, salt="password-reset-salt")

def generate_reset_token(email: str) -> str:
    s = _get_serializer()
    token = s.dumps(email)
    # Store expiry in the user doc so you can optionally double‑check
    users = get_user_collection()
    users.update_one({"email": email},
                     {"$set": {
                        "reset_token": token,
                        "reset_expires": datetime.utcnow() + timedelta(seconds=EXPIRES_SEC)
                     }})
    return token

def verify_reset_token(token: str) -> str | None:
    s = _get_serializer()
    try:
        email = s.loads(token, max_age=EXPIRES_SEC)
    except Exception:
        return None
    # Optional DB double‑check:
    users = get_user_collection()
    u = users.find_one({"email": email, "reset_token": token})
    if not u or u.get("reset_expires", datetime.min) < datetime.utcnow():
        return None
    return email

