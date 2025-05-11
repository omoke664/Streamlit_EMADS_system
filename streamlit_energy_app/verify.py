# pass.py
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=['bcrypt'], deprecated='auto')

def hash_password(password: str) -> str:
    """Hash a plaintext password to a bcrypt string."""
    return pwd_ctx.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return pwd_ctx.verify(plain, hashed)