import logging
from functools import wraps

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone
import uuid

from back_end.db.database import (
    get_users_collection,
    find_one,
    find_many,
    insert_one,
    update_one,
    delete_one,
    count_documents
)

from back_end.auth.auth_utils import (
    hash_password,
    validate_password
)

from back_end.auth.auth_deps import (
    get_current_user,
    super_admin_required
)


logger = logging.getLogger(__name__)


def handle_route_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Unhandled error in admin auth route")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            ) from exc
    return wrapper


router = APIRouter(prefix="/api/auth", tags=["Admin Authentication"])


@router.post("/admin/create-user")
@handle_route_errors
async def create_user_under_admin(
    full_name: str,
    email: str,
    password: str,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can create users"
        )

    if not validate_password(password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters with uppercase, lowercase, number, and special character"
        )

    email = email.lower().strip()

    existing_user = await find_one(get_users_collection(), {"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    user_doc = {
        "id": user_id,
        "full_name": full_name.strip(),
        "email": email,
        "hashed_password": hash_password(password),
        "role": "user",
        "is_active": True,
        "created_by": current_user["id"],
        "admin_id": current_user["id"],
        "created_at": now,
        "updated_at": now
    }

    await insert_one(get_users_collection(), user_doc)

    return {
        "success": True,
        "message": "User created successfully under admin",
        "user": {
            "id": user_id,
            "full_name": user_doc["full_name"],
            "email": user_doc["email"],
            "role": "user",
            "admin_id": current_user["id"]
        }
    }


@router.get("/admin/users")
@handle_route_errors
async def list_users_under_admin(
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can view users under admin"
        )

    users = await find_many(
        get_users_collection(),
        query={
            "role": "user",
            "admin_id": current_user["id"]
        },
        limit=100
    )

    clean_users = []

    for user in users:
        user.pop("hashed_password", None)
        user.pop("_id", None)
        clean_users.append(user)

    return {
        "success": True,
        "count": len(clean_users),
        "users": clean_users
    }


@router.delete("/admin/users/{user_id}")
@handle_route_errors
async def delete_user_under_admin(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can delete users"
        )

    user = await find_one(
        get_users_collection(),
        {
            "id": user_id,
            "role": "user",
            "admin_id": current_user["id"]
        }
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found under this admin"
        )

    success = await delete_one(
        get_users_collection(),
        {"id": user_id}
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

    return {
        "success": True,
        "message": "User deleted successfully"
    }


@router.get("/super-admin/users")
@handle_route_errors
async def list_all_users(
    role: str = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(super_admin_required)
):
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
        "success": True,
        "users": clean_users,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/super-admin/create-admin")
@handle_route_errors
async def create_admin(
    full_name: str,
    email: str,
    password: str,
    current_user: dict = Depends(super_admin_required)
):
    if not validate_password(password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters with uppercase, lowercase, number, and special character"
        )

    email = email.lower().strip()

    existing_user = await find_one(get_users_collection(), {"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    admin_doc = {
        "id": user_id,
        "full_name": full_name.strip(),
        "email": email,
        "hashed_password": hash_password(password),
        "role": "admin",
        "is_active": True,
        "created_by": current_user["id"],
        "admin_id": user_id,
        "created_at": now,
        "updated_at": now
    }

    await insert_one(get_users_collection(), admin_doc)

    return {
        "success": True,
        "message": "Admin created successfully",
        "user": {
            "id": user_id,
            "full_name": admin_doc["full_name"],
            "email": admin_doc["email"],
            "role": "admin",
            "admin_id": user_id
        }
    }


@router.patch("/super-admin/users/{user_id}/role")
@handle_route_errors
async def update_user_role(
    user_id: str,
    new_role: str,
    current_user: dict = Depends(super_admin_required)
):
    allowed_roles = ["user", "admin", "super_admin"]

    if new_role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail="Invalid role. Must be user, admin, or super_admin"
        )

    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot change your own role"
        )


    update_data = {
        "role": new_role,
        "updated_at": datetime.now(timezone.utc)
    }

    if new_role == "admin":
        update_data["admin_id"] = user_id

    if new_role == "user":
        update_data["admin_id"] = None

    updated = await update_one(
        get_users_collection(),
        {"id": user_id},
        update_data
    )

    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "success": True,
        "message": f"User role updated to {new_role}"
    }


@router.delete("/super-admin/users/{user_id}")
@handle_route_errors
async def delete_user(
    user_id: str,
    current_user: dict = Depends(super_admin_required)
):
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own account"
        )

    success = await delete_one(
        get_users_collection(),
        {"id": user_id}
    )

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "success": True,
        "message": "User deleted successfully"
    }