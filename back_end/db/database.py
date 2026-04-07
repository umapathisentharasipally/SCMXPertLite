import os
from motor.motor_asyncio import AsyncIOMotorClient

def get_db():
    """Get database connection."""
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db_name = os.environ.get("DB_NAME", "scmxpert_db")
    return client[db_name]