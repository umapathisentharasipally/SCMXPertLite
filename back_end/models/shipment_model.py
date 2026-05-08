from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime


ShipmentStatus = Literal[
    "Created",
    "In Transit",
    "Delayed",
    "Delivered",
    "Closed"
]


class ShipmentCreate(BaseModel):
    shipment_id: str = Field(..., min_length=3, max_length=50)
    container_id: str = Field(..., min_length=2, max_length=50)
    route_from: str = Field(..., min_length=2, max_length=100)
    route_to: str = Field(..., min_length=2, max_length=100)
    status: ShipmentStatus = "Created"
    device_id: str = Field(..., min_length=2, max_length=50)

    @field_validator(
        "shipment_id",
        "container_id",
        "route_from",
        "route_to",
        "device_id"
    )
    @classmethod
    def validate_strings(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty")

        return value


class ShipmentUpdate(BaseModel):
    container_id: Optional[str] = None
    route_from: Optional[str] = None
    route_to: Optional[str] = None
    status: Optional[ShipmentStatus] = None
    device_id: Optional[str] = None

    @field_validator(
        "container_id",
        "route_from",
        "route_to",
        "device_id"
    )
    @classmethod
    def validate_optional_strings(cls, value):
        if value is not None:
            value = value.strip()

            if not value:
                raise ValueError("Field cannot be empty")

        return value


class ShipmentOut(BaseModel):
    id: str
    shipment_id: str
    container_id: str
    route_from: str
    route_to: str
    status: ShipmentStatus
    device_id: str
    created_by: dict
    created_at: datetime
    updated_at: datetime