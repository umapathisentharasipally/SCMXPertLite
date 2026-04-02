from fastapi import APIRouter, HTTPException, status, Depends,HTTPBearer, HTTPAuthorizationCredentials
import os
import jwt
from typing import Optional
from datetime import datetime, timedelta, timezone
import bcrypt

user_id = str(input("Enter user ID: "))
user_email = str(input("Enter user email: "))

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

async def get_current_user(token: str = Depends(HTTPBearer())):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return {"user_id": user_id, "email": email}
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
