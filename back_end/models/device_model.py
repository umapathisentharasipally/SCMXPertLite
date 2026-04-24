
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
import os
import random
from bson import ObjectId

from back_end.routes.auth import get_current_user  
from back_end.db.database import sensor_data_collection, insert_one, find_many, find_one
router = APIRouter(prefix="/api/device", tags=["Device"])


class SensorData(BaseModel):
    # Use Field(alias="_id") for mapping "_id" from MongoDB to "id" in Pydantic
    # default_factory=lambda: str(ObjectId()) generates a new ObjectId string if not provided
    id: Optional[str] = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    Device_ID: int
    Battery_Level: float
    First_Sensor_temperature: float
    Route_From: str
    Route_To: str
    # Use default_factory=datetime.utcnow for automatic UTC timestamp generation
    Timestamp_IST: datetime = Field(default_factory=datetime.utcnow)

    # Configuration for Pydantic model
    class Config:
        populate_by_name = True  # Allow population by field name or alias
        json_encoders = {ObjectId: str} # Encode ObjectId to string when serializing to JSON
        arbitrary_types_allowed = True # Allows types like ObjectId to be used in model




class DeviceModel:
    """
    Manages database operations for sensor data in the "sensor_data" MongoDB collection.
    """
    def __init__(self):
        self.collection = sensor_data_collection

    async def create_sensor_reading(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Inserts a new sensor data reading into the collection.
        Args:
            data (Dict[str, Any]): A dictionary containing the sensor data.
                                   Expected keys: Device_ID, Battery_Level,
                                   First_Sensor_temperature, Route_From, Route_To.
        Returns:
            Optional[str]: The string representation of the inserted document's ID,
                           or None if an error occurred.
        """
        try:
            result = await self.collection.insert_one(data)
            print(f"Inserted sensor data with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error inserting sensor data: {e}")
            return None
    
    async def get_all_sensor_data(self) -> List[Dict[str, Any]]:
        """
        Retrieves all sensor data readings from the collection.
        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing all sensor data readings.
        """
        try:
            data = await find_many(self.collection)
            for items in data:
                if "_id" in items:
                    items["id"] = str(items["_id"])
            return data
        except Exception as e:
            print(f"Error retrieving all sensor data: {e}")
            return []
    
    async def get_sensor_data_by_device_id(self, device_id:int) -> List[Dict[str,Any]]:
        """
        Retrieves historical sensor data for a specific device ID, sorted by timestamp (latest first).
        Args:
            device_id (int): The ID of the device to retrieve data for."""
        try:
            data = await find_many(self.collection, {"Device_Id": device_id}, sort=[("timestamp", -1)])
            for items in data:
                items['_id'] = str(items['_id'])
            return data
        except Exception as e:
            print(f"Error retrieving sensor data for device ID {device_id}: {e}")
            return []
        
    async def get_latest_sensor_data_by_device_id(self, device_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves the latest sensor data for a specific device ID.
        Args:
            device_id (int): The ID of the device to retrieve data for.
        Returns:
            Optional[Dict[str, Any]]: A dictionary representing the latest sensor data for the device,
                                      or None if no data is found or an error occurs.     """        
        try:
            data = await find_one(self.collection, {"Device_Id": device_id})
            if data:
                data['_id'] = str(data['_id'])
            return data
        except Exception as e:
            print(f"Error retrieving latest sensor data for device ID {device_id}: {e}")
            return None
        
    