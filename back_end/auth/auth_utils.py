import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import jwt
import httpx
from passlib.context import CryptContext

from back_end.config import (
    SECRET_KEY,
    ALGORITHM,
    JWT_ISSUER,
    RECAPTCHA_SECRET,
    RECAPTCHA_VERIFY_URL
)

logger = logging.getLogger(__name__)

# bcrypt password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
)


def validate_password(password: str) -> bool:
    """Validate password strength."""
    if not password:
        return False
    return bool(PASSWORD_REGEX.match(password))


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    if not password:
        raise ValueError("Password is required")

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt."""
    if not plain_password or not hashed_password:
        return False

    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""

    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(hours=24))

    payload = data.copy()
    payload.update({
        "exp": expire,
        "iat": now,
        "iss": JWT_ISSUER,
        "type": "access"
    })

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_reset_token(email: str) -> str:
    """Create password reset token."""

    now = datetime.now(timezone.utc)

    payload = {
        "sub": email.strip().lower(),
        "exp": now + timedelta(minutes=15),
        "iat": now,
        "iss": JWT_ISSUER,
        "type": "reset"
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def verify_recaptcha_token(
    token: str,
    remote_ip: Optional[str] = None,
    expected_action: Optional[str] = None,
    min_score: float = 0.5
) -> bool:
    """Verify Google reCAPTCHA token."""

    if not token:
        return False

    if not RECAPTCHA_SECRET:
        logger.error("RECAPTCHA_SECRET is missing")
        return False

    try:
        payload = {
            "secret": RECAPTCHA_SECRET,
            "response": token
        }

        if remote_ip:
            payload["remoteip"] = remote_ip

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                RECAPTCHA_VERIFY_URL,
                data=payload
            )

        response.raise_for_status()
        result = response.json()

        if not result.get("success"):
            logger.warning(f"reCAPTCHA failed: {result.get('error-codes')}")
            return False

        score = result.get("score")
        action = result.get("action")

        if score is not None and score < min_score:
            return False

        if expected_action and action != expected_action:
            return False

        return True

    except httpx.HTTPError as e:
        logger.error(f"reCAPTCHA HTTP error: {e}")
        return False

    except Exception as e:
        logger.exception(f"Unexpected reCAPTCHA error: {e}")
        return False