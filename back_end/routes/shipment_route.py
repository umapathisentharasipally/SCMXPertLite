from fastapi import APIRouter, Depends
from typing import List, Optional
from back_end.models.shipment_model import ShipmentCreate, ShipmentOut
from back_end.db.database import shipments_collection, insert_one, find_many, find_one, update_one, delete_one
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/shipments", tags=["Shipments"])

@router.post("/", response_model=ShipmentOut)
async def create_shipment(shipment: ShipmentCreate):
    shipment_dict = shipment.dict()
    shipment_dict["created_by"] = "admin"  # Placeholder, replace with actual user info
    shipment_dict["created_at"] = datetime.utcnow()
    inserted_id = await insert_one(shipments_collection, shipment_dict)
    shipment_dict["id"] = inserted_id
    return ShipmentOut(**shipment_dict)