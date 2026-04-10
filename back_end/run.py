from pydantic import BaseModel,Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from bson import ObjectId

class SensorData(BaseModel):
    id : Optional[str] = Field (alias="_id", default_factory=lambda: str(ObjectId()))
    Device_ID: int
    Battery_Level: float
    First_Sensor_temperature: float
    Route_From: str
    Route_To: str
    Timestamp_IST: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        arbitrary_types_allowed = True
