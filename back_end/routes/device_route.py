from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional

from back_end.models.device_model import DeviceModel, SensorData
from back_end.auth.auth_deps import get_current_user
from back_end.auth.access_control import build_device_query


router = APIRouter(prefix="/api/device", tags=["Device"])


@router.post("/sensor_data")
async def create_sensor_data(
    payload: SensorData,
    user: dict = Depends(get_current_user)
):
    if user.get("role") == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Users are not allowed to create device data"
        )

    device_model = DeviceModel()
    data = payload.dict(by_alias=False)

    inserted_id = await device_model.create_sensor_reading(data)

    if not inserted_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save sensor data"
        )

    return {
        "success": True,
        "message": "Sensor data saved successfully",
        "id": inserted_id
    }


@router.get("/sensor_data", response_model=List[Dict[str, Any]])
async def get_all_sensor_data(
    user: dict = Depends(get_current_user)
):
    query = await build_device_query(user)

    device_model = DeviceModel()
    data = await device_model.get_sensor_data_by_query(query)

    return data


@router.get("/{device_id}/latest_sensor_data", response_model=Optional[Dict[str, Any]])
async def get_latest_device_sensor_data(
    device_id: int,
    user: dict = Depends(get_current_user)
):
    query = await build_device_query(user)

    device_model = DeviceModel()
    data = await device_model.get_latest_sensor_data_by_device_id(device_id, query)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sensor data found for this device ID"
        )

    return data


@router.get("/{device_id}/sensor_history", response_model=List[Dict[str, Any]])
async def get_device_sensor_history(
    device_id: int,
    user: dict = Depends(get_current_user)
):
    query = await build_device_query(user)

    device_model = DeviceModel()
    data = await device_model.get_sensor_data_by_device_id(device_id, query)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No historical sensor data found for this device ID"
        )

    return data