from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


ShipmentStatus = Literal["Created", "In Transit", "Delayed", "Delivered", "Closed"]


class ShipmentCreate(BaseModel):
    shipment_id: str = Field(..., min_length=1)
    container_id: str
    route_from: str
    route_to: str
    status: ShipmentStatus = "Created"
    device_id: str


class ShipmentUpdate(BaseModel):
    container_id: Optional[str] = None
    route_from: Optional[str] = None
    route_to: Optional[str] = None
    status: Optional[ShipmentStatus] = None
    device_id: Optional[str] = None


class ShipmentOut(BaseModel):
    id: str
    shipment_id: str
    container_id: str
    route_from: str
    route_to: str
    status: str
    device_id: str
    created_by: dict
    created_at: datetime
    updated_at: datetime