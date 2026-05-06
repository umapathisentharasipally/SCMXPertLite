import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables once
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(dotenv_path=ROOT_DIR / '.env')

# Database Configuration
MONGO_USERNAME = os.getenv('MONGO_USERNAME', '')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', '')
MONGO_CLUSTER_NAME = os.getenv('MONGO_CLUSTER_NAME', 'users')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'SCM_DB')
MONGO_URL = os.getenv('MONGO_URL')

# Collection Names
COLL_USERS = os.getenv('COLL_USERS', 'users')
COLL_SHIPMENTS = os.getenv('COLL_SHIPMENTS', 'shipments')
COLL_LOGS = os.getenv('COLL_LOGS', 'logins')
COLL_DEVICES = os.getenv('COLL_DEVICES', 'devices')

# JWT Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = 'HS256'
JWT_ISSUER = 'scmxpertlite'

# Other Configs
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM')