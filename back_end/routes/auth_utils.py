import re
import bcrypt
import jwt
import uuid
import os
import httpx
from typing import Optional
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from starlette import status

from back_end.routes.auth_config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ISSUER,
    RECAPTCHA_SECRET_KEY,
    RECAPTCHA_VERIFY_URL,
)

PASSWORD_REGEX = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=[\]{};:\'"\\|,.<>/?]).{8,}$'
)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update(
        {
            "iss": JWT_ISSUER,
            "sub": data.get("sub"),
            "iat": now,
            "nbf": now,
            "exp": expire,
            "jti": str(uuid.uuid4()),
        }
    )
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_reset_token(email: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=1)

    to_encode = {
        "iss": JWT_ISSUER,
        "sub": email,
        "iat": now,
        "nbf": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "type": "reset",
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def verify_recaptcha_token(recaptcha_token: str) -> None:
    if not RECAPTCHA_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="reCAPTCHA secret key is not configured",
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                RECAPTCHA_VERIFY_URL,
                data={"secret": RECAPTCHA_SECRET_KEY, "response": recaptcha_token},
                timeout=10.0,
            )
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to verify reCAPTCHA token",
        )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reCAPTCHA token",
        )

    score = result.get("score")
    if score is not None:
        try:
            threshold = float(os.environ.get("RECAPTCHA_SCORE_THRESHOLD", "0.5"))
        except ValueError:
            threshold = 0.5
        if score < threshold:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="reCAPTCHA verification failed due to low score",
            )