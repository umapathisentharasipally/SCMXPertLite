from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from back_end.models.shipment_model import ShipmentCreate
from back_end.db.database import get_shipments_collection, get_users_collection, insert_one, find_many, update_one, delete_one, find_one
from back_end.auth.auth_deps import get_current_user, admin_required
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/shipments", tags=["Shipments"])


async def verify_user_for_shipment(user: dict) -> dict:
    """
    Verify user data before accessing shipment information.
    Ensures user exists and is active in database.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User data is invalid"
        )
    
    # Verify user exists in database
    db_user = await find_one(get_users_collection(), {"id": user.get("id")})
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in database"
        )
    
    # Check if user has valid role
    valid_roles = ["user", "admin", "super_admin"]
    if db_user.get("role") not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has invalid role"
        )
    
    return db_user


def serialize_shipment(shipment: Dict[str, Any]) -> Dict[str, Any]:
    shipment["id"] = str(shipment.pop("_id", ""))
    if isinstance(shipment.get("created_by"), dict) and shipment["created_by"].get("id"):
        shipment["created_by"]["id"] = str(shipment["created_by"]["id"])
    if isinstance(shipment.get("created_at"), datetime):
        shipment["created_at"] = shipment["created_at"].isoformat()
    return shipment


@router.get("/all")
async def get_all_shipments(admin=Depends(admin_required)):
    # Verify user data before accessing shipments
    verified_user = await verify_user_for_shipment(admin)
    
    shipments = await find_many(get_shipments_collection(), {}, limit=100)
    return [serialize_shipment(s) for s in shipments]


@router.get("/mine")
async def get_my_shipments(user=Depends(get_current_user)):
    # Verify user data before accessing shipments
    verified_user = await verify_user_for_shipment(user)
    
    query = {}
    if verified_user.get("role") != "admin":
        query = {"created_by.id": verified_user["_id"]}

    shipments = await find_many(get_shipments_collection(), query, limit=100)
    return [serialize_shipment(s) for s in shipments]


@router.post("/", status_code=201)
async def create_shipment(shipment: ShipmentCreate, user=Depends(get_current_user)):
    # Verify user data before creating shipment
    verified_user = await verify_user_for_shipment(user)
    
    shipment_data = shipment.dict()
    shipment_data["created_by"] = {
        "id": verified_user["_id"],
        "username": verified_user["username"],
        "role": verified_user["role"]
    }
    shipment_data["created_at"] = datetime.utcnow()

    shipment_id = await insert_one(get_shipments_collection(), shipment_data)
    return {"msg": "Shipment created", "shipment_id": shipment_id}


@router.put("/{shipment_id}", dependencies=[Depends(admin_required)])
async def update_shipment(shipment_id: str, updates: dict):
    success = await update_one(
        get_shipments_collection(),
        {"_id": ObjectId(shipment_id)},
        updates
    )
    if not success:
        raise HTTPException(status_code=404, detail="Shipment not found or no changes applied")
    return {"msg": "Shipment updated successfully"}


@router.delete("/{shipment_id}", dependencies=[Depends(admin_required)])
async def delete_shipment(shipment_id: str):
    success = await delete_one(get_shipments_collection(), {"_id": ObjectId(shipment_id)})
    if not success:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return {"msg": "Shipment deleted"}
