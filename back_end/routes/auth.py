from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
import jwt
import bcrypt

# This is what main.py looks for
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Jwt configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def get_db():
    # FIXED: Cleaned up the double AsyncIOMotorClient call
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db_name = os.environ.get("DB_NAME", "scmxpert_db")
    return client[db_name]

class SignupReuest(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class LoginRequest(BaseModel):
    email:EmailStr
    password:str

def hash_password(password: str) -> str:
    """Hash a password using bcrypt """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password:str, hashed_password:str) ->bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'),hashed_password.encode('utf-8'))


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupReuest):
    """Register a new user"""
    db = get_db()

    # check if user already exists
    existing_user = await db.users.find_one({"email": request.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # create new user
    user_id = str(uuid.uuid4())
    user_docs = {
        "id": user_id,
        "full_name": request.full_name,
        "email": request.email,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_docs)

    # Create access token 
    access_token = str(uuid.uuid4())
    user_response = UserResponse(
        id=user_id,
        full_name=request.full_name,
        email=request.email,
        created_at=user_docs["created_at"]
    )
    
    return TokenResponse(
        access_token=access_token,
        user=user_response
    )

#@router.post("/login", response_model=TokenResponse)
#async def login(request: LoginRequest):
