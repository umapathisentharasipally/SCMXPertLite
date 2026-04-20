from fastapi import APIRouter, Depends
from typing import List, Optional
from back_end.models.shipment_model import ShipmentCreate, ShipmentOut
from back_end.db.database import get_db
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/shipments", tags=["Shipments"])

@router.post("/", response_model=ShipmentOut)
async def create_shipment(shipment: ShipmentCreate, db=Depends(get_db)):
    shipment_dict = shipment.dict()
    shipment_dict["created_by"] = "admin"  # Placeholder, replace with actual user info
    shipment_dict["created_at"] = datetime.utcnow()
    result = db.shipments.insert_one(shipment_dict)
    shipment_out = ShipmentOut(id=str(result.inserted_id), **shipment_dict)
    return shipment_out