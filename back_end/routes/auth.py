from fastapi import APIRouter, Depends, HTTPException, status, Request
from datetime import datetime, timezone
import uuid
import jwt

from back_end.db.database import (
    get_db,
    get_users_collection,
    find_one,
    find_many,
    insert_one,
    update_one,
    delete_one,
    count_documents
)

from back_end.auth.auth_config import (
    COLL_USERS,
    SECRET_KEY,
    ALGORITHM,
    JWT_ISSUER
)

from back_end.auth.auth_utils import (
    hash_password,
    create_access_token,
    create_reset_token,
    verify_recaptcha_token,
    verify_password,
    validate_password
)

from back_end.auth.auth_deps import (
    get_current_user,
    super_admin_required,
    log_login_attempt
)

from back_end.models.auth_models import (
    SignupRequest,
    UserResponse,
    TokenResponse,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest
)


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ==================== SIGNUP ====================

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest):
    """Register new user. Role is always user by default."""

    captcha_valid = await verify_recaptcha_token(request.recaptcha_token)
    if not captcha_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reCAPTCHA"
        )

    if not validate_password(request.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters with uppercase, lowercase, number, and special character"
        )

    email = request.email.lower().strip()

    existing_user = await find_one(get_users_collection(), {"email": email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    user_doc = {
        "id": user_id,
        "full_name": request.full_name.strip(),
        "email": email,
        "hashed_password": hash_password(request.password),
        "role": "user",
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }

    await insert_one(get_users_collection(), user_doc)

    access_token = create_access_token(
        data={
            "sub": user_id,
            "role": "user"
        }
    )

    user_response = UserResponse(
        id=user_id,
        full_name=user_doc["full_name"],
        email=user_doc["email"],
        created_at=user_doc["created_at"]
    )

    return TokenResponse(
        access_token=access_token,
        user=user_response
    )


# ==================== LOGIN ====================

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, fastapi_request: Request):
    """Login user and return JWT token."""

    db = get_db()

    captcha_valid = await verify_recaptcha_token(
        request.recaptcha_token,
        remote_ip=fastapi_request.client.host if fastapi_request.client else None
    )

    if not captcha_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reCAPTCHA"
        )

    email = request.email.lower().strip()

    ip_address = fastapi_request.client.host if fastapi_request.client else "unknown"
    user_agent = fastapi_request.headers.get("user-agent", "unknown")

    user = await find_one(get_users_collection(), {"email": email})

    if not user:
        await log_login_attempt(db, email, False, ip_address, user_agent)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.get("is_active", True):
        await log_login_attempt(db, email, False, ip_address, user_agent)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    password_hash = user.get("hashed_password")

    if not password_hash or not verify_password(request.password, password_hash):
        await log_login_attempt(db, email, False, ip_address, user_agent)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        data={
            "sub": user["id"],
            "role": user.get("role", "user")
        }
    )

    await update_one(
        get_users_collection(),
        {"id": user["id"]},
        {"last_login": datetime.now(timezone.utc)}
    )

    await log_login_attempt(db, email, True, ip_address, user_agent)

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


# ==================== CURRENT USER ====================

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get logged-in user details."""

    return UserResponse(
        id=current_user["id"],
        full_name=current_user["full_name"],
        email=current_user["email"],
        created_at=current_user["created_at"]
    )


# ==================== FORGOT PASSWORD ====================

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Generate password reset token."""

    email = request.email.lower().strip()

    user = await find_one(get_users_collection(), {"email": email})

    if not user:
        return {
            "message": "If the email exists, a reset link has been sent."
        }

    reset_token = create_reset_token(email)

    # Production: send this token by email, do not print it
    print(f"Reset token for {email}: {reset_token}")

    return {
        "message": "If the email exists, a reset link has been sent."
    }


# ==================== RESET PASSWORD ====================

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password using JWT reset token."""

    try:
        payload = jwt.decode(
            request.token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer=JWT_ISSUER
        )

        if payload.get("type") != "reset":
            raise jwt.InvalidTokenError

        email = payload.get("sub")

        if not email:
            raise jwt.InvalidTokenError

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )

    if not validate_password(request.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters with uppercase, lowercase, number, and special character"
        )

    user = await find_one(get_users_collection(), {"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )

    await update_one(
        get_users_collection(),
        {"email": email},
        {
            "hashed_password": hash_password(request.new_password),
            "updated_at": datetime.now(timezone.utc)
        }
    )

    return {
        "message": "Password has been reset successfully"
    }


# ==================== SUPER ADMIN ROUTES ====================

@router.get("/super-admin/users")
async def list_all_users(
    role: str = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(super_admin_required)
):
    """List all users. Super admin only."""

    query = {}

    if role:
        query["role"] = role

    users = await find_many(
        get_users_collection(),
        query=query,
        limit=limit
    )

    clean_users = []

    for user in users:
        user.pop("hashed_password", None)
        user.pop("_id", None)
        clean_users.append(user)

    total = await count_documents(get_users_collection(), query)

    return {
        "users": clean_users,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.patch("/super-admin/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    new_role: str,
    current_user: dict = Depends(super_admin_required)
):
    """Update user role. Super admin only."""

    allowed_roles = ["user", "admin", "super_admin"]

    if new_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be user, admin, or super_admin"
        )

    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )

    updated = await update_one(
        get_users_collection(),
        {"id": user_id},
        {
            "role": new_role,
            "updated_at": datetime.now(timezone.utc)
        }
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "message": f"User role updated to {new_role}"
    }


@router.delete("/super-admin/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(super_admin_required)
):
    """Delete user. Super admin only."""

    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    success = await delete_one(get_users_collection(), {"id": user_id})

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "message": "User deleted successfully"
    }


@router.post("/super-admin/create-admin")
async def create_admin(
    full_name: str,
    email: str,
    password: str,
    current_user: dict = Depends(super_admin_required)
):
    """Create admin user. Super admin only."""

    if not validate_password(password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters with uppercase, lowercase, number, and special character"
        )

    email = email.lower().strip()

    existing_user = await find_one(get_users_collection(), {"email": email})

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    admin_doc = {
        "id": user_id,
        "full_name": full_name.strip(),
        "email": email,
        "hashed_password": hash_password(password),
        "role": "admin",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "created_by": current_user["id"]
    }

    await insert_one(get_users_collection(), admin_doc)

    return {
        "message": "Admin created successfully",
        "user": {
            "id": user_id,
            "full_name": admin_doc["full_name"],
            "email": admin_doc["email"],
            "role": "admin"
        }
    }