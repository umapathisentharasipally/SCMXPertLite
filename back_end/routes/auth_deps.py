from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timezone

from back_end.db.database import get_db
from back_end.routes.auth_config import (
    SECRET_KEY,
    ALGORITHM,
    JWT_ISSUER,
    COLL_LOGS,
    COLL_USERS,
)
from back_end.routes.auth_utils import verify_password
import jwt

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user."""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer=JWT_ISSUER,
            options={"require": ["exp", "iat", "nbf", "sub", "iss"]},
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    db = get_db()
    user = await db[COLL_USERS].find_one({"id": user_id}, {"_id": 0})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def admin_required(user: dict = Depends(get_current_user)):
    """A dependency that ensures the current user has the 'admin' role."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


async def super_admin_required(user: dict = Depends(get_current_user)):
    """A dependency that ensures the current user has the 'super_admin' role."""
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required")
    return user


async def log_login_attempt(db, email: str, success: bool, ip_address: str = None, user_agent: str = None):
    """Log login attempts to the logins collection."""
    log_entry = {
        "email": email,
        "success": success,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ip_address": ip_address,
        "user_agent": user_agent,
    }
    await db[COLL_LOGS].insert_one(log_entry)