import jwt
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from back_end.db.database import get_db
from back_end.config import SECRET_KEY, ALGORITHM, JWT_ISSUER

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> dict:
    """Get current authenticated user from JWT token."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer=JWT_ISSUER,
            options={"verify_exp": True, "verify_iss": True}
        )

        user_id = payload.get("sub")

        if not user_id:
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except jwt.InvalidTokenError:
        raise credentials_exception

    user = await db["users"].find_one({"id": user_id})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


def admin_required(current_user: dict = Depends(get_current_user)) -> dict:
    """Require admin or super_admin role."""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


def super_admin_required(current_user: dict = Depends(get_current_user)) -> dict:
    """Require super_admin role only."""
    if current_user.get("role") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required"
        )
    return current_user


async def log_login_attempt(
    db: AsyncIOMotorDatabase,
    email: str,
    success: bool,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Dict[str, Any]:
    """Log login attempt to MongoDB."""

    if not email or not email.strip():
        return {
            "status": "error",
            "message": "Email is required"
        }

    login_record = {
        "email": email.strip().lower(),
        "success": bool(success),
        "ip_address": ip_address or "unknown",
        "user_agent": user_agent or "unknown",
        "timestamp": datetime.now(timezone.utc)
    }

    try:
        result = await db["logins"].insert_one(login_record)

        return {
            "status": "success",
            "inserted_id": str(result.inserted_id)
        }

    except PyMongoError as e:
        logger.error(f"MongoDB error while logging login attempt: {e}")

        return {
            "status": "error",
            "message": "Failed to log login attempt"
        }