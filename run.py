import uuid
from datetime import datetime, timezone
from passlib.context import CryptContext
from pymongo import MongoClient
 
from back_end.db.database import get_db
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = get_db()

user_id = str(uuid.uuid4())

db.users.insert_one({
    "id": user_id,
    "full_name": "super_admin",
    "email": "sentharasipallyumapathi@gmail.com",
    "phone_number": "9398860744",
    "hashed_password": pwd.hash("Super@123"),
    "role": "super_admin",
    "is_active": True,
    "created_by": None,
    "admin_id": None,
    "created_at": datetime.now(timezone.utc),
    "updated_at": datetime.now(timezone.utc)
})

print("Super admin created")