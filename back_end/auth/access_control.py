from fastapi import HTTPException, status
from back_end.db.database import get_shipments_collection, find_many


def build_shipment_query(user: dict) -> dict:
    role = user.get("role")
    user_id = user.get("id")

    if role == "super_admin":
        return {}

    if role == "admin":
        return {
            "$or": [
                {"created_by.id": user_id},
                {"admin_id": user_id}
            ]
        }

    if role == "user":
        return {"created_by.id": user_id}

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied"
    )


async def build_device_query(user: dict) -> dict:
    role = user.get("role")
    user_id = user.get("id")

    if role == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Users are not allowed to access device data"
        )

    if role == "super_admin":
        return {}

    if role == "admin":
        shipments = await find_many(
            get_shipments_collection(),
            {
                "$or": [
                    {"created_by.id": user_id},
                    {"admin_id": user_id}
                ]
            }
        )

        allowed_shipment_ids = [
            shipment["shipment_id"]
            for shipment in shipments
            if "shipment_id" in shipment
        ]

        return {
            "shipment_id": {"$in": allowed_shipment_ids}
        }

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied"
    )