import os
import jwt
import re
from datetime import datetime, timezone, timedelta
from typing import Optional
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Password regex for validation
PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
)

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
JWT_ISSUER = "scmxpertlite"


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=24)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": JWT_ISSUER,
        "type": "access"
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_reset_token(email: str) -> str:
    """Create a password reset JWT token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    payload = {
        "sub": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": JWT_ISSUER,
        "type": "reset"
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def verify_recaptcha_token(token: str) -> bool:
    """
    Verify reCAPTCHA token. 
    In production, verify with Google reCAPTCHA API.
    For now, returns True if token exists.
    """
    # TODO: Implement actual reCAPTCHA verification
    # import httpx
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(
    #         "https://www.google.com/recaptcha/api/siteverify",
    #         data={"secret": os.getenv("RECAPTCHA_SECRET"), "response": token}
    #     )
    #     return response.json().get("success", False)
    
    return bool(token)