# auth.py
import jwt
import os
from datetime import datetime, timedelta
from streamlit_cookies_manager import EncryptedCookieManager

# load .env
from dotenv import load_dotenv
load_dotenv()

SECRET    = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
EXP_DAYS  = int(os.getenv("JWT_EXP_DAYS", "7"))

# initialize at import time; in your main.py you'll do `cookies = EncryptedCookieManager(...)`
cookies = EncryptedCookieManager(
    prefix="emads_",  # cookie name prefix
    password=os.getenv("COOKIE_PASSWORD"),  # 16‐32 chars PW for encrypting cookies
)

def make_token(user_dict: dict) -> str:
    exp = datetime.utcnow() + timedelta(days=EXP_DAYS)
    payload = {"user": user_dict, "exp": exp}
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)

def parse_token(token: str):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload["user"]
    except jwt.PyJWTError:
        return None

def login_user(user: dict):
    """Call after successful password check."""
    token = make_token(user)
    # set & persist cookie
    cookies["auth_token"] = token
    cookies.save()  # ensure it’s written

def logout_user():
    cookies.pop("auth_token", None)
    cookies.save()

def get_current_user():
    """Try recovering user from cookie at app startup."""
    token = cookies.get("auth_token")
    if not token:
        return None
    return parse_token(token)

