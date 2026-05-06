import motor
from motor.motor_asyncio import AsyncIOMotorClient
from back_end.config import (
    MONGO_USERNAME, MONGO_PASSWORD, MONGO_CLUSTER_NAME, MONGO_DB_NAME, MONGO_URL,
    COLL_USERS, COLL_SHIPMENTS, COLL_LOGS, COLL_DEVICES
)
from typing import Optional, Dict, List, Any
from urllib.parse import quote_plus


# ============== Database Connection ==============

# Lazy load database connection to avoid connection at import time
_db = None

def get_db():
    global _db
    if _db is None:
        # Check for full MongoDB Atlas URL first
        mongo_url = MONGO_URL

        # If no full URL, construct from Atlas credentials
        if not mongo_url:
            username = MONGO_USERNAME
            password = MONGO_PASSWORD
            cluster = MONGO_CLUSTER_NAME

            if username and password:
                mongo_url = f"mongodb+srv://{username}:{password}@{cluster}.mongodb.net/"
            else:
                mongo_url = "mongodb://localhost:27017"

        client = AsyncIOMotorClient(
            mongo_url,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            retryWrites=True,
            retryReads=True
        )
        _db = client[MONGO_DB_NAME]
    return _db


# ============== Collections ==============

# Lazy load collections to avoid connection at import time
_collections_initialized = False

users_collection = None
shipments_collection = None
logins_collection = None
sensor_data_collection = None

def _init_collections():
    global users_collection, shipments_collection, logins_collection, sensor_data_collection, _collections_initialized
    if not _collections_initialized:
        db = get_db()
        users_collection = db['users']
        shipments_collection = db['shipments']
        logins_collection = db['logins']
        sensor_data_collection = db['sensor_data']
        _collections_initialized = True

def get_users_collection():
    if users_collection is None:
        _init_collections()
    return users_collection

def get_shipments_collection():
    if shipments_collection is None:
        _init_collections()
    return shipments_collection

def get_logins_collection():
    if logins_collection is None:
        _init_collections()
    return logins_collection

def get_sensor_data_collection():
    if sensor_data_collection is None:
        _init_collections()
    return sensor_data_collection


# ============== Reusable CRUD Functions ==============

async def find_one(collection, query: Dict[str, Any]) -> Optional[Dict]:
    """Find a single document matching the query."""
    return await collection.find_one(query)


async def find_many(collection, query: Dict[str, Any] = {}, 
                    limit: int = 0, sort: List[tuple] = None) -> List[Dict]:
    """Find multiple documents matching the query."""
    cursor = collection.find(query)
    if sort:
        cursor = cursor.sort(sort)
    if limit:
        cursor = cursor.limit(limit)
    return await cursor.to_list(length=None)


async def insert_one(collection, data: Dict[str, Any]) -> str:
    """Insert a single document and return the inserted ID."""
    result = await collection.insert_one(data)
    return str(result.inserted_id)


async def insert_many(collection, data: List[Dict[str, Any]]) -> List[str]:
    """Insert multiple documents and return their IDs."""
    result = await collection.insert_many(data)
    return [str(id) for id in result.inserted_ids]


async def update_one(collection, query: Dict[str, Any], 
                     update: Dict[str, Any], upsert: bool = False) -> bool:
    """Update a single document. Returns True if modified."""
    result = await collection.update_one(query, {'$set': update}, upsert=upsert)
    return result.modified_count > 0


async def update_many(collection, query: Dict[str, Any], 
                      update: Dict[str, Any]) -> int:
    """Update many documents. Returns count of modified documents."""
    result = await collection.update_many(query, {'$set': update})
    return result.modified_count


async def delete_one(collection, query: Dict[str, Any]) -> bool:
    """Delete a single document. Returns True if deleted."""
    result = await collection.delete_one(query)
    return result.deleted_count > 0


async def delete_many(collection, query: Dict[str, Any]) -> int:
    """Delete many documents. Returns count of deleted documents."""
    result = await collection.delete_many(query)
    return result.deleted_count


async def count_documents(collection, query: Dict[str, Any] = {}) -> int:
    """Count documents matching the query."""
    return await collection.count_documents(query)


async def exists(collection, query: Dict[str, Any]) -> bool:
    """Check if a document exists matching the query."""
    doc = await collection.find_one(query, {'_id': 1})
    return doc is not None


__all__ = [
    'get_db',
    'find_one',
    'find_many',
    'insert_one',
    'insert_many',
    'update_one',
    'update_many',
    'delete_one',
    'delete_many',
    'count_documents',
    'exists',
    'get_users_collection',
    'get_shipments_collection',
    'get_logins_collection',
    'get_sensor_data_collection'
]