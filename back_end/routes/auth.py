from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone
import uuid
import jwt

from back_end.db.database import get_db, users_collection, find_one, find_many, insert_one, update_one, delete_one, count_documents
from back_end.routes.auth_config import COLL_USERS, SECRET_KEY, ALGORITHM, JWT_ISSUER
from back_end.routes.auth_utils import (
    hash_password,
    create_access_token,
    create_reset_token,
    verify_recaptcha_token,
    verify_password,
)
from back_end.routes.auth_deps import (
    get_current_user,
    admin_required,
    super_admin_required,
    log_login_attempt,
)
from back_end.models.auth_models import (
    SignupRequest,
    UserResponse,
    TokenResponse,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest):
    """Register a new user."""
    await verify_recaptcha_token(request.recaptcha_token)

    existing_user = await find_one(users_collection, {"email": request.email})
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
    await insert_one(users_collection, user_docs)

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
async def login(request: LoginRequest, ip_address: str = None, user_agent: str = None):
    """Authenticate user and return JWT token"""
    await verify_recaptcha_token(request.recaptcha_token)
    
    user = await find_one(users_collection, {"email": request.email})
    if not user:
        await log_login_attempt(get_db(), request.email, False, ip_address, user_agent)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    password_hash = user.get("hashed_password") or user.get("password_hash")
    if not password_hash:
        await log_login_attempt(get_db(), request.email, False, ip_address, user_agent)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account needs to be re-registered. Please sign up again."
        )

    if not verify_password(request.password, password_hash):
        await log_login_attempt(get_db(), request.email, False, ip_address, user_agent)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(
        data={"sub": user["id"], "role": user.get("role", "user")}
    )
    
    await log_login_attempt(get_db(), request.email, True, ip_address, user_agent)
    
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
    """Request a password reset token"""
    user = await find_one(users_collection, {"email": request.email})
    if not user:
        return {"message": "If the email exists, a reset link has been sent."}

    reset_token = create_reset_token(request.email)
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

    user = await find_one(users_collection, {"email": email})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    hashed_password = hash_password(request.new_password)
    await update_one(users_collection, {"email": email}, {"hashed_password": hashed_password})

    return {"message": "Password has been reset successfully"}


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
    user = await db[COLL_USERS].find_one({"email": request.email})
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
    user = await db[COLL_USERS].find_one({"email": email})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    hashed_password = hash_password(request.new_password)
    await db[COLL_USERS].update_one(
        {"email": email},
        {"$set": {"hashed_password": hashed_password}}
    )


    return {"message": "Password has been reset successfully"}


# ==================== Super Admin Routes ====================

@router.get("/super-admin/users", dependencies=[Depends(super_admin_required)])
async def list_all_users(
    role: str = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(super_admin_required)
):
    """List all users (super admin only). Optionally filter by role."""
    query = {}
    if role:
        query["role"] = role
    
    users = await find_many(users_collection, query, limit=limit)
    # Remove sensitive fields from results
    for user in users:
        user.pop("hashed_password", None)
        user.pop("_id", None)
    total = await count_documents(users_collection, query)
    
    return {
        "users": users,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.patch("/super-admin/users/{user_id}/role", dependencies=[Depends(super_admin_required)])
async def update_user_role(
    user_id: str,
    new_role: str,
    current_user: dict = Depends(super_admin_required)
):
    """Update a user's role (super admin only)."""
    if new_role not in ["user", "admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'user', 'admin', or 'super_admin'"
        )
    
    # Prevent self-demotion
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    updated = await update_one(users_collection, {"id": user_id}, {"role": new_role})
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": f"User role updated to '{new_role}'"}


@router.delete("/super-admin/users/{user_id}", dependencies=[Depends(super_admin_required)])
async def delete_user(
    user_id: str,
    current_user: dict = Depends(super_admin_required)
):
    """Delete a user (super admin only)."""
    # Prevent self-deletion
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    deleted = await delete_one(users_collection, {"id": user_id})
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}


@router.post("/super-admin/create-admin", dependencies=[Depends(super_admin_required)])
async def create_admin(
    full_name: str,
    email: str,
    password: str,
    current_user: dict = Depends(super_admin_required)
):
    """Create a new admin user (super admin only)."""
    from back_end.models.auth_models import SignupRequest
    
    # Verify the email is deliverable
    from back_end.routes.auth_utils import verify_recaptcha_token
    from back_end.models.auth_models import PASSWORD_REGEX
    
    if not PASSWORD_REGEX.match(password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters with uppercase, lowercase, digit, and special character"
        )
    
    existing = await find_one(users_collection, {"email": email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_id = str(uuid.uuid4())
    user_docs = {
        "id": user_id,
        "full_name": full_name,
        "email": email,
        "hashed_password": hash_password(password),
        "role": "admin",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await insert_one(users_collection, user_docs)
    
    return {
        "message": "Admin created successfully",
        "user": {
            "id": user_id,
            "full_name": full_name,
            "email": email,
            "role": "admin"
        }
    }
 
