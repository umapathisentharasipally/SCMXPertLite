
import motor
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from typing import Optional, Dict

load_dotenv()


def get_mongo_uri() -> str:
    """Build MongoDB connection URI from environment variables."""
    username = quote_plus(os.getenv('MONGO_USERNAME', ''))
    password = quote_plus(os.getenv('MONGO_PASSWORD', ''))
    cluster_name = os.getenv('MONGO_CLUSTER_NAME', 'users')
    return f'mongodb+srv://{username}:{password}@{cluster_name}.qarlknd.mongodb.net/?retryWrites=true&w=majority'


def get_database(db_name: Optional[str] = None) -> motor.AsyncIOMotorDatabase:
    """Create and return MongoDB client and database."""
    uri = get_mongo_uri()
    client = AsyncIOMotorClient(uri)
    database_name = db_name or os.getenv("MONGO_DB_NAME", "SCM_DB")
    return client[database_name]


def get_collections(db: motor.motor_asyncio.AsyncIOMotorDatabase) -> Dict[str, motor.motor_asyncio.AsyncIOMotorCollection]:
    """Return a dictionary of collection references."""
    coll_users = os.getenv('COLL_USERS', 'users')
    coll_shipments = os.getenv('COLL_SHIPMENTS', 'shipments')
    coll_logs = os.getenv('COLL_LOGS', 'logins')
    coll_devices = os.getenv('COLL_DEVICES', 'devices')
    return {
        'users': db[coll_users],
        'shipments': db[coll_shipments],
        'logins': db[coll_logs],
        'devices': db[coll_devices]
    }


# Initialize default collections
client = motor.motor_asyncio.AsyncIOMotorClient(get_mongo_uri())
db = client[os.getenv("MONGO_DB_NAME", "SCM_DB")]

coll_users = os.getenv('COLL_USERS', 'users')
coll_shipments = os.getenv('COLL_SHIPMENTS', 'shipments')
coll_logs = os.getenv('COLL_LOGS', 'logins')
coll_devices = os.getenv('COLL_DEVICES', 'devices')

users_collection = db[coll_users]
shipments_collection = db[coll_shipments]
logins_collection = db[coll_logs]
devices_collection = db[coll_devices]


