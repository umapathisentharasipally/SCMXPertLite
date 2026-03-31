from fastapi import APIRouter, HTTPException, status
import os 
import jwt
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient 
from pydantic import BaseModel, EmailStr, Field
from back_end.routes.auth import get_db, verify_password

router = APIRouter(prefix="/api/login", tags=["Login"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
class LoginRequest(BaseModel):
        email: EmailStr
        password: str
class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    created_at: str

@router.post("/login",response_model=TokenResponse, status_code = status.HTTP_202_ACCEPTED)
async def login(email: EmailStr, password: str):
    """Authenticate user """
    db = get_db()
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"

        )
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    user_response = UserResponse(
        id=user["id"],
        full_name=user["full_name"],
        email=user["email"],
        created_at=user["created_at"]
    )
    return TokenResponse(
        access_token=user_response.id,
        token_type="bearer"
    )