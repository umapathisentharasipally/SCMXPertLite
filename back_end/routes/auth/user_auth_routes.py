from fastapi import APIRouter, Depends, HTTPException, status, Request
from datetime import datetime, timezone
import uuid
import jwt

from back_end.db.database import (
    get_db,
    get_users_collection,
    find_one,
    insert_one,
    update_one
)

from back_end.auth.auth_config import (
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


router = APIRouter(prefix="/api/auth", tags=["User Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest):
    """captcha_valid = await verify_recaptcha_token(request.recaptcha_token)

    if not captcha_valid:
        raise HTTPException(status_code=400, detail="Invalid reCAPTCHA")"""

    if not validate_password(request.password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters with uppercase, lowercase, number, and special character"
        )

    email = request.email.lower().strip()

    existing_user = await find_one(get_users_collection(), {"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    user_doc = {
        "id": user_id,
        "full_name": request.full_name.strip(),
        "email": email,
        "phone_number": request.phone_number.strip() if request.phone_number else None,
        "hashed_password": hash_password(request.password),
        "role": "user",
        "is_active": True,
        "created_by": None,
        "admin_id": None,
        "created_at": now,
        "updated_at": now
    }

    await insert_one(get_users_collection(), user_doc)

    access_token = create_access_token(
        data={
            "sub": user_id,
            "role": "user",
            "admin_id": None
        }
    )

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user_id,
            full_name=user_doc["full_name"],
            email=user_doc["email"],
            created_at=user_doc["created_at"]
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, fastapi_request: Request):
    db = get_db()

    """captcha_valid = await verify_recaptcha_token(
        request.recaptcha_token,
        remote_ip=fastapi_request.client.host if fastapi_request.client else None
    )

    if not captcha_valid:
        raise HTTPException(status_code=400, detail="Invalid reCAPTCHA")"""

    email = request.email.lower().strip()
    ip_address = fastapi_request.client.host if fastapi_request.client else "unknown"
    user_agent = fastapi_request.headers.get("user-agent", "unknown")

    user = await find_one(get_users_collection(), {"email": email})

    if not user:
        await log_login_attempt(db, email, False, ip_address, user_agent)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.get("is_active", True):
        await log_login_attempt(db, email, False, ip_address, user_agent)
        raise HTTPException(status_code=403, detail="Account is disabled")

    password_hash = user.get("hashed_password")

    if not password_hash or not verify_password(request.password, password_hash):
        await log_login_attempt(db, email, False, ip_address, user_agent)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(
        data={
            "sub": user["id"],
            "role": user.get("role", "user"),
            "admin_id": user.get("admin_id")
        }
    )

    await update_one(
        get_users_collection(),
        {"id": user["id"]},
        {"last_login": datetime.now(timezone.utc)}
    )

    await log_login_attempt(db, email, True, ip_address, user_agent)

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user["id"],
            full_name=user["full_name"],
            email=user["email"],
            created_at=user["created_at"]
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        full_name=current_user["full_name"],
        email=current_user["email"],
        created_at=current_user["created_at"]
    )


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    email = request.email.lower().strip()

    user = await find_one(get_users_collection(), {"email": email})

    if not user:
        return {
            "message": "If the email exists, a reset link has been sent."
        }

    reset_token = create_reset_token(email)

    print(f"Reset token for {email}: {reset_token}")

    return {
        "message": "If the email exists, a reset link has been sent."
    }


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
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
        raise HTTPException(status_code=400, detail="Reset token has expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    if not validate_password(request.new_password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters with uppercase, lowercase, number, and special character"
        )

    user = await find_one(get_users_collection(), {"email": email})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token")

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