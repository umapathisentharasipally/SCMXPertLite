from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from bson import ObjectId

from back_end.db.database import (
    get_sensor_data_collection,
    insert_one,
    find_many
)


class SensorData(BaseModel):
    id: Optional[str] = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    Device_ID: int
    shipment_id: str
    Battery_Level: float
    First_Sensor_temperature: float
    Route_From: str
    Route_To: str
    Timestamp_IST: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        arbitrary_types_allowed = True


class DeviceModel:
    def __init__(self):
        self.collection = get_sensor_data_collection()

    async def create_sensor_reading(self, data: Dict[str, Any]) -> Optional[str]:
        try:
            if "Timestamp_IST" not in data:
                data["Timestamp_IST"] = datetime.now(timezone.utc)

            result = await insert_one(self.collection, data)
            return result

        except Exception as e:
            print(f"Error inserting sensor data: {e}")
            return None

    async def get_sensor_data_by_query(self, query: dict) -> List[Dict[str, Any]]:
        try:
            data = await find_many(
                self.collection,
                query,
                sort=[("Timestamp_IST", -1)]
            )

            for item in data:
                item["_id"] = str(item["_id"])

            return data

        except Exception as e:
            print(f"Error retrieving sensor data by query: {e}")
            return []

    async def get_sensor_data_by_device_id(
        self,
        device_id: int,
        query: Optional[dict] = None
    ) -> List[Dict[str, Any]]:
        try:
            final_query = {"Device_ID": device_id}

            if query:
                final_query = {
                    "$and": [
                        query,
                        {"Device_ID": device_id}
                    ]
                }

            data = await find_many(
                self.collection,
                final_query,
                sort=[("Timestamp_IST", -1)]
            )

            for item in data:
                item["_id"] = str(item["_id"])

            return data

        except Exception as e:
            print(f"Error retrieving sensor data for device ID {device_id}: {e}")
            return []

    async def get_latest_sensor_data_by_device_id(
        self,
        device_id: int,
        query: Optional[dict] = None
    ) -> Optional[Dict[str, Any]]:
        try:
            final_query = {"Device_ID": device_id}

            if query:
                final_query = {
                    "$and": [
                        query,
                        {"Device_ID": device_id}
                    ]
                }

            data = await self.collection.find_one(
                final_query,
                sort=[("Timestamp_IST", -1)]
            )

            if data:
                data["_id"] = str(data["_id"])

            return data

        except Exception as e:
            print(f"Error retrieving latest sensor data for device ID {device_id}: {e}")
            return None