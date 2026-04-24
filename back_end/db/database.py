
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


from typing import Optional, List, Dict, Any

# ============== Database Connection ==============

def get_db():
    """Get database connection."""
    # Check for full MongoDB Atlas URL first
    mongo_url = os.environ.get("MONGO_URL")
    
    # If no full URL, construct from Atlas credentials
    if not mongo_url:
        username = os.environ.get("MONGO_USERNAME")
        password = os.environ.get("MONGO_PASSWORD")
        cluster = os.environ.get("MONGO_CLUSTER_NAME", "users")
        
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
    db_name = os.environ.get("MONGO_DB_NAME", "SCM_DB")
    return client[db_name]


# ============== Collections ==============

db = get_db()
users_collection = db['users']
shipments_collection = db['shipments']
logins_collection = db['logins']
sensor_data_collection = db['sensor_data']


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
    """Update multiple documents. Returns count of modified documents."""
    result = await collection.update_many(query, {'$set': update})
    return result.modified_count


async def delete_one(collection, query: Dict[str, Any]) -> bool:
    """Delete a single document. Returns True if deleted."""
    result = await collection.delete_one(query)
    return result.deleted_count > 0


async def delete_many(collection, query: Dict[str, Any]) -> int:
    """Delete multiple documents. Returns count of deleted documents."""
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
    'users_collection',
    'shipments_collection',
    'logins_collection',
    'sensor_data_collection',
    'db',
]
