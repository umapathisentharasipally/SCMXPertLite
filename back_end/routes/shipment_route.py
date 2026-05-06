from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from bson import ObjectId
from datetime import datetime, timezone
from back_end.auth.access_control import build_shipment_query

from back_end.models.shipment_model import ShipmentCreate, ShipmentUpdate
from back_end.db.database import (
    get_shipments_collection,
    find_one,
    find_many,
    insert_one,
    update_one,
    delete_one
)
from back_end.auth.auth_deps import get_current_user, admin_required

router = APIRouter(prefix="/shipments", tags=["Shipments"])


def serialize_shipment(shipment: Dict[str, Any]) -> Dict[str, Any]:
    shipment["id"] = str(shipment.pop("_id"))

    if isinstance(shipment.get("created_at"), datetime):
        shipment["created_at"] = shipment["created_at"].isoformat()

    if isinstance(shipment.get("updated_at"), datetime):
        shipment["updated_at"] = shipment["updated_at"].isoformat()

    return shipment


@router.post("/", status_code=201)
async def create_shipment(
    shipment: ShipmentCreate,
    user: dict = Depends(get_current_user)
):
    existing = await find_one(
        get_shipments_collection(),
        {"shipment_id": shipment.shipment_id}
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Shipment ID already exists"
        )

    now = datetime.now(timezone.utc)

    shipment_data = shipment.dict()
    shipment_data["created_by"] = {
        "id": user.get("id"),
        "email": user.get("email"),
        "role": user.get("role", "user")
    }

    shipment_data["admin_id"] = (
        user.get("id") if user.get("role") == "admin" else user.get("admin_id")
    )
    shipment_data["created_at"] = now
    shipment_data["updated_at"] = now

    inserted_id = await insert_one(get_shipments_collection(), shipment_data)

    return {
        "success": True,
        "message": "Shipment created successfully",
        "shipment_id": inserted_id
    }


@router.get("/all")
async def get_shipments(user: dict = Depends(get_current_user)):
    query = await build_shipment_query(user)

    shipments = await find_many(
        get_shipments_collection(),
        query,
        sort=[("created_at", -1)]
    )

    return {
        "success": True,
        "count": len(shipments),
        "data": [serialize_shipment(s) for s in shipments]
    }


@router.get("/mine")
async def get_my_shipments(user: dict = Depends(get_current_user)):
    query = await build_shipment_query(user)

    shipments = await find_many(
        get_shipments_collection(),
        query,
        limit=100,
        sort=[("created_at", -1)]
    )

    return {
        "success": True,
        "count": len(shipments),
        "data": [serialize_shipment(s) for s in shipments]
    }


@router.get("/{shipment_id}")
async def get_shipment_by_id(
    shipment_id: str,
    user: dict = Depends(get_current_user)
):
    shipment = await find_one(
        get_shipments_collection(),
        {"shipment_id": shipment_id}
    )

    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    return {
        "success": True,
        "data": serialize_shipment(shipment)
    }


@router.put("/{shipment_id}")
async def update_shipment(
    shipment_id: str,
    updates: ShipmentUpdate,
    admin: dict = Depends(admin_required)
):
    update_data = {
        key: value
        for key, value in updates.dict().items()
        if value is not None
    }

    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    update_data["updated_at"] = datetime.now(timezone.utc)

    success = await update_one(
        get_shipments_collection(),
        {"shipment_id": shipment_id},
        update_data
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found or no changes applied"
        )

    return {
        "success": True,
        "message": "Shipment updated successfully"
    }


@router.patch("/{shipment_id}/status")
async def update_shipment_status(
    shipment_id: str,
    status_value: str,
    admin: dict = Depends(admin_required)
):
    allowed_status = ["Created", "In Transit", "Delayed", "Delivered", "Closed"]

    if status_value not in allowed_status:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Allowed values: {allowed_status}"
        )

    success = await update_one(
        get_shipments_collection(),
        {"shipment_id": shipment_id},
        {
            "status": status_value,
            "updated_at": datetime.now(timezone.utc)
        }
    )

    if not success:
        raise HTTPException(status_code=404, detail="Shipment not found")

    return {
        "success": True,
        "message": "Shipment status updated successfully"
    }


@router.delete("/{shipment_id}")
async def delete_shipment(
    shipment_id: str,
    admin: dict = Depends(admin_required)
):
    success = await delete_one(
        get_shipments_collection(),
        {"shipment_id": shipment_id}
    )

    if not success:
        raise HTTPException(status_code=404, detail="Shipment not found")

    return {
        "success": True,
        "message": "Shipment deleted successfully"
    }