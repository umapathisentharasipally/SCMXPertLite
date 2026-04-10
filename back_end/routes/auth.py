from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
import uuid
import re
import os

from back_end.models.auth_models import (
    SignupRequest,
    UserResponse,
    TokenResponse,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from back_end.db.database import get_db
# This is what main.py looks for
router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()  # For JWT authentication   

# Jwt configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable must be set")
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS512")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
JWT_ISSUER = os.environ.get("JWT_ISSUER", "scmxpert-lite")


PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=[\]{};:'\"\\|,.<>/?]).{8,}$"
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
    expire = now + timedelta(hours=1)  # Reset token expires in 1 hour

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
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user

async def admin_required(user: dict = Depends(get_current_user)):
    """
    A dependency that ensures the current user has the 'admin' role.
    """
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user




@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest):
    """Register a new user."""
    db = get_db()

    existing_user = await db.users.find_one({"email": request.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user_id = str(uuid.uuid4())
    user_docs = {
        "id": user_id,
        "full_name": request.full_name,
        "email": request.email,
        "hashed_password": hash_password(request.password),
        "role": "user",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(user_docs)

    access_token = create_access_token(data={"sub": user_id, "role": "user"})
    user_response = UserResponse(
        id=user_id,
        full_name=request.full_name,
        email=request.email,
        created_at=user_docs["created_at"],
    )

    return TokenResponse(
        access_token=access_token,
        user=user_response,
    )

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    db = get_db()
    
    # Find user by email
    user = await db.users.find_one({"email": request.email}, {"_id": 0})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    password_hash = user.get("hashed_password") or user.get("password_hash")
    if not password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account needs to be re-registered. Please sign up again."
        )

    # Verify password
    if not verify_password(request.password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user["id"], "role": user.get("role", "user")}
    )
    
    user_response = UserResponse(
        id=user["id"],
        full_name=user["full_name"],
        email=user["email"],

        created_at=user["created_at"]
    )
    
    return TokenResponse(
        access_token=access_token,
        user=user_response
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return UserResponse(
        id=current_user["id"],
        full_name=current_user["full_name"],
        email=current_user["email"],
        created_at=current_user["created_at"]
    )
   
@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Request a password reset token (send to email in production)"""
    db = get_db()
    user = await db.users.find_one({"email": request.email})
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a reset link has been sent."}

    reset_token = create_reset_token(request.email)
    # In production, send email with reset_token
    # For now, just return it (remove in production)
    print(f"Reset token for {request.email}: {reset_token}")

    return {"message": "If the email exists, a reset link has been sent."}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password using reset token"""
    try:
        payload = jwt.decode(
            request.token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer=JWT_ISSUER,
            options={"require": ["exp", "iat", "nbf", "sub", "type"]},
        )
        if payload.get("type") != "reset":
            raise jwt.InvalidTokenError
        email = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Reset token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    db = get_db()
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    hashed_password = hash_password(request.new_password)
    await db.users.update_one(
        {"email": email},
        {"$set": {"hashed_password": hashed_password}}
    )

    return {"message": "Password has been reset successfully"}

